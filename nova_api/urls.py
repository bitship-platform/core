from django.urls import path
from django.conf import settings
from django.conf.urls import url
from .views import RenewSubscription,AppStatusUpdate
from django.conf.urls.static import static

urlpatterns = [

    path('subscription/renew/', RenewSubscription.as_view(), name='home'),
    path('app/status/<str:app_id>/', AppStatusUpdate.as_view(), name='status'),
]