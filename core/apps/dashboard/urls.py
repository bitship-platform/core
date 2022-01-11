from django.urls import path, re_path
from .views import DashView, BillingView, LoginView, LogoutView, SettingView,\
    PaypalTransaction, media_access, ActivityView, HelpView, TestView, AdminLoginView
from .app_views import ManageView, AppManageView, AppLogView, AppConsoleView, AppManagementView
from .utility_view import TarballDownload, BackupDownload, set_app_config
from .feature_view import PromoCodeView, ExchangeView


urlpatterns = [

    path('', LoginView.as_view(), name='home'),
    path('login/', LoginView.as_view()),
    re_path(r'^admin/login/', AdminLoginView.as_view(), name="admin_login"),
    re_path(r'^panel/', DashView.as_view(), name="panel"),
    re_path(r'^test/', TestView.as_view(), name="test"),
    re_path(r'^how-to-deploy/', HelpView.as_view(), name="help_deploy"),
    re_path(r'^billing/process/', PaypalTransaction.as_view(), name='billing_process'),
    re_path(r'^billing/', BillingView.as_view(), name='billing'),
    re_path(r'^manage/app/backup/(?P<app_id>.*)', BackupDownload.as_view(), name='backup'),
    re_path(r'^manage/(?P<app_id>[0-9]+)/logs/', AppConsoleView.as_view(), name='app_log'),
    re_path(r'^manage/(?P<app_id>[0-9]+)/(?P<folder_id>.+)', ManageView.as_view(), name='browse'),
    re_path(r'^manage/(?P<app_id>[0-9]+)', ManageView.as_view(), name='manage'),
    re_path(r'^manage/', ManageView.as_view(), name='rename'),
    re_path(r'^settings/', SettingView.as_view(), name='settings'),
    re_path(r'^activity/', ActivityView.as_view(), name='activity'),
    re_path(r'^promocode/', PromoCodeView.as_view(), name='promo_code'),
    re_path(r'^exchange/', ExchangeView.as_view(), name='exchange'),
    re_path(r'^logout/', LogoutView.as_view(), name='logout'),
    re_path(r'^accounts/login/', LoginView.as_view(), name='login'),
    re_path(r'^media/(?P<path>.*)', media_access, name='media'),
    re_path(r'^app/manage/', AppManageView.as_view(), name="app_manage"),
    re_path(r'^app/config/', set_app_config, name="app_config"),
    re_path(r'^app/logs/(?P<app_id>.*)', AppLogView.as_view(), name="app_logs"),
    re_path(r'^app/tarball/(?P<uu_id>.*)', TarballDownload.as_view(), name='app'),
    re_path(r'^app/panel/options/', AppManagementView.as_view(), name="app_management"),
]
