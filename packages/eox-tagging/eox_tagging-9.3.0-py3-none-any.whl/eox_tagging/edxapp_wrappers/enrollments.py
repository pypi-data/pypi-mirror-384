""" Backend abstraction. """
from importlib import import_module

from django.conf import settings


def get_enrollment_object(*args, **kwargs):
    """ Get enrollment object. """
    backend_function = settings.EOX_TAGGING_GET_ENROLLMENT_OBJECT
    backend = import_module(backend_function)
    return backend.get_enrollment_object(*args, **kwargs)


CourseEnrollment = get_enrollment_object()
