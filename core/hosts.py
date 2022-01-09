from django_hosts import patterns, host

host_patterns = patterns(
    '',
    host(r'www', 'main_site.urls', name='www'),
    host(r'dashboard', 'nova_dash.urls', name='dashboard'),
    host(r'admin', 'Nova.urls', name='admin'),
    host(r'api', 'nova_api.urls', name='api'),
)