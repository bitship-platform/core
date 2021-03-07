import os
import json
import uuid
import tarfile
from datetime import datetime, timezone

from django.views import View
from django.conf import settings
from django.core.files import File
from django.db import DatabaseError
from django.forms import ValidationError
from django.views.generic import ListView
from django.contrib.auth.models import User
from django.shortcuts import render, redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth import authenticate, login, logout
from django.http import HttpResponse, QueryDict, HttpResponseForbidden, JsonResponse


from utils.handlers import AlertHandler as alert, PaypalHandler, EmailHandler
from .models import Address, App, Folder, File, Order, Customer, Transaction, Offer, Promo
from utils.hashing import Hasher
from utils.oauth import Oauth
from utils.operations import create_customer, update_customer, bpd_api
from utils.mixins import ResponseMixin
from utils.misc import sample_app_json

oauth = Oauth(redirect_uri=settings.OAUTH_REDIRECT_URI, scope="identify%20email")
hashing = Hasher()
paypal = PaypalHandler(settings.PAYPAL_ID, settings.PAYPAL_SECRET)

icon_cache = {v: k for k, v in App.STACK_CHOICES}
status_cache = {v: k for k, v in App.STATUS_CHOICES}


def media_access(request, path):
    access_granted = False
    user = request.user
    if user.is_authenticated:
        if user.is_superuser:
            # If admin, everything is granted
            access_granted = True
        else:
            file = File.objects.filter(item__exact=path)[0]
            if file.folder.owner == request.user.customer:
                access_granted = True
    if access_granted:
        response = HttpResponse()
        # Content-type will be detected by nginx
        del response['Content-Type']
        response['X-Accel-Redirect'] = '/protected/media/' + path
        return response
    else:
        return HttpResponseForbidden('Not authorized to access this file.')


def make_tarfile(output_filename, source_dir):
    with tarfile.open(f"media/{output_filename}", "w:gz") as tar:
        tar.add(source_dir, arcname=os.path.basename(source_dir))


class TarballDownload(View, ResponseMixin):
    def get(self, request, uu_id):
        try:
            app = App.objects.get(unique_id=uu_id)
        except App.DoesNotExist:
            return self.json_response_404()
        path = settings.MEDIA_ROOT + f'/{app.owner.id}/{app.name}'
        response = HttpResponse()
        make_tarfile(f"{app.unique_id}.tar.gz", path)
        del response['Content-Type']
        response['X-Accel-Redirect'] = "/protected/media/" + f"{app.unique_id}.tar.gz"
        response['Content-Disposition'] = f"attachment; filename={app.unique_id}.tar.gz"
        return response


class BackupDownload(View, ResponseMixin):
    def get(self, request, app_id):
        if request.user.is_authenticated:
            try:
                app = App.objects.get(id=app_id)
                if app.owner == request.user.customer:
                    response = HttpResponse()
                    del response['Content-Type']
                    response['X-Accel-Redirect'] = "/protected/media/" + f"{app.unique_id}.tar.gz"
                    response['Content-Disposition'] = f"attachment; filename={app.unique_id}.tar.gz"
                    return response
            except App.DoesNotExist:
                return self.json_response_404()
        return HttpResponseForbidden('Not authorized to access this file.')


class LogoutView(View):

    def get(self, request):
        logout(request)
        return LoginView.as_view()(self.request)


class LoginView(View):
    template_name = "dashboard/accounts/login.html"
    context = {}
    user_json = None
    access_token = None
    user_id = None
    email = None

    def get(self, request):
        code = request.GET.get('code', None)
        self.email = None
        msg = None
        if code is not None:
            self.access_token = oauth.get_access_token(code)
            self.user_json = oauth.get_user_json(self.access_token)
            self.user_id = self.user_json.get('id')
            self.email = self.user_json.get('email')
        if self.email is not None:
            password = hashing.hashed_user_pass(self.user_id, self.email)
            user = authenticate(username=self.user_id, password=password)
            if user is None:
                customer = create_customer(self.user_json, password)
                login(request, customer.user)
            else:
                login(request, user)
                update_customer(user_json=self.user_json)
            return redirect("/panel")
        return render(request, self.template_name, {"Oauth": oauth, "msg": msg})


