"""
Integration tests.

This suite performs multiple http requests to guarantee
that the eox-tagging rest API is behaving as expected on a live server.
"""
import json
from os import environ
from unittest import skipUnless

import requests
from django.test import SimpleTestCase
from django.urls import reverse
from rest_framework import status


@skipUnless(environ.get("TEST_INTEGRATION"), "integration")
class TagTestCase(SimpleTestCase):  # pragma: no cover
    """Test suite."""

    @classmethod
    def setUpClass(cls):
        """Initialize data fixtures."""
        cls.data = json.loads(environ.get("TEST_DATA"))
        base_url = cls.data["base_url"]
        endpoint = reverse("tag-list")

        cls.url = f"{base_url}/eox-tagging{endpoint}"
        cls.session = requests.Session()
        cls.session.headers.update(
            {
                "Authorization": f"Bearer {cls.data['access_token']}",
            }
        )

        cls.tags_data = [
            {
                "tag_type": "test_user_tag",
                "tag_value": "test_user_tag",
                "target_type": "user",
                "target_id": cls.data["username"],
                "access": "PUBLIC",
                "owner_type": "site",
            },
            {
                "tag_type": "test_course_tag",
                "tag_value": "test_course_tag",
                "target_type": "courseoverview",
                "target_id": cls.data["course_id"],
                "access": "PUBLIC",
                "owner_type": "site",
            },
            {
                "tag_type": "test_enrollment_tag",
                "tag_value": "test_enrollment_tag",
                "target_type": "courseenrollment",
                "target_id": f"{cls.data['username']}: {cls.data['course_id']}",
                "access": "PUBLIC",
                "owner_type": "site",
            },
        ]

        cls.tear_down_tags_ids = []
        cls.delete_test_tag_id = create_tag(cls.session, cls.url, cls.tags_data[0])
        cls.read_test_tag_id = create_tag(cls.session, cls.url, cls.tags_data[0])
        cls.tear_down_tags_ids.append(cls.read_test_tag_id)

    @classmethod
    def tearDownClass(cls):
        """Deactive tags created by tests."""
        for tag_id in cls.tear_down_tags_ids:
            delete_tag(cls.session, cls.url, tag_id)

    def test_read_list_tag(self):
        """Test the tag list view."""
        response = self.session.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("count", response.json())

    def test_read_detail_tag(self):
        """Test the tag detail view."""
        tag_id = self.read_test_tag_id
        url = f"{self.url}{tag_id}/"
        expected_response = {
            "key": tag_id,
            "tag_value": self.tags_data[0]["tag_value"],
            "tag_type": self.tags_data[0]["tag_type"],
            "access": "PUBLIC",
            "activation_date": None,
            "expiration_date": None,
            "status": "ACTIVE",
        }

        response = self.session.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response = response.json()
        for key, value in expected_response.items():
            self.assertIn(key, response)
            self.assertEqual(response[key], value)

    def test_create_tag_user(self):
        """Test tag creation for target=user."""
        response = self.session.post(self.url, self.tags_data[0])

        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.text)

        self.tear_down_tags_ids.append(response.json()["key"])

    def test_create_tag_course(self):
        """Test tag creation for target=course."""
        response = self.session.post(self.url, self.tags_data[1])

        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.text)

        self.tear_down_tags_ids.append(response.json()["key"])

    def test_create_tag_enrollment(self):
        """Test tag creation for target=enrollment."""
        response = self.session.post(self.url, self.tags_data[2])

        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.text)

        self.tear_down_tags_ids.append(response.json()["key"])

    def test_create_tag_fail_validation(self):
        """Test creation denial due to validation."""
        data = self.tags_data[0].copy()
        data["access"] = "PRIVATE"

        response = self.session.post(self.url, data)

        self.assertEqual(
            response.status_code, status.HTTP_400_BAD_REQUEST, response.text
        )

    def test_delete_tag(self):
        """Test tag deletion."""
        tag_id = self.delete_test_tag_id
        url = f"{self.url}{tag_id}/"

        response = self.session.delete(url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)


def create_tag(session, url, tag_data):
    """Auxiliary function to create tags."""
    response = session.post(url, data=tag_data)
    response.raise_for_status()
    return response.json()["key"]


def delete_tag(session, url, tag_id):
    """Auxiliary function to delete tags."""
    url = f"{url}{tag_id}/"
    response = session.delete(url)
    response.raise_for_status()
