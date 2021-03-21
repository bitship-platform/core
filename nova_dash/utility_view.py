import json

from django.views import View
from django.conf import settings
from django.http import HttpResponse, HttpResponseForbidden, QueryDict, JsonResponse

from .models import App, File
from utils.mixins import ResponseMixin
from utils.misc import sample_app_json
from utils.operations import make_tarfile, create_backup, set_system_files


def set_app_config(request):
    if request.method == "PUT":
        config = {}
        python_version = ""
        procfile_script = ""

        data = QueryDict(request.body)
        script = int(data.get("script"))
        version = data.get("version")
        file = File.objects.get(id=script)
        app = file.folder.app

        if app.python:
            config["main_executable"] = file.name
            python_version = app.config_options.versions.get(version)
            config["python_version"] = python_version
            procfile_script = f"worker: python {file.name}"
            sample_app_json["image"] = "heroku/python"
        elif app.node:
            config["start_script"] = file.name
            node_version = app.config_options.versions.get(version)
            config["node_version"] = node_version
            procfile_script = f"worker: node {file.name}"
            sample_app_json["image"] = "heroku/nodejs"

        # if app.plan == 2.4:
        #     sample_app_json["buildpacks"].append("https://github.com/jonathanong/heroku-buildpack-ffmpeg-latest.git")
        sample_app_json["name"] = app.name
        config["app_json"] = sample_app_json

        if config != app.config:
            set_system_files(app, "app.json", json.dumps(sample_app_json))
            if app.python:
                set_system_files(app, "runtime.txt", python_version)
            set_system_files(app, "Procfile", procfile_script)
            app.config = config
            app.save()
        return JsonResponse({"message": "Success"}, status=200)


class TarballDownload(View, ResponseMixin):
    def get(self, request, uu_id):
        try:
            app = App.objects.get(unique_id=uu_id)
        except App.DoesNotExist:
            return self.json_response_404()
        path = settings.MEDIA_ROOT + f'/{app.owner.id}/{app.name}'
        response = HttpResponse()
        make_tarfile(f"{app.unique_id}.tar.gz", path)
        create_backup(app, path)
        del response['Content-Type']
        response['X-Accel-Redirect'] = "/protected/media/" + f"{app.unique_id}.tar.gz"
        response['Content-Disposition'] = f"attachment; filename={app.unique_id}.tar.gz"
        return response


class BackupDownload(View, ResponseMixin):
    def get(self, request, app_id):
        if request.user.is_authenticated:
            try:
                app = App.objects.get(unique_id=app_id)
                if app.owner == request.user.customer:
                    response = HttpResponse()
                    del response['Content-Type']
                    response['X-Accel-Redirect'] = "/protected/media/" + f"{app.unique_id}_backup.zip"
                    response['Content-Disposition'] = f"attachment; filename={app.name}_backup.zip"
                    return response
            except App.DoesNotExist:
                return self.json_response_404()
        return HttpResponseForbidden('Not authorized to access this file.')
