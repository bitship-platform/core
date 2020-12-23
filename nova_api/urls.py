from django.urls import path
from django.conf import settings
from django.conf.urls import url
from .views import AddItemView
from django.conf.urls.static import static
urlpatterns = [

    path('data/manage/', AddItemView.as_view(), name='home'),
]