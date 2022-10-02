from rest_framework import serializers
from core.apps.dashboard.models import App, Member


class MemberDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = Member
        fields = ("id",  "verified", "running_apps", "joined_server", "creation_date")


class MemberPutSerializer(serializers.ModelSerializer):
    class Meta:
        model = Member
        fields = ("banned", "verified", "joined_server")


class AppDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = App
        fields = ("name", "app_plan", "app_status", "app_stack")
