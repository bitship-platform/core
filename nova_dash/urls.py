from django.urls import path
from .views import DashView, BillingView, ProfileView, TestView
from django.conf.urls import url

urlpatterns = [

    path('', DashView.as_view(), name='home'),
    url(r'^pages/profile/', ProfileView.as_view(), name='test'),
    url(r'^pages/bill/', BillingView.as_view(), name='bill'),
    url(r'^pages/s/', TestView.as_view(), name='logout'),
]
