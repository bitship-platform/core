from django.contrib import admin
from .models import Customer, App, Address, File, Folder, Setting, Order, Transaction, Offer, Promo, Referral
# Register your models here.

admin.site.register(Customer)
admin.site.register(App)
admin.site.register(Address)
admin.site.register(File)
admin.site.register(Folder)
admin.site.register(Setting)
admin.site.register(Order)
admin.site.register(Transaction)
admin.site.register(Offer)
admin.site.register(Promo)
admin.site.register(Referral)
