"""Module that implements helper functions for other modules."""
import crum
from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from eox_core.edxapp_wrapper.certificates import get_generated_certificate
from eox_core.edxapp_wrapper.users import get_edxapp_user
from opaque_keys.edx.keys import CourseKey

from eox_tagging.edxapp_wrappers.course_overview import CourseOverview
from eox_tagging.edxapp_wrappers.enrollments import CourseEnrollment

GeneratedCertificate = get_generated_certificate()


def get_user(**kwargs):
    """Function used to get users."""
    user_id = kwargs.get("target_id")
    if getattr(settings, "EOX_TAGGING_SKIP_VALIDATIONS", False):  # Skip these validations while testing
        return User.objects.get(username=user_id)

    site = crum.get_current_request().site
    user = get_edxapp_user(username=user_id, site=site)
    return user


def get_course(**kwargs):
    """Function used to get courses from the platform."""
    course_id = kwargs.get("target_id")
    opaque_key = CourseKey.from_string(course_id)
    if getattr(settings, "EOX_TAGGING_SKIP_VALIDATIONS", False):  # Skip these validations while testing
        return object

    course = CourseOverview.get_from_id(opaque_key)
    return course


def get_site(**_kwargs):
    """Function used to get current site."""
    if getattr(settings, "EOX_TAGGING_SKIP_VALIDATIONS", False):  # Use TEST_SITE while testing
        site = Site.objects.get(id=settings.TEST_SITE)
    else:
        site = crum.get_current_request().site
    return site


def get_course_enrollment(**kwargs):
    """Function used to get enrollments from the platform."""
    username = kwargs.get("username")
    course_id = kwargs.get("course_id")

    if getattr(settings, "EOX_TAGGING_SKIP_VALIDATIONS", False):
        return object

    user = get_user(**{"target_id": username})
    course_id = CourseKey.from_string(course_id)
    return CourseEnrollment.objects.get(user_id=user.id, course_id=course_id)


def get_certificate(**kwargs):
    """
    Get GeneratedCertificate for specified id, key download URL or the course_id
    and username associated with it.
    """
    target_id = {}
    verify_uuid = kwargs.get("target_id")
    if verify_uuid:
        target_id["verify_uuid"] = kwargs.get("target_id")
    else:
        target_id["user__username"] = kwargs.get("username")
        target_id["course_id"] = CourseKey.from_string(kwargs.get("course_id"))

    return GeneratedCertificate.objects.get(**target_id)


def get_object_from_edxapp(object_type, **kwargs):
    """Helper function to get objects from edx-platfrom given its identifiers."""
    related_objects = {
        "user": get_user,
        "courseoverview": get_course,
        "site": get_site,
        "courseenrollment": get_course_enrollment,
        "generatedcertificate": get_certificate,
    }
    related_object = related_objects.get(object_type.lower())
    return related_object(**kwargs)