class DashView(LoginRequiredMixin, ListView, View):
    template_name = "dashboard/index.html"
    paginate_by = 5
    status_order = ["Not Started", "Running", "Awaiting Confirmation", "Stopped", "Terminated"]
    order = {pos: status for status, pos in enumerate(status_order)}
    order2 = {pos: status for status, pos in enumerate(status_order[:-1])}
    context = {}

    def get_queryset(self):
        if self.request.user.customer.terminated_apps:
            queryset = App.objects.filter(owner=self.request.user.customer)
        else:
            queryset = App.objects.filter(owner=self.request.user.customer, status__in=list(status_cache.values())[:-1])
        ordered_queryset = sorted(queryset, key=lambda query: self.order.get(query.get_status_display(), 0))
        return ordered_queryset

    def post(self, request):
        try:
            rate = request.POST.get("rate")
            if rate not in ["1.2", "2.4", "4.99"]:
                raise ValueError
            name = request.POST.get("name", None)
            if name:
                if " " in name:
                    name = name.replace(" ", "-")
                queryset = App.objects.filter(name=name, owner=request.user.customer)
                if queryset.exists():
                    for app in queryset:
                        if app.status != "bg-dark":
                            self.context["app"] = app
                            self.context["folder"] = app.folder
                            self.context["alert"] = alert("Error", "App by that name already exists.")
                            return render(request, "dashboard/manage.html", self.context)
                app = App.objects.create(name=name,
                                         owner=request.user.customer,
                                         stack=icon_cache.get(request.POST.get("stack")),
                                         plan=rate,
                                         status=status_cache.get("Not Started")
                                         )
                self.context["app"] = app
                self.context["folder"] = app.folder
                return redirect(to=f"/manage/{app.id}/{app.folder.id}")
        except DatabaseError:
            return render(request, self.template_name, self.context)


class BillingView(LoginRequiredMixin, View):
    template_name = "dashboard/billing.html"
    context = {}

    def get(self, request):
        return render(request, self.template_name)

    def post(self, request):
        fields = ["firstname", "lastname", "city", "country", "pincode", "location"]
        address = Address.objects.get(customer__user=request.user)
        for field in fields:
            data = request.POST.get(field, None)
            if data != "":
                setattr(address, field, data)
        if address.pincode is not None and len(str(address.pincode)) < 5:
            self.context["alert"] = alert("Error", "Zip Code looks invalid.")
        elif address.location is not None and len(address.location) < 8:
            self.context["alert"] = alert("Error", "Address looks invalid.")
        else:
            try:
                address.save()
                self.context["alert"] = alert("Success", "Data saved successfully!")
            except ValidationError:
                self.context["alert"] = alert("Error", "Failed to save data... Try again.")
        return render(request, self.template_name, self.context)


class SettingView(LoginRequiredMixin, View, ResponseMixin):
    template_name = "dashboard/settings.html"

    def get(self, request):
        return render(request, self.template_name)

    def put(self, request):
        data = QueryDict(request.body)
        try:
            option = list(data)[0]
        except IndexError:
            return self.json_response_500()

        status = data.get(option, None)
        if status in ["true", "false"]:
            if status == "true":
                setattr(request.user.customer.settings, option, True)
            elif status == "false":
                setattr(request.user.customer.settings, option, False)
            try:
                request.user.customer.settings.save()
            except DatabaseError:
                return self.json_response_500()
            return self.json_response_200()
        else:
            return self.json_response_500()

    def delete(self, request):
        User.objects.get(username=request.user.username).delete()
        return self.json_response_200()


