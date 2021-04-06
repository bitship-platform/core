import os
from datetime import datetime, timezone

import requests
from django.views import View
from django.conf import settings
from django.db import DatabaseError
from django.shortcuts import render
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import QueryDict, JsonResponse, HttpResponse

from utils.mixins import ResponseMixin
from .models import App, Folder, File, Order
from utils.operations import remove_file_from_storage, remove_dir_from_storage, bpd_api


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
                return render(request, 'dashboard/refresh_pages/filesection.html', self.context, status=403)
            if file_size_exceeded:
                return render(request, 'dashboard/refresh_pages/filesection.html', self.context, status=503)
            else:
                return render(request, 'dashboard/refresh_pages/filesection.html', self.context, status=200)
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
                return render(request, "dashboard/refresh_pages/filesection.html", self.context, status=200)
            return self.json_response_401()
        if file_id and file_name:
            if "." in file_name:
                return JsonResponse({"message": "File name should not contain extension"}, status=403)
            file = File.objects.get(pk=file_id)
            if file.folder.owner == request.user.customer:
                file_path = file.item.path
                file_extension = None
                try:
                    file_extension = file_path.rsplit(".", 1)[1]
                except IndexError:
                    pass
                if file_extension:
                    new_name = f"/{file_name}.{file_extension}"
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
                return render(request, "dashboard/refresh_pages/filesection.html", self.context, status=200)
        return self.json_response_400()

    def delete(self, request, app_id=None, folder_id=None):
        folder = request.GET.get("folder_id", None)
        file = request.GET.get("file_id", None)
        app = App.objects.get(pk=int(app_id))
        if file:
            file = File.objects.get(pk=file)
            if file.folder.owner == request.user.customer:
                if file.folder == app.folder:
                    app.config = {}
                file.delete()
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
        return render(request, 'dashboard/refresh_pages/filesection.html', self.context)


class AppManageView(LoginRequiredMixin, View, ResponseMixin):

    def get(self, request):
        context = {}
        app_id = request.GET.get("app_id")
        context["app"] = App.objects.get(id=app_id)
        return render(request, "dashboard/refresh_pages/mainconfiguration.html", context, status=200)

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
        if app.python:
            if "requirements.txt" not in file_set:
                if "Pipfile" not in file_set:
                    return JsonResponse({"message": "Missing requirements.txt or Pipfile in root."}, status=500)
            if not app.config.get("main_executable"):
                return JsonResponse({"message": "Missing main file configuration"}, status=500)
            if not app.config.get("python_version"):
                return JsonResponse({"message": "Missing python version configuration"}, status=500)
            if not app.config.get("app_json"):
                return JsonResponse({"message": "Something went wrong! please reconfigure your app and save."},
                                    status=500)
        elif app.node:
            if "package.json" not in file_set:
                return JsonResponse({"message": "Missing package.json in root."}, status=500)
            if not app.config.get("start_script"):
                return JsonResponse({"message": "Missing start script configuration"}, status=500)
            if not app.config.get("app_json"):
                return JsonResponse({"message": "Something went wrong! please reconfigure your app and save."},
                                    status=500)

        # Deploying the app and adding a billing plan if it doesn't have one
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
        app.last_deployment_timestamp = datetime.now(timezone.utc)
        app.save()
        context["app"] = app
        bpd_api.deploy(str(app.unique_id))
        return render(request, "dashboard/refresh_pages/appmanagement.html", context=context, status=200)

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
            remove_dir_from_storage(f"{request.user.username}/{app.folder.name}")
            remove_file_from_storage(f"{request.user.username}/{app.unique_id}.tar.gz")
            remove_file_from_storage(f"{request.user.username}/{app.unique_id}_backup.zip")
            app.folder.delete()
            if app.get_status_display() != "Not Started":
                bpd_api.terminate(str(app.unique_id))
            app.status = "bg-dark"
            app.cpu = 0
            app.ram = 0
            app.glacier = 0
            app.disk = 0
            app.save()
        except App.DoesNotExist:
            return self.json_response_500()
        return self.json_response_200()


class AppConsoleView(LoginRequiredMixin, View, ResponseMixin):

    def get(self, request, app_id):
        app_id = App.objects.get(id=app_id).unique_id
        return render(request, "dashboard/logs.html", {"app_id": app_id})


class AppLogView(LoginRequiredMixin, View, ResponseMixin):

    def get(self, request, app_id):
        try:
            resp = bpd_api.get(f"/logs/{app_id}")
            return HttpResponse(resp, status=resp.status_code)
        except Exception as E:
            print(E)
            return self.json_response_500()
