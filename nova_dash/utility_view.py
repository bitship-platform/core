
from django.views import View
from django.conf import settings
from django.http import HttpResponse, HttpResponseForbidden

from .models import App
from utils.mixins import ResponseMixin
from utils.operations import make_tarfile, create_backup


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
