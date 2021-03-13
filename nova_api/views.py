from rest_framework.views import APIView
from utils.mixins import ResponseMixin
from nova_dash.models import App, Order, Customer
from utils.handlers import EmailHandler
from .serializers import AppStatusSerializer, CustomerDataSerializer, CustomerPutSerializer
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from datetime import datetime, timezone


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
                    Order.objects.create(
                        create_time=datetime.now(timezone.utc),
                        update_time=datetime.now(timezone.utc),
                        transaction_amount=app.plan,
                        status="fa-check-circle text-success",
                        service="Subscription Renewal",
                        description=f"{app.name} app",
                        customer=app.owner
                    )
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
                    Order.objects.create(
                        create_time=datetime.now(timezone.utc),
                        update_time=datetime.now(timezone.utc),
                        transaction_amount=app.plan,
                        status="fa-times-circle text-danger",
                        service="Subscription Renewal",
                        description=f"{app.name} app | (insufficient balance)",
                        customer=app.owner
                    )
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
                Order.objects.create(
                    create_time=datetime.now(timezone.utc),
                    update_time=datetime.now(timezone.utc),
                    transaction_amount=app.plan,
                    status="fa-check-circle text-success",
                    service="Deploy Failure Reversal",
                    description=f"{app.name} app | (deploy rejected)",
                    customer=app.owner,
                    credit=True
                )
                return self.json_response_200()
            except App.DoesNotExist:
                return self.json_response_404()
        return self.json_response_400()


class CustomerDataView(APIView, ResponseMixin):
    model = Customer
    serializer = CustomerDataSerializer

    def get(self, request, c_id=None):
        if c_id:
            customer = get_object_or_404(self.model, id=c_id)
            serializer = self.serializer(customer)
            return Response(serializer.data, status=200)
        serializer = self.serializer(Customer.objects.all(), many=True)
        return Response(serializer.data, status=200)

    def put(self, request, c_id):
        customer = get_object_or_404(self.model, id=c_id)
        serializer = CustomerPutSerializer(customer, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=200)
        return self.json_response_400()


