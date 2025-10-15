"""
Test classes for Tags model
"""
import datetime

from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.contrib.sites.models import Site
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.test import TestCase, override_settings
from django.utils import timezone
from mock import Mock, patch
from opaque_keys.edx.keys import CourseKey

from eox_tagging.constants import AccessLevel
from eox_tagging.models import OpaqueKeyProxyModel, Tag, TagQuerySet


@override_settings(
    EOX_TAGGING_DEFINITIONS=[
        {
            "tag_type": "example_tag_1",
            "validate_owner_object": "User",  # default = Site
            "validate_target_object": "User",
            "validate_access": {"equals": "PRIVATE"},
            "validate_tag_value": {"in": ["example_tag_value", "example_tag_value_1"]},
        },
        {
            "tag_type": "example_tag_2",
            "owner_object": "Site",
            "validate_target_object": "User",
            "validate_tag_value": {"opaque_key": "CourseKey"},
        },
        {
            "tag_type": "example_tag_3",
            "validate_tag_value": {"regex": r".*eduNEXT$"},
            "validate_target_object": "User",
            "validate_expiration_date": {"exist": True},
        },
        {
            "tag_type": "example_tag_4",
            "validate_tag_value": {"in": ["example_tag_value", "example_tag_value_2"]},
            "validate_target_object": "User",
        }
    ])
