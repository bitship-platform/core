from rest_framework import serializers
from nova_dash.models import App


class AppStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = App
        fields = ("cpu", "ram", "disk", "network", "glacier")
