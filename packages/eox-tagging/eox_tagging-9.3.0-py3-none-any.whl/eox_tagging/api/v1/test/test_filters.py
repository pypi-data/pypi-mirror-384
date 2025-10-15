""" Test classes for Tags filters. """

from django.test import TestCase
from mock import Mock, patch

from eox_tagging.api.v1.filters import TagFilter
from eox_tagging.models import Tag


class FilterTest(TestCase):
    """Test class for custom filters."""

    def setUp(self):
        """setUp class."""
        self.filterset = TagFilter()
        self.filterset.request = Mock()

    @patch.object(Tag, 'objects')
    def test_filter_by_target_object(self, objects_mock):
        """Used to test filtering tags by target object."""
        objects_mock.find_all_tags_for = Mock()
        name = "username"
        value = "test"

        self.filterset.filter_by_target_object(objects_mock, name, value)

        objects_mock.find_all_tags_for.assert_called_with(
            target_type="user",
            target_id={name: value},
        )

    @patch.object(Tag, 'objects')
    def test_filter_target_certificate_by_uuid(self, objects_mock):
        """Used to test filtering tags by target object."""
        objects_mock.find_all_tags_for = Mock()
        value = "abdcefg12345"
        name = "certificate_verify_uuid"

        self.filterset.filter_by_target_object(objects_mock, name, value)

        objects_mock.find_all_tags_for.assert_called_with(
            target_type="generatedcertificate",
            target_id={"verify_uuid": value},
        )

    @patch.object(Tag, 'objects')
    def test_filter_target_enrollment(self, objects_mock):
        """
        Used to test filtering tags depending on the target type. This also filters courseenrollments
        given that we must specify the target type besides the other filter parameters, in this case
        course_id and username.
        """
        objects_mock.find_all_tags_for = Mock()
        value = "courseenrollment"
        name = "target_type"
        self.filterset.request.query_params = {
            "enrollment_course_id": "course_id",
            "enrollment_username": "username",
        }

        self.filterset.filter_target_types(objects_mock, name, value)

        objects_mock.find_all_tags_for.assert_called_with(
            target_type=value,
            target_id={"username": "username", "course_id": "course_id"},
        )

    @patch.object(Tag, 'objects')
    def test_filter_target_certificate(self, objects_mock):
        """
        Used to test filtering tags depending on the target type. This also filters generatedcertificate
        given that we must specify the target type besides the other filter parameters, in this case
        course_id and username.
        """
        objects_mock.find_all_tags_for = Mock()
        value = "generatedcertificate"
        name = "target_type"
        self.filterset.request.query_params = {
            "certificate_course_id": "course_id",
            "certificate_username": "username",
        }

        self.filterset.filter_target_types(objects_mock, name, value)

        objects_mock.find_all_tags_for.assert_called_with(
            target_type=value,
            target_id={"username": "username", "course_id": "course_id"},
        )

    @patch.object(Tag, 'objects')
    def test_filter_target_enroll_by_user(self, objects_mock):
        """
        Used to test filtering tags depending on the target type. This also filters courseenrollments
        given that we must specify the target type besides the other filter parameters, in this case
        username.
        """
        objects_mock.find_all_tags_for = Mock()
        value = "courseenrollment"
        name = "target_type"
        self.filterset.request.query_params = {
            "enrollment_username": "username",
        }

        self.filterset.filter_target_types(objects_mock, name, value)

        objects_mock.find_all_tags_for.assert_called_with(
            target_type=value,
            target_id={"username": "username", "course_id": None},
        )

    @patch.object(Tag, 'objects')
    def test_filter_target_enroll_by_course(self, objects_mock):
        """
        Used to test filtering tags depending on the target type. This also filters courseenrollments
        given that we must specify the target type besides the other filter parameters, in this case
        course_id.
        """
        objects_mock.find_all_tags_for = Mock()
        value = "courseenrollment"
        name = "target_type"
        self.filterset.request.query_params = {
            "enrollment_course_id": "course_id",
        }

        self.filterset.filter_target_types(objects_mock, name, value)

        objects_mock.find_all_tags_for.assert_called_with(
            target_type=value,
            target_id={"username": None, "course_id": "course_id"},
        )
