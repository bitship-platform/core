from django.urls import path
from .views import MemberDataView, PingView, MemberAppView

urlpatterns = [
    path('member/<int:c_id>/apps/', MemberAppView.as_view(), name="customer_apps"),
    path('member/<int:c_id>/', MemberDataView.as_view(), name="customer_data"),
    path('member/', MemberDataView.as_view(), name="customer"),
    path('ping/', PingView.as_view(), name="ping"),
]
