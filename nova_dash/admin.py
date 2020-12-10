from django.contrib import admin
from .models import Customer, App, Address
# Register your models here.

admin.site.register(Customer)
admin.site.register(App)
admin.site.register(Address)
