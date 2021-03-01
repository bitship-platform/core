from django.urls import path, re_path, include
from .views import DashView, BillingView, LoginView, LogoutView, ManageView, SettingView, media_access,\
    Transaction, TarballDownload, AppManageView, set_app_config, BackupDownload, ActivityView, TransactionView
from django.conf.urls import url
urlpatterns = [

    path('', LoginView.as_view(), name='home'),
    path('login/', LoginView.as_view()),
    url(r'^panel/', DashView.as_view(), name="panel"),
    url(r'^billing/process/', Transaction.as_view(), name='billing_process'),
    url(r'^billing/', BillingView.as_view(), name='billing'),
    url(r'^manage/(?P<app_id>[0-9]+)/(?P<folder_id>.+)', ManageView.as_view(), name='browse'),
    url(r'^manage/(?P<app_id>[0-9]+)', ManageView.as_view(), name='manage'),
    url(r'^manage/', ManageView.as_view(), name='rename'),
    url(r'^settings/', SettingView.as_view(), name='settings'),
    url(r'^activity/', ActivityView.as_view(), name='activity'),
    url(r'^transactions/', TransactionView.as_view(), name='transactions'),
    url(r'^logout/', LogoutView.as_view(), name='logout'),
    url(r'^accounts/login/', LoginView.as_view(), name='login'),
    url(r'^media/(?P<path>.*)', media_access, name='media'),
    url(r'^app/manage/', AppManageView.as_view(), name="app_manage"),
    url(r'^app/config/', set_app_config, name="app_config"),
    url(r'^app/tarball/(?P<uu_id>.*)', TarballDownload.as_view(), name='app'),
    url(r'^app/backup/(?P<app_id>[0-9]+)', BackupDownload.as_view(), name='backup'),
]

# urlpatterns = urlpatterns + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
