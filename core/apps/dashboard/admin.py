from django.contrib import admin
from .models import Member, App, File, Folder, Setting, Order

admin.site.register(Member)
admin.site.register(App)
admin.site.register(File)
admin.site.register(Folder)
admin.site.register(Setting)
admin.site.register(Order)
