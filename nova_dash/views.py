from django.shortcuts import render
from django.views import View
from utils.handlers import WebhookHandler
from django.conf import settings


class DashView(View):
    template_name = "dashboard/index.html"

    def get(self, request):
        return render(request, self.template_name)


class BillingView(View):
    template_name = "dashboard/billing.html"

    def get(self, request):
        return render(request, self.template_name)


class ProfileView(View):
    template_name = "dashboard/profile.html"

    def get(self, request):
        return render(request, self.template_name)


class TestView(View):
    template_name = "dashboard/icons.html"

    def get(self, request):
        return render(request, self.template_name)
