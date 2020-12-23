from django.shortcuts import render
from rest_framework.views import APIView
from django.http import JsonResponse
# Create your views here.


class AddItemView(APIView):
    def post(self, request):
        print("API REQUEST")
        print(request.user)
        return JsonResponse(data={"test": "ok"}, status=200)