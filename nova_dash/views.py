import os
import json
import tarfile

from django.views import View
from django.conf import settings
from django.db import DatabaseError
from django.forms import ValidationError
from django.views.generic import ListView
from django.contrib.auth.models import User
from django.shortcuts import render, redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth import authenticate, login, logout
from django.http import HttpResponse, QueryDict, HttpResponseForbidden, JsonResponse


from utils.handlers import AlertHandler as alert, PaypalHandler
from .models import Address, App, Folder, File, Order
from utils.hashing import Hasher
from utils.oauth import Oauth
from utils.operations import create_customer, update_customer, bpd_api
from utils.mixins import ResponseMixin

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
        return HttpResponseForbidden('Not authorized to access this media.')


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
    status_order = ["Not Started", "Running", "Paused", "Stopped", "Terminated"]
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
                        File.objects.create(folder_id=master, item=file, name=file.name, size=file.size)
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
            if file_size_exceeded:
                return render(request, 'dashboard/filesection.html', self.context, status=403)
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
        if file:
            file = File.objects.get(pk=file)
            if file.folder.owner == request.user.customer:
                file.delete()
            else:
                return self.json_response_401()
        if folder:
            folder = Folder.objects.get(id=folder)
            if folder.owner == request.user.customer:
                folder.delete()
            else:
                return self.json_response_401()
        app = App.objects.get(pk=int(app_id))
        self.context["app"] = app
        if folder_id:
            try:
                self.context["folder"] = Folder.objects.get(id=folder_id)
            except Folder.DoesNotExist:
                self.context["folder"] = app.folder
        else:
            self.context["folder"] = app.folder
        return render(request, 'dashboard/filesection.html', self.context)


class Transaction(LoginRequiredMixin, View, ResponseMixin):

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
        if not Order.objects.filter(id=order_id).exists():
            Order.objects.create(id=order_id,
                                 payer_email=email,
                                 payer_id=payer_id,
                                 create_time=create_time,
                                 update_time=update_time,
                                 status=status,
                                 customer=customer,
                                 transaction_amount=amount)
            customer.credits += float(amount)
            customer.save()
        else:
            return self.json_response_401()
        return self.json_response_200()


def set_system_files(app: App):
    path = os.path.join(settings.MEDIA_ROOT, f"{app.owner.id}/{app.name}")


def deployment_helper(app: App):

    file_set = [file.name for file in app.folder.file_set.all()]
    if "requirements.txt" not in file_set:
        return JsonResponse({"message": "Missing requirements.txt in root."}, status=503)
    if not app.config.get("main_executable") or app.config.get("python_version"):
        return JsonResponse({"message": "App missing configuration, set python version and main file."}, status=503)


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
        if app.get_status_display() == "Not Started":
            if app.owner.credits < app.plan:
                return JsonResponse({"message": "You don't have enough credits for deploying"}, status=503)
            app.owner.credits -= app.plan
            app.owner.credits_spend += app.plan
            app.owner.save()
        app.status = "bg-success"
        app.save()
        context["app"] = app
        bpd_api.deploy(str(app.unique_id))
        return render(request, "dashboard/appmanagement.html", context, status=200)

    def put(self, request):
        data = QueryDict(request.body)
        app_id = data.get("app_id")
        action = data.get("action")
        if app_id and action:
            app = App.objects.get(id=app_id)
            if app.owner != request.user.customer:
                return self.json_response_401()
            app_id = str(app.unique_id)
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
            app.status = "bg-dark"
            app.cpu = 0
            app.save()
            bpd_api.terminate(str(app.unique_id))
        except App.DoesNotExist:
            return self.json_response_500()
        return self.json_response_200()
