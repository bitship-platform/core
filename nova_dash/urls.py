from django.urls import path
from .views import DashView, BillingView, ProfileView, LoginView, LogoutView, ManageView
from django.conf.urls import url

urlpatterns = [

    path('', LoginView.as_view(), name='home'),
    path('login/', LoginView.as_view()),
    url(r'^panel/', DashView.as_view(), name="panel"),
    url(r'^profile/', ProfileView.as_view(), name='profile'),
    url(r'^manage/(?P<app_id>[0-9]+)', ManageView.as_view(), name='manage'),
    url(r'^billing/', BillingView.as_view(), name='billing'),
    url(r'^logout/', LogoutView.as_view(), name='logout'),
    url(r'^accounts/login/', LoginView.as_view(), name='login'),
]
