"""
Backend CourseEnrollments file, here is the method to access enrollments
objects.
"""


def get_enrollment_object():
    """Backend to get enrollment object."""
    from student.models import CourseEnrollment  # pylint: disable=C0415, E0401
    return CourseEnrollment
