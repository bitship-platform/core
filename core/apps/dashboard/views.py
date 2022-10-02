from django.views import View
from django.conf import settings
from rest_framework import status
from django.core.files import File
from django.db import DatabaseError
from django.views.generic import ListView
from django.contrib.auth.models import User
from rest_framework.response import Response
from django.shortcuts import render, redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth import authenticate, login, logout
from django.http import QueryDict, HttpResponse, HttpResponseForbidden

from utils.oauth import Oauth
from utils.hashing import Hasher
from .models import App, File
from utils.operations import update_customer, create_customer
from utils.handlers import AlertHandler as Alert, PaypalHandler, WebhookHandler

oauth = Oauth(redirect_uri=settings.OAUTH_REDIRECT_URI, scope="identify%20email")
hashing = Hasher()
paypal = PaypalHandler(settings.PAYPAL_ID, settings.PAYPAL_SECRET)

icon_cache = {v: k for k, v in App.STACK_CHOICES}
status_cache = {v: k for k, v in App.STATUS_CHOICES}
webhook = WebhookHandler(settings.WEBHOOK_ID, settings.WEBHOOK_SECRET)


def media_access(request, path):
    access_granted = False
    user = request.user
    if user.is_authenticated:
        if user.is_superuser:
            access_granted = True
        else:
            file = File.objects.filter(item__exact=path)[0]
            if file.folder.owner == request.user.customer:
                access_granted = True
    if access_granted:
        response = HttpResponse()
        del response['Content-Type']
        response['X-Accel-Redirect'] = '/protected/media/' + path
        return response
    else:
        return HttpResponseForbidden('Not authorized to access this file.')


class LogoutView(View):

    def get(self, request):
        logout(request)
        return LoginView.as_view()(self.request)


class HelpView(View):
    template = "dashboard/help.html"

    def get(self, request):
        return render(request, self.template)


class RedirectLoginView(View):

    def get(self, request):
        if request.user.is_authenticated:
            return redirect(to="/panel")
        return redirect(to=oauth.discord_login_url)


class LoginView(View):
    template_name = "dashboard/accounts/user_login.html"
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
                    webhook.send_embed(
                        {
                            "type": "rich",
                            "title": "",
                            "description": f"New user signed up\n\nID: `{customer.id}`",
                            "color": 0xfd9c00,
                            "author": {
                                "name": f"{customer.user.first_name}#{customer.tag}",
                                "icon_url": f"{customer.get_avatar_url()}"
                            }
                        }
                    )
                    login(request, customer.user)
                    return redirect("/panel")
                elif user.customer.banned:
                    msg = "Your account has been banned. Contact admin if you think this was a mistake."
                    webhook.send_embed(
                        {
                            "type": "rich",
                            "title": "",
                            "description": f"Banned user attempted sign in\n\nID: `{user.customer.id}`",
                            "color": 0xff0707,
                            "author": {
                                "name": f"{user.first_name}#{user.customer.tag}",
                                "icon_url": f"{user.customer.get_avatar_url()}"
                            }
                        }
                    )
                    return render(request, self.template_name, {"Oauth": oauth, "msg": msg})
                else:
                    login(request, user)
                    update_customer(user_json=self.user_json)
                    webhook.send_embed(
                        {
                            "type": "rich",
                            "title": "",
                            "description": f"User signed in\n\nID: `{user.customer.id}`",
                            "color": 0x00aaff,
                            "author": {
                                "name": f"{user.first_name}#{user.customer.tag}",
                                "icon_url": f"{user.customer.get_avatar_url()}"
                            }
                        }
                    )
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
        if not request.user.customer.banned:
            try:
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
                                             status=status_cache.get("Not Started")
                                             )
                    self.context["app"] = app
                    self.context["folder"] = app.folder
                    return redirect(to=f"/manage/{app.id}/{app.folder.id}")
            except DatabaseError:
                return render(request, self.template_name, self.context)
        logout(request)
        return redirect("/")


class TeamsView(LoginRequiredMixin, View):
    template_name = "dashboard/teams.html"
    context = {}

    def get(self, request):
        return render(request, self.template_name)


class SettingView(LoginRequiredMixin, View):
    template_name = "dashboard/settings.html"

    def get(self, request):
        return render(request, self.template_name)

    def put(self, request):
        data = QueryDict(request.body)
        try:
            option = list(data)[0]
        except IndexError:
            return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        status_resp = data.get(option, None)
        if status_resp in ["true", "false"]:
            if status_resp == "true":
                setattr(request.user.customer.settings, option, True)
            elif status_resp == "false":
                setattr(request.user.customer.settings, option, False)
            try:
                request.user.customer.settings.save()
            except DatabaseError:
                return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            return Response(status=status.HTTP_200_OK)
        else:
            return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def delete(self, request):
        user = User.objects.get(username=request.user.username)
        user.customer.reset()
        logout(request)
        return Response(status=status.HTTP_200_OK)


class ActivityView(LoginRequiredMixin, View):

    def get(self, request):
        return render(request, "dashboard/activity.html")
