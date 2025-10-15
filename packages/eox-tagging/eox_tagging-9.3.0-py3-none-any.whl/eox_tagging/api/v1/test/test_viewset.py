""" Test classes for Tags viewset. """
import datetime
from functools import wraps

from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from django.test import TestCase, override_settings
from django.urls import reverse
from mock import patch
from rest_framework.test import APIClient

from eox_tagging.api.v1.serializers import TagSerializer
from eox_tagging.constants import AccessLevel
from eox_tagging.models import Tag


def mock_decorator(action=None):  # pylint: disable=unused-argument
    """Utility decorator that returns same function."""
    def decorator(func):
        @wraps(func)
        def decorated_function(*args, **kwargs):
            return func(*args, **kwargs)
        return decorated_function
    return decorator


@override_settings(
    EOX_TAGGING_DEFINITIONS=[
        {
            "tag_type": "example_tag_1",
            "validate_owner_object": "User",  # default = Site
            "validate_access": {"equals": "PRIVATE"},
            "validate_tag_value": {"in": ["example_tag_value", "example_tag_value_1"]},
            "validate_target_object": "User",
            "validate_expiration_date": {"exist": True},
        },
        {
            "tag_type": "example_tag_2",
            "validate_owner_object": "Site",
            "validate_access": {"equals": "PRIVATE"},
            "validate_tag_value": {"in": ["example_tag_value", "example_tag_value_1"]},
            "validate_target_object": "User",
            "validate_expiration_date": {"exist": True},
        },
        {
            "tag_type": "example_tag_3",
            "validate_owner_object": "User",
            "validate_access": {"equals": "PUBLIC"},
            "validate_tag_value": {"in": ["example_tag_value", "example_tag_value_1"]},
            "validate_target_object": "Site",
            "validate_expiration_date": {"exist": True},
        },
    ])
