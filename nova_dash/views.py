from django.shortcuts import render, redirect
from django.views import View
from utils.handlers import AlertHandler as alert
from django.views.generic import ListView
from .models import Address, App, Folder, File
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from utils.hashing import Hasher
from utils.oauth import Oauth
from utils.operations import create_customer, update_customer
from django.contrib.auth.mixins import LoginRequiredMixin
from django.forms import ValidationError
from django.db import DatabaseError
from django.conf import settings
from utils.mixins import ResponseMixin
oauth = Oauth(redirect_uri=settings.OAUTH_REDIRECT_URI, scope="identify%20email")
hashing = Hasher()
icon_cache = {v: k for k, v in App.STACK_CHOICES}
status_cache = {v: k for k, v in App.STATUS_CHOICES}
from django.http import HttpResponse, JsonResponse
from django.http import QueryDict
from django.http import HttpResponseForbidden


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
            # app = App.objects.get(pk=int(app_id))
            # self.context["app"] = app
            # if folder_id:
            #     try:
            #         self.context["folder"] = Folder.objects.get(id=folder_id)
            #     except:
            #         self.context["folder"] = app.folder
            # else:
            #     self.context["folder"] = app.folder
            if file_size_exceeded:
                return render(request, 'dashboard/filesection.html', self.context, status=403)
            else:
                return render(request, 'dashboard/filesection.html', self.context, status=200)
        except DatabaseError:
            return render(request, "dashboard/index.html", self.context)

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
