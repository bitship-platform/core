from django.urls import path, re_path, include
from .views import DashView, BillingView, LoginView, LogoutView, SettingView,\
    PaypalTransaction, media_access, ActivityView, HelpView, TestView, AdminLoginView
from .app_views import ManageView, AppManageView, AppLogView, AppConsoleView, AppManagementView
from .utility_view import TarballDownload, BackupDownload, set_app_config
from .feature_view import TransactionView, TransactionUtility, PromoCodeView, ExchangeView
from django.conf.urls import url
urlpatterns = [

    path('', LoginView.as_view(), name='home'),
    path('login/', LoginView.as_view()),
    url(r'^admin/login/', AdminLoginView.as_view(), name="admin_login"),
    url(r'^panel/', DashView.as_view(), name="panel"),
    url(r'^test/', TestView.as_view(), name="test"),
    url(r'^how-to-deploy/', HelpView.as_view(), name="help_deploy"),
    url(r'^billing/process/', PaypalTransaction.as_view(), name='billing_process'),
    url(r'^billing/', BillingView.as_view(), name='billing'),
    url(r'^manage/app/backup/(?P<app_id>.*)', BackupDownload.as_view(), name='backup'),
    url(r'^manage/(?P<app_id>[0-9]+)/logs/', AppConsoleView.as_view(), name='app_log'),
    url(r'^manage/(?P<app_id>[0-9]+)/(?P<folder_id>.+)', ManageView.as_view(), name='browse'),
    url(r'^manage/(?P<app_id>[0-9]+)', ManageView.as_view(), name='manage'),
    url(r'^manage/', ManageView.as_view(), name='rename'),
    url(r'^settings/', SettingView.as_view(), name='settings'),
    url(r'^activity/', ActivityView.as_view(), name='activity'),
    url(r'^transactions/utility/', TransactionUtility.as_view(), name='transaction_utility'),
    url(r'^transactions/', TransactionView.as_view(), name='transactions'),
    url(r'^promocode/', PromoCodeView.as_view(), name='promo_code'),
    url(r'^exchange/', ExchangeView.as_view(), name='exchange'),
    url(r'^logout/', LogoutView.as_view(), name='logout'),
    url(r'^accounts/login/', LoginView.as_view(), name='login'),
    url(r'^media/(?P<path>.*)', media_access, name='media'),
    url(r'^app/manage/', AppManageView.as_view(), name="app_manage"),
    url(r'^app/config/', set_app_config, name="app_config"),
    url(r'^app/logs/(?P<app_id>.*)', AppLogView.as_view(), name="app_logs"),
    url(r'^app/tarball/(?P<uu_id>.*)', TarballDownload.as_view(), name='app'),
    url(r'^app/panel/options/', AppManagementView.as_view(), name="app_management"),
]
