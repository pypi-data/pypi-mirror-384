"""
eox_tagging URL Configuration
"""
from django.urls import include, re_path

from eox_tagging import views
from eox_tagging.api_schema import docs_ui_view

urlpatterns = [
    re_path(r'^eox-info$', views.info_view, name='eox-info'),
    re_path(r'api/', include('eox_tagging.api.urls')),
    re_path(r'^api-docs/$', docs_ui_view, name='apidocs-ui'),
]