class TestTag(TestCase):
    """Class for testing the Tag model."""

    def setUp(self):
        """ Model setup used to create objects used in tests."""
        self.target_object = User.objects.create(username="Tag")
        self.owner_object = User.objects.create(username="User")
        self.fake_owner_object = Site.objects.create()
        self.course_key = CourseKey.from_string('course-v1:edX+FUN101x+3T2017')

        self.test_tag = Tag.objects.create_tag(
            tag_value="example_tag_value",
            tag_type="example_tag_1",
            target_object=self.target_object,
            owner_object=self.owner_object,
            access=AccessLevel.PRIVATE,
        )

    @override_settings(
        EOX_TAGGING_DEFINITIONS=[
            {
                "tag_type": "example_tag_4",
                "validate_tag_value": {"belongs": ["example_tag_value", "example_tag_value_2"]},
                "validate_target_object": "OpaqueKeyProxyModel",
            }
        ])
    def test_bad_validation_config(self):
        """
        Used to check that if the validation is not defined then the creation fails.
        In this case, `belongs` is not defined.
        """
        with self.assertRaises(ValidationError):
            Tag.objects.create_tag(
                tag_value="example_tag_value",
                tag_type="example_tag_4",
                target_object=self.target_object,
                owner_object=self.fake_owner_object
            )

    @override_settings(
        EOX_TAGGING_DEFINITIONS=[
            {
                "tag_type": "example_tag_4",
                "validate_tag_name": {"in": ["example_tag_value", "example_tag_value_2"]},
                "validate_target_object": "OpaqueKeyProxyModel",
            }
        ])
    def test_bad_field_config(self):
        """
        Used to check that if the validation is not defined then the creation fails.
        In this case, `tag_name` is not defined.
        """
        with self.assertRaises(ValidationError):
            Tag.objects.create_tag(
                tag_value="example_tag_value",
                tag_type="example_tag_4",
                target_object=self.target_object,
                owner_object=self.fake_owner_object
            )

    @override_settings(EOX_TAGGING_DEFINITIONS=[])
    def test_empty_setting(self):
        """
        Used to test saving without validations defined.
        If the definitions array is empty then the tag cannot be created.
        """
        with self.assertRaises(ValidationError):
            Tag.objects.create_tag(
                tag_value="example_tag_value",
                tag_type="example_tag_1",
                target_object=self.target_object,
                owner_object=self.owner_object,
                access=AccessLevel.PRIVATE,
            )

    @override_settings(
        EOX_TAGGING_DEFINITIONS=[
            {
                "tag_type": "subscription_tier",
                "force_access": "private",
                "validate_tag_value": {"in": ["free", "private"]},
                "validate_owner_object": "User",
                "validate_target_object": "User",
            },
        ])
    def test_force_access_configuration(self):
        """
        Used to test that if a field is `forced` then it must be set to the value
        specified."""
        tag = Tag.objects.create_tag(
            tag_value="free",
            tag_type="subscription_tier",
            target_object=self.target_object,
            owner_object=self.owner_object,
        )

        self.assertIsNotNone(tag.id)
        self.assertEqual(tag.access.name, "PRIVATE")

    @override_settings(
        EOX_TAGGING_DEFINITIONS=[
            {
                "tag_type": "subscription_tier",
                "force_activation_date": "2020-10-19 10:20:30",
                "validate_tag_value": {"in": ["free", "private"]},
                "validate_owner_object": "User",
                "validate_target_object": "User",
            },
        ])
    def test_force_activation_date_configuration(self):
        """Used to test that if a field is `forced` the must be set to the value specified."""
        tag = Tag.objects.create_tag(
            tag_value="free",
            tag_type="subscription_tier",
            target_object=self.target_object,
            owner_object=self.owner_object,
        )

        self.assertIsNotNone(tag.id)
        self.assertEqual(str(tag.activation_date), "2020-10-19 10:20:30")

    @override_settings(
        EOX_TAGGING_DEFINITIONS=[
            {
                "tag_type": "subscription_tier",
                "force_expiration_date": "2020-10-19 10:20:30",
                "validate_tag_value": {"in": ["free", "private"]},
                "validate_owner_object": "User",
                "validate_target_object": "User",
            },
        ])
    def test_force_expiration_date_configuration(self):
        """Used to test that if a field is `forced` the must be set to the value specified."""
        tag = Tag.objects.create_tag(
            tag_value="free",
            tag_type="subscription_tier",
            target_object=self.target_object,
            owner_object=self.owner_object,
        )

        self.assertIsNotNone(tag.id)
        self.assertEqual(str(tag.expiration_date), "2020-10-19 10:20:30")

    @override_settings(
        EOX_TAGGING_DEFINITIONS=[
            {
                "tag_type": "subscription_tier",
                "force_tag_value": "free",
                "validate_owner_object": "User",
                "validate_target_object": "User",
            },
        ])
    def test_force_tag_value_configuration(self):
        """Used to test that if a field is `forced` the must be set to the value specified."""
        tag = Tag.objects.create_tag(
            tag_type="subscription_tier",
            target_object=self.target_object,
            owner_object=self.owner_object,
        )

        self.assertIsNotNone(tag.id)
        self.assertEqual(tag.tag_value, "free")

    @override_settings(
        EOX_TAGGING_DEFINITIONS=[
            {
                "tag_type": "example_tag_7",
                "validate_owner_object": "User",
                "validate_access": {"equals": "PRIVATE"},
                "validate_tag_value": {"in": ["example_tag_value", "example_tag_value_1"]},
            }]
    )
    def test_create_config_without_target(self):
        """
        Used to test creating a Tag without target.
        It results in validation error.
        """
        with self.assertRaises(ValidationError):
            Tag.objects.create_tag(
                tag_value="example_tag_value",
                tag_type="example_tag_7",
                target_object=self.target_object,
                owner_object=self.owner_object,
                access=AccessLevel.PRIVATE,
            )

    def test_valid_tag(self):
        """ Used to confirm that the tags created are valid."""
        tag_status = getattr(self.test_tag, "status")

        self.assertEqual(tag_status, 1)

    def test_tag_value(self):
        """ Used to confirm that the tag_value is correct."""
        tag_value = getattr(self.test_tag, "tag_value")

        self.assertEqual(tag_value, "example_tag_value")

    def test_tag_type(self):
        """ Used to confirm that the tag_type is correct."""
        tag_value = getattr(self.test_tag, "tag_type")

        self.assertEqual(tag_value, "example_tag_1")

    def test_tag_value_not_in_settings(self):
        """
        Used to confirm validation error when the value is not defined in settings.
        If the key validate_tag_value or tag_value is defined in the config settings
        of the tag, then tag_value must exist or match the validation defined.
        """
        with self.assertRaises(ValidationError):
            Tag.objects.create_tag(
                tag_value="testValues",
                tag_type="example_tag_1",
                target_object=self.target_object,
                owner_object=self.owner_object,
            )

    def test_tag_type_not_in_settings(self):
        """
        Used to confirm validation error when the value is not defined in settings.
        Due to tag_type is a required field, it must exist in any case and match the
        value defined.
        """
        with self.assertRaises(ValidationError):
            Tag.objects.create_tag(
                tag_value="example_tag_value",
                tag_type="testTypes",
                target_object=self.target_object,
                owner_object=self.owner_object,
            )

    def test_tag_different_generic_objects_fail(self):
        """
        Used to confirm that tags can't be created if the target_object does not match
        the definition.
        """
        with self.assertRaises(ValidationError):
            Tag.objects.create_tag(
                tag_value="course-v1:demo-courses+DM101+2017",
                tag_type="example_tag_2",
                target_object=self.fake_owner_object,  # Is site not user as defined
                owner_object=self.fake_owner_object,
            )

    def test_tag_validation_regex_accepts_pattern(self):
        """ Used to confirm that tags can accept a pattern if defined in settings."""
        Tag.objects.create_tag(
            tag_value="example by eduNEXT",
            tag_type="example_tag_3",
            target_object=self.target_object,
            owner_object=self.fake_owner_object,
            expiration_date=datetime.date(2020, 10, 19),
        )

    def test_tag_validation_regex_accepts_pattern_fail(self):
        """ Used to confirm that saving fails if tag does not match pattern defined in settings."""
        with self.assertRaises(ValidationError):
            Tag.objects.create_tag(
                tag_value="example by edx",
                tag_type="example_tag_3",
                target_object=self.target_object,
                owner_object=self.owner_object,
                expiration_date=datetime.date(2020, 10, 19),
            )

    def test_tag_validation_owner_must_be_site(self):
        """ Used to confirm that a tag must have a site as owner."""
        with self.assertRaises(ValidationError):
            Tag.objects.create_tag(
                tag_value="example by eduNEXT",
                tag_type="example_tag_3",
                target_object=self.target_object,
                owner_object=self.target_object,  # Is user and not site as specified
                expiration_date=datetime.date(2020, 10, 19),
            )

    def test_tag_immutable(self):
        """ Used to confirm that the tags can't be updated."""
        setattr(self.test_tag, "tag_value", "value")
        with self.assertRaises(ValidationError):
            self.test_tag.save()

    def test_find_by_owner(self):
        """ Used to confirm that can retrieve tags by owner_object."""
        tags_owned = Tag.objects.find_by_owner(owner_type="user", owner_id={"username": "User"})

        self.assertEqual(tags_owned.first().owner_object_id, self.owner_object.id)

    def test_find_all_tags_for(self):
        """Used to confirm that can retrieve tags by target object."""
        tags = Tag.objects.find_all_tags_for(target_type="user", target_id={"username": "Tag"})

        self.assertEqual(tags.first().target_object_id, self.target_object.id)

    def test_tag_soft_delete(self):
        """
        Used to confirm that the tags can be invalidated soft deleting them.
        This also means that they will no longer exist in active tags set.
        """
        self.test_tag.delete()

        deleted_tag = Tag.objects.inactive().get(id=self.test_tag.id)
        with self.assertRaises(ObjectDoesNotExist):
            Tag.objects.active().get(id=self.test_tag.id)
        self.assertGreater(timezone.now(), deleted_tag.inactivated_at)

    def test_create_tag_without_target_object(self):
        """
        Used to test that a tag can't be created without a target.
        """
        with self.assertRaises(ValidationError):
            Tag.objects.create_tag(
                tag_value="example_tag_value",
                tag_type="example_tag_4",
                owner_object=self.fake_owner_object,
            )

    def test_create_with_default_owner(self):
        """
        Used to test that if the configuration does not have an owner defined, then
        the tag must belong to a site.
        """
        Tag.objects.create_tag(
            tag_value="example_tag_value",
            tag_type="example_tag_4",
            target_object=self.target_object,
            owner_object=self.fake_owner_object,
        )

    def test_create_without_matching_default_owner(self):
        """
        Used to test that if the configuration does not have an owner defined, then
        the tag must belong to a site.
        """
        with self.assertRaises(ValidationError):
            Tag.objects.create_tag(
                tag_value="example_tag_value",
                tag_type="example_tag_4",
                target_object=self.target_object,
                owner_object=self.owner_object,
            )

    def test_create_without_default_owner(self):
        """
        Used to test that if the configuration does not have an owner defined, then
        the tag must belong to a site.
        """
        with self.assertRaises(ValidationError):
            Tag.objects.create_tag(
                tag_value="example_tag_value",
                tag_type="example_tag_4",
                target_object=self.target_object,
            )

    @override_settings(
        EOX_TAGGING_DEFINITIONS=[
            {
                "tag_type": "example_tag_3",
                "validate_tag_value": {"regex": r".*eduNEXT$"},
                "validate_target_object": "User",
                "validate_expiration_date": {"exist": True, "between": ["2020-10-19 10:20:30", "2020-12-04 10:20:30"]},
                "validate_activation_date": "2020-06-16 10:20:30",
            }]
    )
    def test_validation_date_between(self):
        """
        Used to test date validations using BETWEEN validator.
        This means that expiration_date must be grater or equal than "2020-10-19 10:20:30",
        or less or equal than "2020-12-04 10:20:30".
        """
        tag = Tag.objects.create_tag(
            tag_value="example by eduNEXT",
            tag_type="example_tag_3",
            target_object=self.target_object,
            owner_object=self.fake_owner_object,
            expiration_date=datetime.datetime(2020, 10, 19, 10, 20, 30),
            activation_date=datetime.datetime(2020, 6, 16, 10, 20, 30),
        )

        self.assertIsNotNone(tag.id)

    @override_settings(
        EOX_TAGGING_DEFINITIONS=[
            {
                "tag_type": "example_tag_3",
                "validate_tag_value": {"regex": r".*eduNEXT$"},
                "validate_target_object": "User",
                "validate_expiration_date": {"exist": True, "between": ["2020-10-19 10:20:30", "2020-12-04 10:20:30"]},
                "validate_activation_date": "2020-06-16 10:20:30",
            }]
    )
    def test_validation_date_not_in_between(self):
        """
        Used to test date validations using BETWEEN validator. In this case, the validator must
        raise a validation error because the date is not in between the two dates defined.
        """
        with self.assertRaises(ValidationError):
            Tag.objects.create_tag(
                tag_value="example by eduNEXT",
                tag_type="example_tag_3",
                target_object=self.target_object,
                owner_object=self.fake_owner_object,
                expiration_date=datetime.datetime(2020, 5, 19, 10, 20, 30),
                activation_date=datetime.datetime(2020, 6, 16, 10, 20, 30),
            )

    @override_settings(
        EOX_TAGGING_DEFINITIONS=[
            {
                "tag_type": "example_tag_3",
                "validate_tag_value": {"regex": r".*eduNEXT$"},
                "validate_target_object": "User",
                "validate_expiration_date": {"in": ["2020-12-04 10:20:30", "2020-10-19 10:20:30"]},
                "validate_activation_date": "2020-06-16 10:20:30",
            }]
    )
    def test_validation_date_in_list(self):
        """
        Used to test date validations using IN validator. This means that expiration_date bust be equal to
        "2020-12-04 10:20:30" or equal to "2020-10-19 10:20:30".
        """
        tag = Tag.objects.create_tag(
            tag_value="example by eduNEXT",
            tag_type="example_tag_3",
            target_object=self.target_object,
            owner_object=self.fake_owner_object,
            expiration_date=datetime.datetime(2020, 10, 19, 10, 20, 30),
            activation_date=datetime.datetime(2020, 6, 16, 10, 20, 30),
        )

        self.assertIsNotNone(tag.id)

    @override_settings(
        EOX_TAGGING_DEFINITIONS=[
            {
                "tag_type": "example_tag_3",
                "validate_tag_value": {"regex": r".*eduNEXT$"},
                "validate_target_object": "User",
                "validate_expiration_date": {"in": ["2020-12-04 10:20:30", "2020-10-19 10:20:30"]},
                "validate_activation_date": "2020-06-16 10:20:30",
            }]
    )
    def test_validation_date_not_in_list(self):
        """
        Used to test date validations using IN validator. In this case, the validator must raise
        a validation error because the date is different two those defined inside the array.
        """
        with self.assertRaises(ValidationError):
            Tag.objects.create_tag(
                tag_value="example by eduNEXT",
                tag_type="example_tag_3",
                target_object=self.target_object,
                owner_object=self.fake_owner_object,
                expiration_date=datetime.datetime(2020, 4, 19, 10, 20, 30),
                activation_date=datetime.datetime(2020, 6, 16, 10, 20, 30),
            )

    def test_soft_delete_queryset(self):
        """Used to test deactivating tags using a tag queryset."""
        Tag.objects.delete()

        self.assertFalse(Tag.objects.active())


