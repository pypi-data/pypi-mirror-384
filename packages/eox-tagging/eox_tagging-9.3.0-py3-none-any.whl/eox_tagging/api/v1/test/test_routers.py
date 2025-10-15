"""
Test classes for Tags router
"""
from django.test import TestCase
from django.urls import reverse


class TestRouters(TestCase):
    """Test class for API router."""

    def test_get_route_for_list_tags(self):
        """Used to test correctness of list route."""
        list_route = reverse("tag-list")

        self.assertEqual(list_route, "/api/v1/tags/")

    def test_get_route_for_tag_details(self):
        """Used to test correctness of details route."""
        detail_route = reverse("tag-detail", args=[1])

        self.assertEqual(detail_route, "/api/v1/tags/1/")
