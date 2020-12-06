from django.shortcuts import render, redirect
from django.views import View
from utils.handlers import WebhookHandler
from utils.hashing import Hasher
from utils.oauth import Oauth
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
        if code is not None:
            self.access_token = oauth.get_access_token(code)
            self.user_json = oauth.get_user_json(self.access_token)
            self.user_id = self.user_json.get('id')
            self.email = self.user_json.get('email')
        if self.email is not None:
            password = hashing.hashed_user_pass(self.user_id, self.email)
            if not password:
                pass
            else:
                msg = "Internal Server Error. Please try again later"
                # TODO: Add logging and webhook alert
        return render(request, self.template_name, {"Oauth": oauth, "msg": msg})


class DashView(View, LoginRequiredMixin):
    template_name = "dashboard/index.html"

    def get(self, request):
        return render(request, self.template_name)


class BillingView(View, LoginRequiredMixin):
    template_name = "dashboard/billing.html"

    def get(self, request):
        return render(request, self.template_name)


class ProfileView(View, LoginRequiredMixin):
    template_name = "dashboard/profile.html"

    def get(self, request):
        return render(request, self.template_name)


class ManageView(View, LoginRequiredMixin):
    template_name = "dashboard/manage.html"

    def get(self, request):
        return render(request, self.template_name)
