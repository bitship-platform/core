from django.contrib import admin
from .models import Member, App, File, Folder, Setting, Activity, Team


admin.site.register(Member)
admin.site.register(App)
admin.site.register(Team)
admin.site.register(File)
admin.site.register(Folder)
admin.site.register(Setting)
admin.site.register(Activity)
