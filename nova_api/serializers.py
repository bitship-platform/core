from rest_framework import serializers
from nova_dash.models import App, Customer


class AppStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = App
        fields = ("cpu", "ram", "disk", "network", "glacier")


class CustomerDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = ("id", "credits", "coins", "verified", "running_apps", "joined_server", "creation_date")


class CustomerPutSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = ("banned", "verified", "joined_server")


class AppDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = App
        fields = ("name", "app_plan", "app_status", "app_stack")
