"""
Backend CourseOverview file, here are all the methods from
openedx.core.djangoapps.content.course_overviews.
"""
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview  # pylint: disable=import-error


def get_course_overview():
    """Backend to get course overview."""
    return CourseOverview
