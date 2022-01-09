from django_hosts import patterns, host

host_patterns = patterns(
    '',
    host(r'www', 'core.apps.site.urls', name='www'),
    host(r'dashboard', 'core.apps.dashboard.urls', name='dashboard'),
    host(r'admin', 'core.urls', name='admin'),
    host(r'api', 'core.apps.api.urls', name='api'),
)