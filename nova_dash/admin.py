from django.contrib import admin
from .models import Customer, App, Address, File, Folder, Setting, Order, Transaction
# Register your models here.

admin.site.register(Customer)
admin.site.register(App)
admin.site.register(Address)
admin.site.register(File)
admin.site.register(Folder)
admin.site.register(Setting)
admin.site.register(Order)
admin.site.register(Transaction)
