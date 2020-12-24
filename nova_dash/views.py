from django.shortcuts import render, redirect
from django.views import View
from utils.handlers import AlertHandler as alert
from django.views.generic import ListView
from .models import Address, App, Folder, File
from django.contrib.auth import authenticate, login, logout
from utils.hashing import Hasher
from utils.oauth import Oauth
from utils.operations import create_customer, update_customer
from django.contrib.auth.mixins import LoginRequiredMixin
from django.forms import ValidationError
from django.db import DatabaseError
from django.conf import settings
from django.http import JsonResponse, HttpResponse
import json
oauth = Oauth(redirect_uri="http://dashboard.novanodes.co:8000/login/", scope="identify%20email")
hashing = Hasher()
icon_cache = {v: k for k, v in App.STACK_CHOICES}
status_cache = {v: k for k, v in App.STATUS_CHOICES}


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
    context = {}

    def get_queryset(self):
        queryset = App.objects.filter(owner=self.request.user.customer)
        ordered_queryset = sorted(queryset, key=lambda query: self.order.get(query.get_status_display(), 0))
        return ordered_queryset

    def post(self, request):
        try:
            rate = request.POST.get("rate")
            if rate not in ["1.2", "2.4", "4.99"]:
                raise ValueError
            app = App.objects.create(name=request.POST.get("name", "nova-app"),
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

    def get(self, request, app_id, folder_id=None):
        app = App.objects.get(pk=int(app_id))
        self.context["app"] = app
        if folder_id:
            try:
                self.context["folder"] = Folder.objects.get(id=folder_id)
            except:
                self.context["folder"] = app.folder
        else:
            self.context["folder"] = app.folder
        return render(request, self.template_name, self.context)

    def post(self, request, app_id, folder_id=None):
        try:
            files = request.FILES.getlist('files_to_upload')
            folder_name = request.POST.get("folder")
            master = request.POST.get("master")
            if master:
                master = Folder.objects.get(id=master)
            if folder_name:
                Folder.objects.create(name=folder_name, owner=request.user.customer, folder=master)
            if files:
                for file in files:
                    if file.size < settings.MAX_FILE_SIZE:
                        File.objects.create(folder=master, item=file, name=file.name, size=file.size)
            if request.user.customer.ajax_enabled:
                app = App.objects.get(pk=int(app_id))
                self.context["app"] = app
                if folder_id:
                    try:
                        self.context["folder"] = Folder.objects.get(id=folder_id)
                    except:
                        self.context["folder"] = app.folder
                else:
                    self.context["folder"] = app.folder
                return render(request, 'dashboard/filesection.html', self.context)
            else:
                return redirect(to=f"/manage/{app_id}/{folder_id}")
        except DatabaseError:
            return render(request, "dashboard/index.html", self.context)

    def delete(self, request, app_id=None, folder_id=None):
        folder = request.GET.get("folder_id", None)
        file = request.GET.get("file_id", None)
        if file:
            File.objects.get(pk=file).delete()
        if folder:
            Folder.objects.get(id=folder).delete()
        app = App.objects.get(pk=int(app_id))
        self.context["app"] = app
        if folder_id:
            try:
                self.context["folder"] = Folder.objects.get(id=folder_id)
            except Folder.DoesNotExist:
                self.context["folder"] = app.folder
        else:
            self.context["folder"] = app.folder
        if request.user.customer.ajax_enabled:
            return render(request, 'dashboard/filesection.html', self.context)
        else:
            return render(request, self.template_name, self.context)