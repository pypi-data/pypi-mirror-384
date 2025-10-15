""" Test classes for API Permissions. """
from django.contrib.auth.models import Permission, User
from django.test import TestCase, override_settings
from mock import Mock
from rest_framework import exceptions

from eox_tagging.api.v1.permissions import EoxTaggingAPIPermission, load_permissions


@override_settings(EOX_TAGGING_LOAD_PERMISSIONS=True)
class TestAPIPermissions(TestCase):
    """Test class for tags viewset."""

    def setUp(self):
        """ Permissions setup."""
        load_permissions()

        # User with permission to acccess the API
        user_permission = Permission.objects.get(codename="can_call_eox_tagging")
        self.user_authorized = User.objects.create(username="user_with_permission")
        self.user_authorized.user_permissions.add(user_permission)

        # Common user without permission
        self.common_user = User.objects.create(username="user_without_permission")

        self.has_permission = EoxTaggingAPIPermission().has_permission

        self.mock_request = Mock()
        self.view = Mock()

    def test_api_access_success(self):
        """Used to test that an authorized user can access to the Tag API."""
        self.mock_request.get_host.return_value = "test.com"
        self.mock_request.user = self.user_authorized
        self.mock_request.auth.client.url = "test.com"

        has_permission = self.has_permission(self.mock_request, self.view)

        self.assertTrue(has_permission)

    def test_api_access_denied(self):
        """Used to test that a unauthorized user can't access to the Tag API."""
        self.mock_request.get_host.return_value = "test.com"
        self.mock_request.user = self.common_user
        self.mock_request.auth.client.url = "test.com"

        has_permission = self.has_permission(self.mock_request, self.view)

        self.assertFalse(has_permission)

    def test_api_access_with_bad_host(self):
        """Used to test that an authorized user without a matching host with client can't access the API."""
        self.mock_request.get_host.return_value = "test_.com"
        self.mock_request.user = self.user_authorized
        self.mock_request.auth.client.url = "test.com"
        self.mock_request.auth.application.redirect_uri_allowed.return_value = False

        with self.assertRaises(exceptions.NotAuthenticated):
            self.has_permission(self.mock_request, self.view)

    def test_api_access_without_valid_host(self):
        """Used to test that an authorized user without a valid host can't access the API."""
        self.mock_request.get_host.return_value = None
        self.mock_request.user = self.user_authorized
        self.mock_request.auth.client.url = "test.com"
        self.mock_request.auth.application.redirect_uri_allowed.return_value = False

        with self.assertRaises(exceptions.NotAuthenticated):
            self.has_permission(self.mock_request, self.view)

    def test_api_access_without_valid_client(self):
        """Used to test that an authorized user without a valid client can't access the API."""
        self.mock_request.get_host.return_value = "test_.com"
        self.mock_request.user = self.user_authorized
        self.mock_request.auth.client.url = None
        self.mock_request.auth.application.redirect_uri_allowed.return_value = False

        with self.assertRaises(exceptions.NotAuthenticated):
            self.has_permission(self.mock_request, self.view)
