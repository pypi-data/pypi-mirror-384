"""
Authentication definitions.
"""
from importlib import import_module

from django.conf import settings


def get_bearer_authentication():
    """ Gets BearerAuthentication function. """

    backend_function = settings.EOX_TAGGING_BEARER_AUTHENTICATION
    backend = import_module(backend_function)

    return backend.get_bearer_authentication()


BearerAuthentication = get_bearer_authentication()
