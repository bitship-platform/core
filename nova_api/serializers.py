from rest_framework import serializers
from nova_dash.models import App, Customer


class AppStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = App
        fields = ("cpu", "ram", "disk", "network", "glacier")


class CustomerDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = ("id", "credits", "coins", "verified", "running_apps")


class CustomerPutSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = ("banned", "verified")
