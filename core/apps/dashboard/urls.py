from django.urls import path, re_path
from .views import DashView, TeamsView, LoginView, LogoutView, SettingView,\
    media_access, ActivityView, HelpView, AdminLoginView, RedirectLoginView
from .app_views import ManageView, AppManageView, AppLogView, AppConsoleView, AppManagementView
from .utility_view import TarballDownload, set_app_config


urlpatterns = [

    path('', RedirectLoginView.as_view(), name='redirect'),
    path('login/', LoginView.as_view()),
    re_path(r'^admin/login/', AdminLoginView.as_view(), name="admin_login"),
    re_path(r'^panel/', DashView.as_view(), name="panel"),
    re_path(r'^how-to-deploy/', HelpView.as_view(), name="help_deploy"),
    re_path(r'^teams/', TeamsView.as_view(), name='teams'),
    re_path(r'^manage/(?P<app_id>[0-9]+)/logs/', AppConsoleView.as_view(), name='app_log'),
    re_path(r'^manage/(?P<app_id>[0-9]+)/(?P<folder_id>.+)', ManageView.as_view(), name='browse'),
    re_path(r'^manage/(?P<app_id>[0-9]+)', ManageView.as_view(), name='manage'),
    re_path(r'^manage/', ManageView.as_view(), name='rename'),
    re_path(r'^settings/', SettingView.as_view(), name='settings'),
    re_path(r'^activity/', ActivityView.as_view(), name='activity'),
    re_path(r'^logout/', LogoutView.as_view(), name='logout'),
    re_path(r'^accounts/login/', LoginView.as_view(), name='login'),
    re_path(r'^media/(?P<path>.*)', media_access, name='media'),
    re_path(r'^app/manage/', AppManageView.as_view(), name="app_manage"),
    re_path(r'^app/config/', set_app_config, name="app_config"),
    re_path(r'^app/logs/(?P<app_id>.*)', AppLogView.as_view(), name="app_logs"),
    re_path(r'^app/tarball/(?P<uu_id>.*)', TarballDownload.as_view(), name='app'),
    re_path(r'^app/panel/options/', AppManagementView.as_view(), name="app_management"),
]
