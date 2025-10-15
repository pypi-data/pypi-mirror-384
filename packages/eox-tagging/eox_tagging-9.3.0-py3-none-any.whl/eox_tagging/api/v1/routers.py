"""
Router module for Tag API.
"""
from rest_framework.routers import DefaultRouter

from eox_tagging.api.v1.viewset import TagViewSet

router = DefaultRouter()
router.register(r'tags', TagViewSet, basename='tag')
