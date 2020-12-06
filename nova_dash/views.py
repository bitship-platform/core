from django.shortcuts import render, redirect
from django.views import View
from utils.handlers import WebhookHandler
from django.contrib.auth import authenticate, login
from utils.hashing import Hasher
from utils.oauth import Oauth
from utils.operations import create_customer
from django.contrib.auth.mixins import LoginRequiredMixin
oauth = Oauth(redirect_uri="http://dashboard.novanodes.co:8000/login/", scope="guilds%20identify%20email")
hashing = Hasher()


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
        customer = None
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
            return redirect(f"/user/{self.user_id}/")
        return render(request, self.template_name, {"Oauth": oauth, "msg": msg})


class DashView(LoginRequiredMixin, View):
    template_name = "dashboard/index.html"

    def get(self, request, user_id=None):
        return render(request, self.template_name)


class BillingView(LoginRequiredMixin, View):
    template_name = "dashboard/billing.html"

    def get(self, request):
        return render(request, self.template_name)


class ProfileView(LoginRequiredMixin, View):
    template_name = "dashboard/profile.html"

    def get(self, request):
        return render(request, self.template_name)


class ManageView(View, LoginRequiredMixin):
    template_name = "dashboard/manage.html"

    def get(self, request):
        return render(request, self.template_name)