class ManageView(LoginRequiredMixin, View, ResponseMixin):
    template_name = "dashboard/manage.html"
    context = {}

    def get(self, request, app_id, folder_id=None):
        app = App.objects.get(pk=int(app_id))
        if app:
            if app.get_status_display() == "Terminated":
                return self.http_responce_404(request)
        self.context["app"] = app
        if app.owner != request.user.customer:
            return self.http_responce_400(request)
        if folder_id:
            try:
                self.context["folder"] = Folder.objects.get(id=folder_id)
            except:
                self.context["folder"] = app.folder
        else:
            self.context["folder"] = app.folder
        return render(request, self.template_name, self.context)

    def post(self, request, app_id, folder_id=None):
        file_size_exceeded = False
        forbidden_file_type = False
        try:
            files = request.FILES.getlist('files_to_upload')
            folder_name = request.POST.get("folder")
            master = request.POST.get("master")
            if folder_name:
                if " " in folder_name:
                    return self.json_response_403()
                if Folder.objects.filter(name=folder_name, folder_id=master).exists():
                    return self.json_response_405()
                Folder.objects.create(name=folder_name, owner=request.user.customer, folder_id=master)
            if files:
                for file in files:
                    if file.size < settings.MAX_FILE_SIZE:
                        if file.name in ["app.json", "Procfile", "runtime.txt", ".env"]:
                            # ignoring system files
                            forbidden_file_type = True
                            continue
                        try:
                            File.objects.create(folder_id=master, item=file, name=file.name, size=file.size)
                        except Exception as e:
                            pass
                    else:
                        file_size_exceeded = True
            app = App.objects.get(pk=int(app_id))
            self.context["app"] = app
            if folder_id:
                try:
                    self.context["folder"] = Folder.objects.get(id=folder_id)
                except:
                    self.context["folder"] = app.folder
            else:
                self.context["folder"] = app.folder
            if forbidden_file_type:
                return render(request, 'dashboard/filesection.html', self.context, status=403)
            if file_size_exceeded:
                return render(request, 'dashboard/filesection.html', self.context, status=503)
            else:
                return render(request, 'dashboard/filesection.html', self.context, status=200)
        except DatabaseError:
            return render(request, "dashboard/index.html", self.context)

    def put(self, request):
        data = QueryDict(request.body)
        folder_id = data.get("folder_id")
        folder_name = data.get("folder")
        file_id = data.get("file_id")
        file_name = data.get("file_name")
        if folder_id and folder_name:
            folder = Folder.objects.get(id=folder_id)
            if folder.owner == request.user.customer:
                dir_path = folder.get_absolute_path()
                new_path = dir_path.rsplit("/", 1)[0] + f"/{folder_name}"
                absolute_path = os.path.join(settings.BASE_DIR, 'media', dir_path[1:])
                new_path = os.path.join(settings.BASE_DIR, 'media', new_path[1:])
                try:
                    os.rename(absolute_path, new_path)
                except PermissionError:
                    return self.json_response_500()
                except FileNotFoundError:
                    pass
                folder.name = folder_name
                folder.save()
                self.context["folder"] = folder.folder
                return render(request, "dashboard/filesection.html", self.context, status=200)
            return self.json_response_401()
        if file_id and file_name:
            if "." in file_name:
                return JsonResponse({"message": "File name should not contain extenstion"}, status=403)
            file = File.objects.get(pk=file_id)
            if file.folder.owner == request.user.customer:
                file_path = file.item.path
                file_extenstion = None
                try:
                    file_extenstion = file_path.rsplit(".", 1)[1]
                except IndexError:
                    pass
                if file_extenstion:
                    new_name = f"/{file_name}.{file_extenstion}"
                else:
                    new_name = f"/{file_name}"
                if new_name in ["app.json", "Procfile", "runtime.txt"]:
                    return self.json_response_500()
                if os.name == "nt":
                    new_path = file_path.rsplit("\\", 1)[0] + new_name
                else:
                    new_path = file_path.rsplit("/", 1)[0] + new_name
                try:
                    os.rename(file_path, new_path)
                    file.item.name = new_path.split("media")[1][1:].replace("\\", "/")
                    file.name = new_name[1:]
                    file.save()
                except PermissionError:
                    return self.json_response_500()
                self.context["folder"] = file.folder
                return render(request, "dashboard/filesection.html", self.context, status=200)
        return self.json_response_400()

    def delete(self, request, app_id=None, folder_id=None):
        folder = request.GET.get("folder_id", None)
        file = request.GET.get("file_id", None)
        app = App.objects.get(pk=int(app_id))
        if file:
            file = File.objects.get(pk=file)
            if file.folder.owner == request.user.customer:
                file.delete()
                app.config = {}
                app.save()
            else:
                return self.json_response_401()
        if folder:
            folder = Folder.objects.get(id=folder)
            if folder.owner == request.user.customer:
                folder.delete()
            else:
                return self.json_response_401()
        self.context["app"] = app
        if folder_id:
            try:
                self.context["folder"] = Folder.objects.get(id=folder_id)
            except Folder.DoesNotExist:
                self.context["folder"] = app.folder
        else:
            self.context["folder"] = app.folder
        return render(request, 'dashboard/filesection.html', self.context)


