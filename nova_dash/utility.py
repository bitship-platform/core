import os
import tarfile
from zipfile import ZipFile

from django.views import View
from django.conf import settings
from django.http import HttpResponse, HttpResponseForbidden

from .models import File, App
from utils.mixins import ResponseMixin


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


def make_tarfile(output_filename, source_dir):
    with tarfile.open(f"media/{output_filename}", "w:gz") as tar:
        tar.add(source_dir, arcname=os.path.basename(source_dir))


def create_backup(app, path):
    system_files = ["Procfile", "app.json", "runtime.txt"]
    with ZipFile(os.path.join(settings.MEDIA_ROOT, f"{app.unique_id}_backup.zip"), "w") as backup:
        for root, dirs, files in os.walk(path):
            for file in files:
                if file not in system_files:
                    backup.write(os.path.join(root, file),
                                 os.path.relpath(os.path.join(root, file),
                                                 os.path.join(path, '..')))


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