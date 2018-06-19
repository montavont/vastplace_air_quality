from django.conf.urls import url
from rest_framework.urlpatterns import format_suffix_patterns
from . import views

rest_patterns = [
    url(r'grafana$', views.grafana, name='grafana'),
    url(r'grafana/query$', views.grafana_query, name='grafana_query'),
    url(r'grafana/search$', views.grafana_search, name='grafana_search'),
    url(r'grafana_sources$', views.grafana_sources, name='grafana'),
    url(r'grafana_sources/query$', views.grafana_sources_query, name='grafana_sources_query'),
    url(r'grafana_sources/search$', views.grafana_sources_search, name='grafana_sources_search'),
]

rest_patterns = format_suffix_patterns(rest_patterns)


urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'air_map', views.air_map, name='air_map'),
    url(r'air_test', views.air_test, name='air_test'),
    url(r'bargraph/{(?P<targetId_str>[,\w]+)}$', views.bargraph, name='ambassadair_bargraphs'),
] + rest_patterns

