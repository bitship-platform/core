from django.urls import path
from .views import DashView, BillingView, ProfileView, LoginView
from django.conf.urls import url
from django.contrib.auth.views import LogoutView

urlpatterns = [

    path('', LoginView.as_view(), name='home'),
    path('login/', LoginView.as_view()),
    url(r'^user/(?P<user_id>[0-9]{18})/', DashView.as_view(), name="main"),
    url(r'^profile/', ProfileView.as_view(), name='profile'),
    url(r'^billing/', BillingView.as_view(), name='billing'),
    url(r'^logout/', LogoutView.as_view(), name='logout'),
]
