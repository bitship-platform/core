from django.shortcuts import render, redirect
from django.views import View
from utils.handlers import AlertHandler as alert
from django.views.generic import ListView
from .models import Address, App
from django.contrib.auth import authenticate, login, logout
from utils.hashing import Hasher
from utils.oauth import Oauth
from utils.operations import create_customer, update_customer
from django.contrib.auth.mixins import LoginRequiredMixin
from django.forms import ValidationError
oauth = Oauth(redirect_uri="http://dashboard.novanodes.co:8000/login/", scope="identify%20email")
hashing = Hasher()


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
    status_order = ["Running", "Paused", "Stopped", "Terminated"]
    order = {pos: status for status, pos in enumerate(status_order)}

    def get_queryset(self):
        queryset = App.objects.filter(owner=self.request.user.customer)
        ordered_queryset = sorted(queryset, key=lambda query: self.order.get(query.get_status_display(), 0))
        return ordered_queryset


class ProfileView(LoginRequiredMixin, View):
    template_name = "dashboard/profile.html"
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


class BillingView(LoginRequiredMixin, View):
    template_name = "dashboard/billing.html"

    def get(self, request):
        return render(request, self.template_name)


class ManageView(LoginRequiredMixin, View):
    template_name = "dashboard/manage.html"
    context = {}

    def get(self, request, app_id):
        self.context["app"] = App.objects.get(pk=int(app_id))
        return render(request, self.template_name, self.context)
