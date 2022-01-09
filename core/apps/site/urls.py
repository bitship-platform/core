from django.urls import path, re_path
from .views import DynamicView, ContactView

urlpatterns = [
    path('', DynamicView.as_view(), name='home'),
    re_path(r'^pages/terms/', DynamicView.as_view(template_name="terms-condition.html"), name='terms'),
    re_path(r'^pages/about/', DynamicView.as_view(template_name="about.html"), name='about'),
    re_path(r'^pages/privacy/', DynamicView.as_view(template_name="privacy-policy.html"), name='privacy'),
    re_path(r'^pages/discord-hosting/', DynamicView.as_view(template_name="discord-hosting.html"), name='discord'),
    re_path(r'^pages/contact/', ContactView.as_view(), name='contact'),
    re_path(r'^pages/dash/', DynamicView.as_view(template_name="dashboard/index.html"), name='dash'),
    re_path(r'^pages/log/', DynamicView.as_view(template_name="dashboard/index.html"), name='logout'),
]
