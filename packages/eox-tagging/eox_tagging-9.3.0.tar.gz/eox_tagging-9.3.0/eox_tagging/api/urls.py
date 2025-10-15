"""
URL module for Tags API.
"""
from django.urls import include, re_path

from eox_tagging.api.v1.routers import router

urlpatterns = [
    re_path(r'v1/', include(router.urls)),
]
