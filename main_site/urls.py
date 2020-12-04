from django.urls import path
from .views import DynamicView, ContactView
from django.conf.urls import url

urlpatterns = [

    path('', DynamicView.as_view(), name='home'),
    url(r'^pages/terms/', DynamicView.as_view(template_name="terms-condition.html"), name='terms'),
    url(r'^pages/about/', DynamicView.as_view(template_name="about.html"), name='about'),
    url(r'^pages/privacy/', DynamicView.as_view(template_name="privacy-policy.html"), name='privacy'),
    url(r'^pages/discord-hosting/', DynamicView.as_view(template_name="discord-hosting.html"), name='discord'),
    url(r'^pages/contact/', ContactView.as_view(), name='contact'),
    url(r'^pages/dash/', DynamicView.as_view(template_name="dashboard/templates/index.html"), name='dash'),
    url(r'^pages/log/', DynamicView.as_view(template_name="dashboard/templates/index.html"), name='logout'),
]
