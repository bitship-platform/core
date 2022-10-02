from rest_framework.views import APIView
from utils.mixins import ResponseMixin
from core.apps.dashboard.models import App, Member
from .serializers import MemberDataSerializer, MemberPutSerializer, AppDataSerializer
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from rest_framework.permissions import DjangoModelPermissions


class PingView(APIView, ResponseMixin):
    def get(self, request):
        return self.json_response_200()


class CustomerDataView(APIView, ResponseMixin):
    model = Member
    serializer = MemberDataSerializer
    permission_classes = [DjangoModelPermissions]

    def get_queryset(self):
        return self.model.objects.all()

    def get(self, request, c_id=None):
        if c_id:
            customer = get_object_or_404(self.model, id=c_id)
            serializer = self.serializer(customer)
            return Response(serializer.data, status=200)
        serializer = self.serializer(self.get_queryset(), many=True)
        return Response(serializer.data, status=200)

    def put(self, request, c_id):
        customer = get_object_or_404(self.model, id=c_id)
        serializer = MemberPutSerializer(customer, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=200)
        return self.json_response_400()


class CustomerAppView(APIView, ResponseMixin):
    model = App
    serializer = AppDataSerializer

    def get_queryset(self):
        return self.model.objects.all()

    def get(self, request, c_id):
        serializer = self.serializer(self.model.objects.filter(owner__id=c_id), many=True)
        return Response(serializer.data, status=200)