class PaypalTransaction(LoginRequiredMixin, View, ResponseMixin):

    def post(self, request):
        data = json.loads(request.body)
        order_id = data['details']['id']
        details = paypal.get_order_details(order_id)
        status = details["purchase_units"][0]["payments"]["captures"][0]["status"]
        amount = details["purchase_units"][0]["payments"]["captures"][0]["amount"]["value"]
        create_time = details["create_time"]
        update_time = details["update_time"]
        order_id = details["id"]
        payer_id = details["payer"]["payer_id"]
        email = details["payer"]["email_address"]
        customer = request.user.customer
        if status == "COMPLETED":
            status = "fa-check-circle text-success"
            customer.credits += float(amount)
            customer.save()
        elif status == "PAYER_ACTION_REQUIRED":
            status = "fa-clock text-warning"
        else:
            status = "fa-times-circle text-danger"
        if not Order.objects.filter(id=order_id).exists():
            Order.objects.create(id=order_id,
                                 payer_email=email,
                                 payer_id=payer_id,
                                 create_time=create_time,
                                 update_time=update_time,
                                 status=status,
                                 customer=customer,
                                 transaction_amount=amount,
                                 service="Credit Recharge",
                                 description=f"Paypal: {payer_id}",
                                 credit=True)
        else:
            return self.json_response_401()
        return self.json_response_200()


def set_system_files(app: App, file_name, content):
    path = os.path.join(settings.MEDIA_ROOT, f"{app.owner.id}/{app.name}/")
    with open(path+file_name, "w") as file:
        file.write(content)


def set_app_config(request):
    if request.method == "PUT":
        data = QueryDict(request.body)
        config = {}
        main_file = int(data.get("main_executable"))
        python_version = data.get("python_version")
        main_file = File.objects.get(id=main_file)
        config["main_executable"] = main_file.name
        config["python_version"] = python_version
        app = main_file.folder.app
        if app.plan == 2.4:
            sample_app_json["buildpacks"].append("https://github.com/jonathanong/heroku-buildpack-ffmpeg-latest.git")
        python_version = app.config_options.python_versions.get(python_version)
        sample_app_json["name"] = app.name
        config["app_json"] = sample_app_json
        if config != app.config:
            set_system_files(app, "app.json", json.dumps(sample_app_json))
            set_system_files(app, "runtime.txt", python_version)
            set_system_files(app, "Procfile", f"worker: python {main_file.name}")
            app.config = config
            app.save()
        return JsonResponse({"message": "Success"}, status=200)