class TestTagQuerysetManager(TestCase):
    """
    Test cases for queryset used as tag manager. This test cases are focused to
    check how the method behaves with objects like CourseOverview and CourseEnrollment.
    """

    def setUp(self):
        self.tag_query_set = TagQuerySet()
        self.course_id = "course-v1:edX+DemoX+Demo_Course"

    @patch.object(OpaqueKeyProxyModel, 'objects')
    def test_create_tag_with_course(self, opaque_objects_mock):
        """Test tagging a course using TagQueryset manager."""
        self.tag_query_set.create = Mock()
        course_mock = Mock()
        opaque_mock = Mock()
        opaque_objects_mock.get_or_create.return_value = opaque_mock, Mock()
        course_mock.__class__.__name__ = "CourseOverview"
        kwargs = {
            "target_object": course_mock,
        }

        self.tag_query_set.create_tag(**kwargs)

        self.tag_query_set.create.assert_called_once_with(target_object=opaque_mock)

    @patch.object(TagQuerySet, '_get_object_for_this_type')
    def test_find_all_tags_for_course(self, _get_object_for_this_type):
        """Test getting tags with course as target."""
        target_type, target_id = "CourseOverview", 1
        target, target_ctype = Mock(), Mock()
        _get_object_for_this_type.return_value = target, target_ctype
        self.tag_query_set.filter = Mock()
        target.values_list.return_value = [1]

        self.tag_query_set.find_all_tags_for(target_type, target_id)

        _get_object_for_this_type.assert_called_once_with(
            "opaquekeyproxymodel",
            target_id
        )
        self.tag_query_set.filter.assert_called_once_with(
            target_type=target_ctype,
            target_object_id__in=[1],
        )

    @patch.object(ContentType, 'objects')
    def test_get_objects_for_type_user(self, content_type_mock):
        """Test getting courses associated with tags."""
        ctype_object = Mock()
        content_type_mock.get.return_value = ctype_object
        object_type, object_id = "User", {
            "username": "username",
        }

        self.tag_query_set._get_object_for_this_type(  # pylint: disable=protected-access
            object_type,
            object_id,
        )

        content_type_mock.get.assert_called_once_with(model=object_type)
        ctype_object.get_all_objects_for_this_type.assert_called_once_with(
            username="username",
        )

    @patch.object(ContentType, 'objects')
    def test_get_objects_for_type_course(self, content_type_mock):
        """Test getting courses associated with tags."""
        ctype_object = Mock()
        content_type_mock.get.return_value = ctype_object
        object_type, object_id = "OpaqueKeyProxyModel", {
            "course_id": self.course_id,
        }
        object_id_modified = {
            "opaque_key": CourseKey.from_string(self.course_id),
        }

        self.tag_query_set._get_object_for_this_type(  # pylint: disable=protected-access
            object_type,
            object_id,
        )

        content_type_mock.get.assert_called_once_with(model=object_type)
        ctype_object.get_all_objects_for_this_type.assert_called_once_with(
            **object_id_modified
        )

    @patch.object(ContentType, 'objects')
    def test_get_objects_for_type_enrollment(self, content_type_mock):
        """Test getting enrollments associated with tags."""
        ctype_object = Mock()
        content_type_mock.get.return_value = ctype_object
        object_type, object_id = "CourseEnrollment", {
            "course_id": self.course_id,
            "username": "username",
        }
        object_id_modified = {
            "course_id": CourseKey.from_string(self.course_id),
            "user__username": "username",
        }

        self.tag_query_set._get_object_for_this_type(   # pylint: disable=protected-access
            object_type,
            object_id,
        )

        content_type_mock.get.assert_called_once_with(model=object_type)
        ctype_object.get_all_objects_for_this_type.assert_called_once_with(
            **object_id_modified
        )