class TestTagViewSet(TestCase):
    """Test class for tags viewset."""

    patch_permissions = patch(
        "eox_tagging.api.v1.permissions.EoxTaggingAPIPermission.has_permission",
        return_value=True,
    )
    patch("eox_tagging.api.v1.viewset.audit_method", mock_decorator).start()

    def setUp(self):
        """Model setup used to create objects used in tests."""
        self.target_object = User.objects.create(username="user_test")
        self.owner_site = Site.objects.get(id=settings.TEST_SITE)

        # Client authentication
        self.owner_user = User.objects.create(username="myuser")
        self.client = APIClient()
        self.client.force_authenticate(self.owner_user)

        self.example_tag = Tag.objects.create(
            tag_value="example_tag_value",
            tag_type="example_tag_1",
            target_object=self.target_object,
            owner_object=self.owner_user,
            access=AccessLevel.PRIVATE,
            expiration_date=datetime.datetime(2020, 10, 19, 10, 20, 30),
            activation_date=datetime.datetime(2020, 10, 19, 10, 20, 30),
        )

        self.example_tag_1 = Tag.objects.create(
            tag_value="example_tag_value",
            tag_type="example_tag_2",
            target_object=self.target_object,
            owner_object=self.owner_site,
            access=AccessLevel.PRIVATE,
            expiration_date=datetime.datetime(2020, 9, 19, 10, 30, 40),
            activation_date=datetime.datetime(2020, 9, 19, 10, 30, 40),
        )

        self.example_tag_2 = Tag.objects.create(
            tag_value="example_tag_value",
            tag_type="example_tag_2",
            target_object=self.target_object,
            owner_object=self.owner_site,
            access=AccessLevel.PRIVATE,
            expiration_date=datetime.datetime(2020, 8, 19, 10, 30, 40),
        )

        self.example_tag_3 = Tag.objects.create(
            tag_value="example_tag_value",
            tag_type="example_tag_3",
            target_object=self.owner_site,
            owner_object=self.owner_user,
            access=AccessLevel.PUBLIC,
            expiration_date=datetime.datetime(2020, 7, 19, 10, 30, 40),
        )
        self.key = self.example_tag.key.hex
        # Test URLs
        self.url = reverse("tag-list")
        self.url_details = reverse("tag-detail", args=[self.key])

    @patch_permissions
    def test_get_all_tags(self, _):
        """Used to test getting all tags."""
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)

    @patch_permissions
    def test_retreive_tag(self, _):
        """Used to test getting a tag given its key."""
        response = self.client.get(self.url_details)

        self.assertEqual(response.status_code, 200)

    @patch_permissions
    def test_create_tag(self, _):
        """"Used to test creating a tag."""

        data = {
            "tag_type": "example_tag_1",
            "tag_value": "example_tag_value",
            "target_type": "user",
            "target_id": "user_test",
            "owner_type": "user",
            "access": "PRIVATE",
            "expiration_date": "2020-12-04 10:20:30",
        }

        response = self.client.post(self.url, data, format='json')

        self.assertEqual(response.status_code, 201)

    @patch_permissions
    def test_create_tag_without_owner(self, _):
        """"
        Used to test creating a tag without an owner. The owner should be set as a default
        to be the site.
        """
        data = {
            "tag_type": "example_tag_2",
            "tag_value": "example_tag_value",
            "target_type": "user",
            "target_id": "user_test",
            "access": "PRIVATE",
            "expiration_date": "2020-12-04 10:20:30",
        }

        response = self.client.post(self.url, data, format='json')

        owner_type = response.data.get("meta").get("owner_type")
        self.assertEqual(owner_type, "Site")

    @patch_permissions
    def test_create_tag_with_iso_datetime_format(self, _):
        """"Used to test creating a tag using ISO format in datetime fields."""
        data = {
            "tag_type": "example_tag_1",
            "tag_value": "example_tag_value",
            "target_type": "user",
            "target_id": "user_test",
            "owner_type": "user",
            "access": "PRIVATE",
            "expiration_date": "2020-12-04T10:20:30.15785",
        }

        response = self.client.post(self.url, data, format='json')

        self.assertEqual(response.status_code, 201)

    @patch_permissions
    def test_create_tag_with_wrong_datetime_format(self, _):
        """"
        Used to test creating a tag using wrong format in datetime fields. This results in a
        bad request.
        """
        data = {
            "tag_type": "example_tag_1",
            "tag_value": "example_tag_value",
            "target_type": "user",
            "target_id": "user_test",
            "owner_type": "user",
            "access": "PRIVATE",
            "expiration_date": "12-04-2020 10:20:30",
        }

        response = self.client.post(self.url, data, format='json')

        self.assertEqual(response.status_code, 400)

    @patch_permissions
    def test_create_tag_with_owner_site(self, _):
        """"Used to test creating a tag with site as owner."""
        data = {
            "tag_type": "example_tag_2",
            "tag_value": "example_tag_value",
            "target_type": "user",
            "target_id": "user_test",
            "owner_type": "site",
            "access": "PRIVATE",
            "expiration_date": "2020-12-04 10:30:40",
        }

        response = self.client.post(self.url, data, format='json')

        owner_type = response.data.get("meta").get("owner_type").lower()
        self.assertEqual(owner_type, "site")

    @patch_permissions
    def test_create_tag_with_wrong_owner(self, _):
        """"Used to test creating a tag with wrong owner_type. This results in bad request."""
        data = {
            "tag_type": "example_tag_1",
            "tag_value": "example_tag_value",
            "target_type": "user",
            "target_id": "user_test",
            "owner_type": "course",  # default is site
            "access": "PRIVATE",
            "expiration_date": "2020-12-04 10:30:40 ",
        }

        response = self.client.post(self.url, data, format='json')

        self.assertEqual(response.status_code, 400)

    @patch_permissions
    def test_patch_tag(self, _):
        """Used to test that a tag can't be updated."""
        response = self.client.patch(self.url_details)

        self.assertEqual(response.status_code, 405)

    @patch_permissions
    def test_put_tag(self, _):
        """Used to test that a tag can't be updated."""
        response = self.client.put(self.url_details)

        self.assertEqual(response.status_code, 405)

    @patch_permissions
    def test_filter_by_tag_key(self, _):
        """Used to test getting a tag given its key."""
        query_params = {
            "key": self.example_tag.key.hex,
        }

        response = self.client.get(self.url, query_params)

        data = response.json().get("results")[0]
        self.assertEqual(data.get("key").replace("-", ""), self.key)

    @patch_permissions
    def test_filter_by_username(self, _):
        """Used to test getting a tag given its target."""
        query_params = {
            "username": "user_test",
        }

        response = self.client.get(self.url, query_params)

        data = response.json().get("results")[0].get("meta")
        self.assertEqual(data.get("target_id"), "user_test")

    @patch_permissions
    def test_filter_by_owner_user(self, _):
        """Used to test getting a tag given its owner of type user."""
        query_params = {
            "owner_type": "user",
        }

        response = self.client.get(self.url, query_params)

        results = response.json().get("results")
        owner_is_user = [tag.get("meta").get("owner_type") == "User" for tag in results]
        self.assertTrue(all(owner_is_user))

    @patch_permissions
    def test_filter_by_owner_user_and_target(self, _):
        """Used to test getting a tag given its owner of type user and target type."""
        query_params = {
            "owner_type": "user",
            "target_type": "user",
        }

        response = self.client.get(self.url, query_params)

        results = response.json().get("results")
        owner_is_user = [tag.get("meta").get("owner_type") == "User" for tag in results]
        target_is_user = [tag.get("meta").get("target_type") == "User" for tag in results]
        self.assertTrue(all(owner_is_user))
        self.assertTrue(all(target_is_user))

    @patch_permissions
    def test_filter_by_owner_user_and_username(self, _):
        """Used to test getting a tag given its owner of type user and target username."""
        query_params = {
            "owner_type": "user",
            "username": "user_test",
        }

        response = self.client.get(self.url, query_params)

        results = response.json().get("results")
        owner_type = results[0].get("meta").get("owner_type")
        username = results[0].get("meta").get("target_id")
        self.assertEqual(owner_type, "User")
        self.assertEqual(username, "user_test")

    @patch_permissions
    def test_filter_by_owner_site(self, _):
        """Used to test getting a tag given its owner of type user."""
        query_params = {
            "owner_type": "site",
        }

        response = self.client.get(self.url, query_params)

        data = response.json().get("results")[0]
        owner_type = data.get("meta").get("owner_type").lower()
        self.assertEqual(owner_type, "site")

    @patch_permissions
    def test_filter_by_wrong_owner(self, _):
        """
        Used to test getting a tag given an undefined type of owner. This returns an empty
        queryset.
        """
        query_params = {
            "owner_type": "course",
        }

        response = self.client.get(self.url, query_params)

        data = response.json().get("results")
        self.assertFalse(data)

    @patch_permissions
    def test_filter_by_type(self, _):
        """Used to test getting a tag given its target."""
        query_params = {
            "target_type": "user",
        }

        response = self.client.get(self.url, query_params)

        self.assertEqual(response.status_code, 200)

    @patch_permissions
    def test_filter_by_existent_access(self, _):
        """Used to test filters with valid access level."""
        query_params = {
            "access": "public",
        }

        response = self.client.get(self.url, query_params)

        data = response.json().get("results")[0]
        self.assertEqual(data.get("key").replace("-", ""), self.example_tag_3.key.hex)

    @patch_permissions
    def test_filter_by_non_existent_access(self, _):
        """Used to test filters with invalid access level."""
        query_params = {
            "access": "pub",
        }

        response = self.client.get(self.url, query_params)

        data = response.json().get("results")
        self.assertFalse(data)

    @patch_permissions
    def test_filter_using_after_datetime(self, _):
        """
        Used to test filtering tags using a range datetime filter. In this case, the filter is
        before a specific datetime.
        """
        query_params = {
            "activation_date_after": "2020-10-10 10:20:30",
            "activation_date_0": "2020-10-10 10:20:30",
        }
        datetime_value = datetime.datetime(2020, 10, 10, 10, 20, 30)
        datetime_format = "%Y-%m-%dT%H:%M:%SZ"

        response = self.client.get(self.url, query_params)

        results = response.json().get("results")
        datetimes = [datetime.datetime.strptime(tag.get("activation_date"), datetime_format) > datetime_value
                     for tag in results]
        self.assertTrue(all(datetimes))

    @patch_permissions
    def test_activation_using_before_filter(self, _):
        """
        Used to test filtering tags using a range datetime filter on activation date. In this case, the filter is
        after a specific datetime.
        """
        query_params = {
            "activation_date_before": "2020-10-10 10:20:30",
            "activation_date_1": "2020-10-10 10:20:30",
        }
        datetime_value = datetime.datetime(2020, 10, 10, 10, 20, 30)
        datetime_format = "%Y-%m-%dT%H:%M:%SZ"

        response = self.client.get(self.url, query_params)

        results = response.json().get("results")
        activation_date = [datetime.datetime.strptime(tag.get("activation_date"), datetime_format) < datetime_value
                           for tag in results]
        self.assertTrue(all(activation_date))

    @patch_permissions
    def test_expiration_using_before_filter(self, _):
        """
        Used to test filtering tags using a range datetime filter on expiration date. In this case, the filter is
        after a specific datetime.
        """
        query_params = {
            "expiration_date_before": "2020-10-10 10:20:30",
            "expiration_date_1": "2020-10-10 10:20:30",
        }
        datetime_value = datetime.datetime(2020, 10, 10, 10, 20, 30)
        datetime_format = "%Y-%m-%dT%H:%M:%SZ"

        response = self.client.get(self.url, query_params)

        results = response.json().get("results")
        expiration_date = [datetime.datetime.strptime(tag.get("expiration_date"), datetime_format) < datetime_value
                           for tag in results]
        self.assertTrue(all(expiration_date))

    @patch_permissions
    def test_soft_delete(self, _):
        """Used to test a tag soft deletion."""
        response = self.client.delete(self.url_details)

        self.assertEqual(response.status_code, 204)

    @patch_permissions
    def test_getting_meta_field(self, _):
        """Used to test getting tag most important technical information."""
        response = self.client.get(self.url_details)

        data = response.json().get("meta")
        self.assertIsNotNone(data)
        self.assertEqual(data.get("target_id"), str(self.example_tag.target_object))
        self.assertEqual(data.get("target_type"), self.example_tag.target_object_type)
        self.assertEqual(data.get("owner_id"), str(self.example_tag.owner_object))
        self.assertEqual(data.get("owner_type"), self.example_tag.target_object_type)

    @patch_permissions
    def test_retreive_inactive_tag(self, _):
        """Used to test getting a tag given its key."""
        self.client.delete(self.url_details)
        response = self.client.get(self.url_details)

        self.assertEqual(response.data.get("key").replace("-", ""), self.key)
        self.assertEqual(response.data.get("status"), "INACTIVE")

    @patch_permissions
    def test_get_inactive_tag_with_filter(self, _):
        """Used to test getting a tag given its key."""
        query_params = {
            "key": self.key,
        }

        self.client.delete(self.url_details)
        response = self.client.get(self.url, query_params)

        data = response.json().get("results")[0]
        self.assertEqual(data.get("status"), "INACTIVE")
        self.assertEqual(data.get("key").replace("-", ""), self.key)

    @patch_permissions
    def test_listing_inactive_tags(self, _):
        """Used to test adding inactive tags to the list of tags."""
        query_params = {
            "include_inactive": "true"
        }

        self.client.delete(self.url_details)  # To deactivate the tag
        response_include_inactive = self.client.get(self.url, query_params)

        include_inactive = [tag.get("key") for tag in response_include_inactive.json().get("results")]
        serialized_tag = TagSerializer(self.example_tag).data
        self.assertIn(serialized_tag.get("key"), include_inactive)

    @patch_permissions
    def test_listing_just_active_tags(self, _):
        """Used to test getting just active tags using as the only inactive tag the tag in url_details."""
        self.client.delete(self.url_details)  # To deactivate the tag
        response_exclude_inactive = self.client.get(self.url)

        exclude_inactive = [tag.get("key") for tag in response_exclude_inactive.json().get("results")]
        serialized_tag = TagSerializer(self.example_tag).data
        self.assertNotIn(serialized_tag.get("key"), exclude_inactive)