class AppManageView(LoginRequiredMixin, View, ResponseMixin):

    def get(self, request):
        context = {}
        app_id = request.GET.get("app_id")
        context["app"] = App.objects.get(id=app_id)
        return render(request, "dashboard/mainconfiguration.html", context, status=200)

    def post(self, request):
        context = {}
        app_id = request.POST.get("app_id")
        if not app_id:
            return self.json_response_400()
        try:
            app = App.objects.get(id=app_id)
            if app.owner != request.user.customer:
                return self.json_response_401()
        except App.DoesNotExist:
            return self.json_response_404()
        file_set = app.primary_file_set
        if "requirements.txt" not in file_set:
            if "Pipfile" not in file_set:
                return JsonResponse({"message": "Missing requirements.txt or Pipfile in root."}, status=503)
        if not app.config.get("main_executable"):
            return JsonResponse({"message": "Missing main file configuration"}, status=503)
        if not app.config.get("python_version"):
            return JsonResponse({"message": "Missing python version configuration"}, status=503)
        if not app.config.get("app_json"):
            return JsonResponse({"message": "Something went wrong! please reconfigure your app and save."}, status=503)
        if app.get_status_display() == "Not Started":
            if app.owner.credits < app.plan:
                return JsonResponse({"message": "You don't have enough credits for deploying"}, status=503)
            app.owner.credits -= app.plan
            app.owner.credits_spend += app.plan
            app.owner.save()
            Order.objects.create(
                create_time=datetime.now(timezone.utc),
                update_time=datetime.now(timezone.utc),
                transaction_amount=app.plan,
                status="fa-check-circle text-success",
                service="App Subscription Start",
                description=f"{app.name} app",
                customer=app.owner
            )
        app.status = "bg-success"
        app.save()
        context["app"] = app
        bpd_api.deploy(str(app.unique_id))
        return render(request, "dashboard/appmanagement.html", context=context, status=200)

    def put(self, request):
        data = QueryDict(request.body)
        app_id = data.get("app_id")
        action = data.get("action")
        if action not in ["start", "stop", "restart"]:
            return self.json_response_400()
        if app_id and action:
            app = App.objects.get(id=app_id)
            if app.owner != request.user.customer:
                return self.json_response_401()
            app_id = str(app.unique_id)
            if action == "stop":
                app.status = "bg-danger"
                app.cpu = 0
                app.ram = 0
                app.network = 0
                app.save()
            elif action == "start":
                app.status = "bg-success"
                app.save()
            bpd_api.manage(app_id=app_id, action=action)
            return self.json_response_200()
        return self.json_response_500()

    def delete(self, request):
        app_id = request.GET.get("app_id")
        if not app_id:
            return self.json_response_400()
        try:
            app = App.objects.get(id=int(app_id))
            if app.owner != request.user.customer:
                return self.json_response_401()
            app.folder.delete()
            if app.get_status_display() != "Not Started":
                bpd_api.terminate(str(app.unique_id))
            app.status = "bg-dark"
            app.cpu = 0
            app.save()
        except App.DoesNotExist:
            return self.json_response_500()
        return self.json_response_200()


class ActivityView(LoginRequiredMixin, View, ResponseMixin):

    def get(self, request):
        return render(request, "dashboard/activity.html")


class TransactionUtility(LoginRequiredMixin, View, ResponseMixin):

    def post(self, request):
        transaction_id = request.POST.get("transaction_id")
        try:
            transaction = Transaction.objects.get(id=transaction_id)
            if (datetime.now(timezone.utc) - transaction.last_otp_generation_time).total_seconds() > 120:
                otp = uuid.uuid4().hex.upper()[0:6]
                transaction.otp = otp
                transaction.last_otp_generation_time = datetime.now(timezone.utc)
                transaction.save()
                msg = f"Hi {transaction.patron.user.first_name}," \
                      f"\nPlease copy paste the OTP below to authorize the transaction " \
                      f"of ${transaction.amount} to {transaction.recipient.user.first_name} " \
                      f"#{transaction.recipient.tag}\n\n" \
                      f"{otp}\n\n" \
                      f"Please do not share this otp with anyone\n" \
                      f"Thank you!\n~Novanodes"
                EmailHandler.send_email(transaction.patron.user.email,
                                        "OTP for transaction",
                                        msg=msg)
                return self.json_response_200()
            else:
                return self.json_response_503()
        except Transaction.DoesNotExist:
            return self.json_response_500()

    def put(self, request):
        data = QueryDict(request.body)
        transaction_id = data.get("transaction_id")
        try:
            transaction = Transaction.objects.get(id=transaction_id, status="fa-clock text-warning")
            return render(request, "dashboard/transaction_refresh.html", {"recipient": transaction.recipient,
                                                                          "transaction_id": transaction.id},
                          status=200)
        except Transaction.DoesNotExist:
            return self.json_response_500


