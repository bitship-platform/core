from django.shortcuts import render
from rest_framework.views import APIView
from django.http import JsonResponse
from utils.mixins import ResponseMixin
from nova_dash.models import App
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
                    # TODO: Notify the user by email and discord
                    pass
            except App.DoesNotExist:
                return self.json_response_404()

