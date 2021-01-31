from rest_framework.views import APIView
from utils.mixins import ResponseMixin
from nova_dash.models import App
from utils.handlers import EmailHandler
# Create your views here.


class RenewSubscription(APIView, ResponseMixin):

    def post(self, request):
        app_id = request.data.get("app_id")
        if app_id:
            try:
                app = App.objects.get(unique_id=app_id)
                if app.owner.credits >= app.plan:
                    app.owner.credits -= app.plan
                    app.owner.credits_spend += app.plan
                    app.owner.save()
                    return self.json_response_200()
                else:
                    msg = f"Hi {app.owner.user.first_name}\n\nYour app {app.name} has been shutdown since " \
                          f"your account doesn't have enought credits to renew the app subscription.\n" \
                          f"Please kindly recharge your account to continue using the services\n\n" \
                          f"Thank you!\n~Novanodes"
                    EmailHandler.send_email(app.owner.user.email,
                                            "Failed to renew subscription",
                                            msg=msg)
                    app.status = "bg-warning"
                    app.save()
                    return self.json_response_503()
            except App.DoesNotExist:
                return self.json_response_404()


class AppStatusUpdate(APIView, ResponseMixin):

    def post(self, request):
        app_id = request.data.get("app_id")
        cpu = request.data.get("cpu")
        memory = request.data.get("memory")
        network = request.data.get("network")
        if app_id:
            try:
                app = App.objects.get(unique_id=app_id)
                if not app.idle:
                    app.cpu = int(cpu)
                    app.ram = int(memory)
                    app.network = int(network)
                    app.save()
                return self.json_response_200()
            except App.DoesNotExist:
                return self.json_response_404()
