import json

from django.views import View
from django.conf import settings
from rest_framework import status
from rest_framework.response import Response
from django.http import HttpResponse, QueryDict, JsonResponse

from .models import App, File
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


class TarballDownload(View):
    def get(self, request, uu_id):
        try:
            app = App.objects.get(unique_id=uu_id)
        except App.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
        path = settings.MEDIA_ROOT + f'/{app.owner.id}/{app.name}'
        response = HttpResponse()
        make_tarfile(f"{app.unique_id}.tar.gz", path)
        create_backup(app, path)
        del response['Content-Type']
        response['X-Accel-Redirect'] = "/protected/media/" + f"{app.unique_id}.tar.gz"
        response['Content-Disposition'] = f"attachment; filename={app.unique_id}.tar.gz"
        return response
