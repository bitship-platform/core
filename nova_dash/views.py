import os
import json
from datetime import datetime, timezone
from ipware import get_client_ip

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
from django.http import QueryDict, HttpResponse, HttpResponseForbidden


from utils.handlers import AlertHandler as Alert, PaypalHandler
from .models import Address, App, File, Order, Customer, Referral
from utils.hashing import Hasher
from utils.oauth import Oauth
from utils.operations import create_customer, update_customer
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
        return HttpResponseForbidden('Not authorized to access this file.')


class TestView(View):

    def get(self, request):
        return render(request, "dashboard/accounts/user_login.html")


class LogoutView(View):

    def get(self, request):
        logout(request)
        return LoginView.as_view()(self.request)


class HelpView(View):
    template = "dashboard/help.html"

    def get(self, request):
        return render(request, self.template)


class LoginView(View):
    template_name = "dashboard/accounts/user_login.html"
    context = {}
    user_json = None
    access_token = None
    user_id = None
    email = None

    def get(self, request):
        code = request.GET.get('code', None)
        referrer_id = request.GET.get('refID', None)
        if referrer_id:
            client_ip, is_routable = get_client_ip(request)
            if is_routable:
                try:
                    referrer = Customer.objects.get(id=referrer_id)
                    if referrer.settings.affiliate:
                        if not Referral.objects.filter(ip=client_ip).exists():
                            Referral.objects.create(affiliate=referrer,
                                                    ip=client_ip)
                except Customer.DoesNotExist:
                    pass
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
                    client_ip, is_routable = get_client_ip(request)
                    if is_routable:
                        try:
                            ref_obj = Referral.objects.get(ip=client_ip)
                            customer.referrer = ref_obj.affiliate.user
                            customer.save()
                            ref_obj.delete()
                        except Referral.DoesNotExist:
                            pass
                    login(request, customer.user)
                elif user.customer.banned:
                    msg = "Your account has been banned. Contact admin if you think this was a mistake."
                    return render(request, self.template_name, {"Oauth": oauth, "msg": msg})
                else:
                    login(request, user)
                    update_customer(user_json=self.user_json)
                return redirect("/panel")
            else:
                msg = "Please add an email to your discord account and try again."
        return render(request, self.template_name, {"Oauth": oauth, "msg": msg})


class AdminLoginView(View):
    template_name = "dashboard/accounts/admin_login.html"

    def get(self, request):
        return render(request, self.template_name)

    def post(self, request):
        username = request.POST.get("username")
        password = request.POST.get("password")
        user = authenticate(username=username, password=password)
        if user is not None:
            if user.customer.banned:
                msg = "This account has been banned."
                return render(request, self.template_name, {"msg": msg})
            else:
                login(request, user)
                return redirect("/panel")
        else:
            msg = "Account does not exist, please check the credentials"
            return render(request, self.template_name, {"msg": msg})


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
                            self.context["alert"] = Alert("Error", "App by that name already exists.")
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
            self.context["alert"] = Alert("Error", "Zip Code looks invalid.")
        elif address.location is not None and len(address.location) < 8:
            self.context["alert"] = Alert("Error", "Address looks invalid.")
        else:
            try:
                address.save()
                self.context["alert"] = Alert("Success", "Data saved successfully!")
            except ValidationError:
                self.context["alert"] = Alert("Error", "Failed to save data... Try again.")
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
        user = User.objects.get(username=request.user.username)
        user.customer.reset()
        logout(request)
        return self.json_response_200()


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
            if not customer.verified:
                customer.verified = True
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
        if float(amount) >= 12:
            Order.objects.create(create_time=datetime.now(timezone.utc),
                                 update_time=datetime.now(timezone.utc),
                                 status="fa-check-circle text-success",
                                 customer=customer,
                                 transaction_amount=2.4,
                                 service="Annual Subscription Bonus",
                                 credit=True)
            customer.credits += 2.4
            customer.save()
        else:
            return self.json_response_401()
        return self.json_response_200()


class ActivityView(LoginRequiredMixin, View, ResponseMixin):

    def get(self, request):
        return render(request, "dashboard/activity.html")


class AffiliateView(LoginRequiredMixin, View, ResponseMixin):

    def get(self, request):
        if request.user.customer.settings.affiliate:
            return render(request, "dashboard/affiliates.html")
        return self.http_responce_404(request)
