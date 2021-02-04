from rest_framework.views import APIView
from utils.mixins import ResponseMixin
from nova_dash.models import App
from utils.handlers import EmailHandler
from .serializers import AppStatusSerializer
from rest_framework.response import Response
from django.shortcuts import get_object_or_404


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
                    if app.owner.settings.email_notification:
                        msg = f"Hi {app.owner.user.first_name}\n\nYour app {app.name} subscription " \
                              f"is renewed for this month. The plan amount has been debited from your account.\n" \
                              f"Please login to check your updated balance.\n\n" \
                              f"Thank you!\n~Novanodes"
                        EmailHandler.send_email(app.owner.user.email,
                                                "Renewed app subscription",
                                                msg=msg)
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
    serializer = AppStatusSerializer
    model = App

    def put(self, request, app_id):
        queryset = get_object_or_404(self.model, unique_id=app_id)
        serializer = self.serializer(queryset, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=201)
        return self.json_response_400()


class AppConfirmationView(APIView, ResponseMixin):
    model = App

    def post(self, request):
        app_id = request.data.get("app_id")
        if app_id:
            try:
                app = App.objects.get(unique_id=app_id)
                if app.status == "bg-success":
                    app.status = "bg-warning"
                    app.owner.credits_spend -= app.plan
                    app.owner.credits += app.plan
                    app.owner.save()
                    app.save()
                return self.json_response_200()
            except App.DoesNotExist:
                return self.json_response_404()
        return self.json_response_400()
