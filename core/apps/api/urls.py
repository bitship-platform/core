from django.urls import path
from .views import CustomerDataView, PingView, CustomerAppView

urlpatterns = [
    path('customer/<int:c_id>/apps/', CustomerAppView.as_view(), name="customer_apps"),
    path('customer/<int:c_id>/', CustomerDataView.as_view(), name="customer_data"),
    path('customer/', CustomerDataView.as_view(), name="customer"),
    path('ping/', PingView.as_view(), name="ping"),
]
