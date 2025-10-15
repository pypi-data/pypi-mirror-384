"""
Custom API permissions module
"""
from django.conf import settings
from django.contrib.auth.models import Permission, User
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ImproperlyConfigured
from django.db.utils import ProgrammingError
from rest_framework import exceptions, permissions


def load_permissions():
    """
    Helper method to load a custom permission on DB that will be use to give access
    to eox-tagging API.
    """
    if settings.EOX_TAGGING_LOAD_PERMISSIONS:
        try:
            content_type = ContentType.objects.get_for_model(User)
            Permission.objects.get_or_create(
                codename='can_call_eox_tagging',
                name='Can access eox-tagging API',
                content_type=content_type,
            )
        except (ProgrammingError, ImproperlyConfigured):
            # This code runs when the app is loaded. If a migration has not been done, a
            # ProgrammingError is raised. The ImproperlyConfigured exception typically
            # indicates a configuration issue. We are bypassing these exceptions to allow
            # the migrations to run smoothly when building the Open edX image.
            pass


class EoxTaggingAPIPermission(permissions.BasePermission):
    """
    Defines a custom permissions to access eox-tagging API
    These permissions make sure that a token is created with the client credentials of the same site is being used on.
    """

    def has_permission(self, request, view):
        """
        To grant access, checks if the requesting user either can call eox-tagging API or if it's an admin user.
        """
        if request.user.is_staff:
            return True

        try:
            application_uri_allowed = request.auth.application.redirect_uri_allowed(request.build_absolute_uri('/'))
        except Exception:  # pylint: disable=broad-except
            application_uri_allowed = False

        try:
            client_url_allowed = request.get_host() in request.auth.client.url
        except Exception:  # pylint: disable=broad-except
            client_url_allowed = False

        if client_url_allowed or application_uri_allowed:
            return request.user.has_perm('auth.can_call_eox_tagging')

        # If we get here either someone is using a token created on one site in a different site
        # or there was a missconfiguration of the oauth client.
        # To prevent leaking important information we return the most basic message.
        raise exceptions.NotAuthenticated(detail="Invalid token")
