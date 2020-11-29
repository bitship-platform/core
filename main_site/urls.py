from django.urls import path
from . import views
from django.conf.urls import url

urlpatterns = [
    url(r'^pages/privacy/', views.DynamicPageView.as_view(), name='projects'),
]
