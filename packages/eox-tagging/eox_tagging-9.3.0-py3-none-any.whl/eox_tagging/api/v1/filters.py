"""Filter module for tags."""
import warnings  # NOTE: to be removed alongside the backport

from django_filters import compat  # NOTE: to be removed alongside the backport
from django_filters import rest_framework as filters

from eox_tagging.constants import AccessLevel
from eox_tagging.models import Tag

FILTER_TARGET_MAPPING = {
    "course_id": {
        "object": "courseoverview",
    },
    "username": {
        "object": "user",
    },
    "certificate_verify_uuid": {
        "object": "generatedcertificate",
        "target_id": "verify_uuid",
    }
}


class TagFilter(filters.FilterSet):
    """Filter class for tags."""

    course_id = filters.CharFilter(method="filter_by_target_object")
    username = filters.CharFilter(method="filter_by_target_object")
    certificate_verify_uuid = filters.CharFilter(method="filter_by_target_object")
    target_type = filters.CharFilter(method="filter_target_types")
    created_at = filters.DateTimeFromToRangeFilter()
    activation_date = filters.DateTimeFromToRangeFilter()
    expiration_date = filters.DateTimeFromToRangeFilter()
    access = filters.CharFilter(method="filter_access_type")

    class Meta:
        """Meta class."""
        model = Tag
        fields = ["key", "status", "tag_type", "tag_value"]

    def filter_by_target_object(self, queryset, name, value):
        """Filter that returns the tags associated with target."""
        if value:

            filter_target = FILTER_TARGET_MAPPING.get(name)
            target_id_name = filter_target.get("target_id")
            name = target_id_name if target_id_name else name

            filter_params = {
                "target_type": filter_target.get("object"),
                "target_id": {
                    name: value,
                },
            }

            try:
                queryset = queryset.find_all_tags_for(
                    **filter_params
                )
            except Exception:  # pylint: disable=broad-except
                return queryset.none()

        return queryset

    def filter_target_types(self, queryset, name, value):  # pylint: disable=unused-argument
        """
        Filter that returns targets using their type.

        **SPECIAL CASE**: course enrollments/generated certificate.

        If the user wants to filter by target_type courseenrollment/generatedcertificate and wants to add filters on
        user or course, it must pass the following:

            - target_type: if the other arguments are passed this is used to differentiate between
            course_id from courseoverview and username from user object.
            Case Course Enrollment
            - enrollment_course_id (optional)
            - enrollment_username (optional)
            Case Generated Certificate
            - certificate_course_id (optional)
            - certificate_username (optional)
        """
        target_id = {}
        username = None
        course_id = None

        if value == "courseenrollment":
            course_id = self.request.query_params.get("enrollment_course_id")
            username = self.request.query_params.get("enrollment_username")

        elif value == "generatedcertificate":
            course_id = self.request.query_params.get("certificate_course_id")
            username = self.request.query_params.get("certificate_username")

        target_id.update({"username": username, "course_id": course_id})

        try:
            if any(object_id for object_id in target_id.values()):
                queryset = queryset.find_all_tags_for(target_type=value, target_id=target_id)
            elif value:
                queryset = queryset.find_all_tags_by_type(value)
        except Exception:  # pylint: disable=broad-except
            return queryset.none()

        return queryset

    def filter_access_type(self, queryset, name, value):  # pylint: disable=unused-argument
        """Filters targets by their access type."""
        if value:
            value_map = {v.lower(): k for k, v in AccessLevel.choices()}
            access = value_map.get(value.lower())
            queryset = queryset.filter(access=access) if access else queryset.none()

        return queryset


class FilterBackend(filters.DjangoFilterBackend):
    """
    Backport this fix (https://github.com/carltongibson/django-filter/pull/1323)
    for range type filters.
    The current version of django-filter on edx-platform (v2.2.0) presents a bug
    were range filters don't produce the correct OpenAPI schema. This schema is
    used by our documentation tools (drf-yasg). This backport should be dropped
    when a new version of django-filter with the fix is released (probably v2.5.0)
    """

    def get_schema_fields(self, view):  # pylint: disable=missing-function-docstring
        # This is not compatible with widgets where the query param differs from the
        # filter's attribute name. Notably, this includes `MultiWidget`, where query
        # params will be of the format `<name>_0`, `<name>_1`, etc...
        assert compat.coreapi is not None, 'coreapi must be installed to use `get_schema_fields()`'  # pylint: disable=no-member
        assert compat.coreschema is not None, 'coreschema must be installed to use `get_schema_fields()`'  # pylint: disable=no-member
        try:
            queryset = view.get_queryset()
        except Exception:  # pylint: disable=broad-except
            queryset = None
            warnings.warn(
                f"{view.__class__} is not compatible with schema generation"
            )

        filterset_class = self.get_filterset_class(view, queryset)
        if not filterset_class:
            return []

        return [self.build_coreapi_field(schema_field_name, field)
                for field_name, field in filterset_class.base_filters.items()
                for schema_field_name in self.get_schema_field_names(field_name, field)
                ]

    def build_coreapi_field(self, name, field):  # pylint: disable=missing-function-docstring
        return compat.coreapi.Field(  # pylint: disable=no-member
            name=name,
            required=field.extra['required'],
            location='query',
            schema=self.get_coreschema_field(field),  # pylint: disable=no-member
        )

    def get_schema_field_names(self, field_name, field):
        """
        Get the corresponding schema field names required to generate the openAPI schema
        by referencing the widget suffixes if available.
        """
        try:
            suffixes = field.field_class.widget.suffixes
        except AttributeError:
            return [field_name]
        else:
            return [field_name] if not suffixes else [
                f'{field_name}_{suffix}'
                for suffix in suffixes if suffix
            ]