class TransactionView(LoginRequiredMixin, View, ResponseMixin):

    def get(self, request):
        return render(request, "dashboard/transactions.html")

    def post(self, request):
        if not request.user.customer.verified:
            return self.json_response_501()
        account_no = request.POST.get("account_no")
        if int(account_no) == request.user.customer.id:
            return self.json_response_405()
        amount = float(request.POST.get("amount"))
        msg = request.POST.get("msg")
        if amount < 1:
            return self.json_response_403()
        if amount > request.user.customer.credits:
            return self.json_response_503()
        try:
            recipient = Customer.objects.get(id=account_no)
            otp = uuid.uuid4().hex.upper()[0:6]
            transaction = Transaction.objects.create(
                patron=request.user.customer,
                recipient=recipient,
                amount=amount,
                status="fa-clock text-warning",
                msg=msg,
                otp=otp,
                last_otp_generation_time=datetime.now(timezone.utc)
            )
            msg = f"Hi {request.user.first_name},\nPlease copy paste the OTP below to authorize the transaction " \
                  f"of ${amount} to {recipient.user.first_name} #{recipient.user.customer.tag}\n\n" \
                  f"{otp}\n\n" \
                  f"Please do not share this otp with anyone\n" \
                  f"Thank you!\n~Novanodes"
            EmailHandler.send_email(request.user.email,
                                    "OTP for transaction",
                                    msg=msg)
            return render(request, "dashboard/transaction_refresh.html", {"recipient": recipient,
                                                                          "transaction_id": transaction.id},
                          status=200)
        except Customer.DoesNotExist:
            return self.json_response_404()

    def put(self, request):
        data = QueryDict(request.body)
        transaction_id = data.get("transaction_id")
        otp = data.get("otp")
        try:
            transaction = Transaction.objects.get(id=transaction_id, status="fa-clock text-warning")
            if otp == transaction.otp:
                if transaction.amount > request.user.customer.credits:
                    transaction.status = "fa-times-circle text-danger"
                    transaction.save()
                    return self.json_response_503()
                else:
                    request.user.customer.credits -= transaction.amount
                    transaction.recipient.credits += transaction.amount
                    transaction.status = "fa-check-circle text-success"
                    transaction.save()
                    request.user.customer.save()
                    transaction.recipient.save()
                    return render(request, "dashboard/pending_transactions.html", status=200)
            else:
                transaction.status = "fa-times-circle text-danger"
                transaction.failure_message = "OTP mismatch"
                transaction.save()
                return self.json_response_400()
        except Transaction.DoesNotExist:
            return self.json_response_500()

    def delete(self, request):
        transaction_id = request.GET.get("transaction_id")
        try:
            transaction = Transaction.objects.get(id=transaction_id, status="fa-clock text-warning")
            transaction.status = "fa-ban text-danger"
            transaction.save()
            return render(request, "dashboard/pending_transactions.html", status=200)
        except Transaction.DoesNotExist:
            return self.json_response_500()


class PromoCodeView(LoginRequiredMixin, View, ResponseMixin):

    def post(self, request):
        code = request.POST.get("promo_code")
        try:
            promo_code = Promo.objects.get(code=code)
            customer = request.user.customer
            if promo_code.offer not in customer.applied_offers.all():
                if not promo_code.expired:
                    if not promo_code.offer.expired:
                        customer.credits += promo_code.offer.credit_reward
                        customer.coins += promo_code.offer.coin_reward
                        customer.applied_offers.add(promo_code.offer)
                        customer.save()
                        return render(request, "dashboard/stats_refresh.html", status=200)
                    return self.json_response_403()
                return self.json_response_403()
            return self.json_response_503()
        except Promo.DoesNotExist:
            return self.json_response_404()


class ExchangeView(LoginRequiredMixin, View, ResponseMixin):

    def post(self, request):
        coins = int(request.POST.get("coins"))
        if coins > request.user.customer.coins:
            return self.json_response_503()
        customer = request.user.customer
        customer.coins -= coins
        customer.credits += coins * 0.12
        customer.coins_redeemed += coins
        customer.save()
        Order.objects.create(customer=customer,
                             transaction_amount=coins * 0.12,
                             credit=True,
                             create_time=datetime.now(timezone.utc),
                             update_time=datetime.now(timezone.utc),
                             service="Coin Exchange",
                             status="fa-check-circle text-success")
        return render(request, "dashboard/stats_refresh.html", status=200)