"""
Viewset for Tags.
"""
from edx_api_doc_tools import query_parameter, schema_for
from edx_rest_framework_extensions.auth.jwt.authentication import JwtAuthentication
from rest_framework import status, viewsets
from rest_framework.authentication import SessionAuthentication

from eox_tagging.api.v1.filters import FilterBackend, TagFilter
from eox_tagging.api.v1.pagination import TagApiPagination
from eox_tagging.api.v1.permissions import EoxTaggingAPIPermission
from eox_tagging.api.v1.serializers import TagSerializer
from eox_tagging.edxapp_accessors import get_site
from eox_tagging.edxapp_wrappers.bearer_authentication import BearerAuthentication
from eox_tagging.models import Tag

try:
    from eox_audit_model.decorators import audit_method
except ImportError:
    def audit_method(*args, **kwargs):  # pylint: disable=unused-argument
        """Identity decorator"""
        return lambda x: x


@schema_for(
    "create",
    """
    Creates a tag for a given object
    There are three different types of objects that can be labeled with a tag: courses,\
    users and enrollments. The type of objects that can be labeled (and extra\
    validations for different fields) are defined in the configuration of the\
    site.

    **Example Request**

        POST /eox-tagging/api/v1/tags/
        {
            "tag_type": "subscription_level",
            "tag_value": "premium",
            "target_type": "courseoverview",
            "target_id": "course-v1:edX+DemoX+Demo_Course",
            "access": "PUBLIC",
            "owner_type": "site"
        }

    **Parameters**

    - `tag_type` (**required**, string, _body_):
    General category for the tag (i.e subscription_level). This value is set in\
    the site configuration.

    - `tag_value` (**required**, string, _body_):
    An item of the category (i.e premium). If there isn't a validation in the\
    site configuration it can take any string.

    - `target_type` (**required**, string, _body_):
    One of courseoverview, user, courseenrollment, generatedcertificate

    - `target_id` (**required**, string, _body_): Identifier of the target\
      object. For users, username; for courseoverview, course_id and for\
      courseenrollments/generatedcertificates a string with the following format: "`username:\
      course_id`. For generatedcertificates it can also be its verify_uuid"

    - `activation_date` (**optional**, string, _body_):
    DateTime format `YYYY-MM-DD HH:MM:SS`.

    - `expiration_date` (**optional**, string, _body_):
    DateTime format `YYYY-MM-DD HH:MM:SS`.

    - `owner_type` (**optional**, string, _body_):
    Owner of the tag, either `site` or `user`

    - `access` (**optional**, string, _body_):
    Visibility of the tag, either `PUBLIC`, `PRIVATE` or `PROTECTED`
    """,
)
@schema_for(
    "destroy",
    """
    Delete single tag by key. Deleted tags are inactivated (soft delete)
    """,
    responses={status.HTTP_404_NOT_FOUND: "Not found"},
)
@schema_for(
    "retrieve",
    """
    Fetch details for a single tag by key
    """,
    responses={status.HTTP_404_NOT_FOUND: "Not found"},
)
@schema_for(
    "list",
    """
    Fetch a list of tags.

    The list can be narrowed using the available filters.
    - Some filters are incompatible with each other,\
    namely `course_id`, `username` and `target_type`. The reason being that `course_id` and `username`\
    have an implicit `target_type` of `courseoverview` and `user`.
    - DateTime filters must have the following format `YY-MM-DD HH:MM:SS`. Time is optional, date is not.\
    Time must be UTC.
    - Parameters not defined bellow will be ignored. If you apply a filter with a typo you'll get the \
    whole list of tags.
    """,
    parameters=[
        query_parameter(
            "key",
            str,
            "The unique identifier. Same as `GET /eox-tagging/api/v1/tags/{key}`",
        ),
        query_parameter(
            "status", str, "Filter active or inactive tags. Default: active"
        ),
        query_parameter(
            "include_inactive", bool, "If true include the inactive tags on the list. Default false"
        ),
        query_parameter(
            "tag_type",
            str,
            "The type of the tag, set on the configuration of the site (i.e. Subscription level)",
        ),
        query_parameter("tag_value", str, "The value of the tag (i.e. Premium)"),
        query_parameter(
            "course_id",
            str,
            "Shortcut to filter objects of target_type `courseoverview` with id `course_id`.",
        ),
        query_parameter(
            "username",
            str,
            "Shortcut to filter objects of target_type `user` with id `username`.",
        ),
        query_parameter(
            "certificate_verify_uuid",
            str,
            "Shortcut to filter objects of target_type `generatedcertificate` with id `verify_uuid`.",
        ),
        query_parameter(
            "owner_type",
            str,
            "Shortcut to filter objects of owner_type `user` or `site`.",
        ),
        query_parameter(
            "target_type",
            str,
            "The type of the object that was tagged, one of: `course (use opaquekeyproxymodel for`"
            "course overview types), `courseenrollment`, `user`, `generatedcertificate`",
        ),
        query_parameter(
            "enrollment_username",
            str,
            "User identifier (username) to be used when target_type=courseenrollment. "
            "Can be omitted and is ignored for a different target_type",
        ),
        query_parameter(
            "enrollment_course_id",
            str,
            "Course identifier to be used when target_type=courseenrollment."
            "Can be omitted and is ignored for a different target_type",
        ),
        query_parameter(
            "certificate_username",
            str,
            "User identifier (username) to be used when target_type=generatedcertificate. "
            "Can be omitted and is ignored for a different target_type",
        ),
        query_parameter(
            "certificate_course_id",
            str,
            "Course identifier to be used when target_type=generatedcertificate."
            "Can be omitted and is ignored for a different target_type",
        ),
        query_parameter(
            "created_at_before",
            str,
            "Filter tags created before date. Format `YY-MM-DD HH:MM:SS`",
        ),
        query_parameter(
            "created_at_after",
            str,
            "Filter tags created after date. Format `YY-MM-DD HH:MM:SS`",
        ),
        query_parameter(
            "activation_date_before",
            str,
            "Filter tags created before date. Format `YY-MM-DD HH:MM:SS`",
        ),
        query_parameter(
            "activation_date_after",
            str,
            "Filter tags created after date. Format `YY-MM-DD HH:MM:SS`",
        ),
        query_parameter(
            "expiration_date_before",
            str,
            "Filter tags created before date. Format `YY-MM-DD HH:MM:SS`",
        ),
        query_parameter(
            "expiration_date_after",
            str,
            "Filter tags created after date. Format `YY-MM-DD HH:MM:SS`",
        ),
        query_parameter("access", str, "Filter by access, One of `PUBLIC`, `PRIVATE`, `PROTECTED`"),
    ],
    responses={status.HTTP_404_NOT_FOUND: "Not found"},
)
class TagViewSet(viewsets.ModelViewSet):
    """Viewset for listing and creating Tags."""

    serializer_class = TagSerializer
    authentication_classes = [BearerAuthentication, SessionAuthentication, JwtAuthentication,]
    permission_classes = (EoxTaggingAPIPermission,)
    pagination_class = TagApiPagination
    filter_backends = (FilterBackend,)
    filterset_class = TagFilter
    lookup_field = "key"
    http_method_names = ["get", "post", "delete", "head"]

    def get_queryset(self):
        """Restricts the returned tags."""
        queryset = Tag.objects.all()

        queryset = self.__get_objects_by_status(queryset)

        queryset = self.__get_objects_by_owner(queryset)

        return queryset

    def create(self, request, *args, **kwargs):
        """Hijack the create method and use a wrapper function to perform the
        audit process. The original parameters of create are not very useful in
        raw form, this way we pass more useful information to our wrapper
        function to be audited
        """

        @audit_method(action="eox_tagging-api-v1-viewset:tagviewset-create")
        def audited_create(body):  # pylint: disable=unused-argument
            return super(TagViewSet, self).create(request, *args, **kwargs)  # pylint: disable=super-with-arguments

        return audited_create(body=request.data)

    def destroy(self, request, *args, **kwargs):
        """Hijack the destroy method and use a wrapper function to perform the
        audit process. The original parameters of destroy are not very useful in
        raw form, this way we pass more useful information to our wrapper
        function to be audited
        """

        @audit_method(action="eox_tagging-api-v1-viewset:tagviewset-destroy")
        def audited_destroy(path):  # pylint: disable=unused-argument
            return super(TagViewSet, self).destroy(request, *args, **kwargs)  # pylint: disable=super-with-arguments

        return audited_destroy(path=request.path)

    def __get_objects_by_status(self, queryset):
        """Method that returns queryset filtered by tag status."""
        include_inactive = self.request.query_params.get("include_inactive")

        if "key" in self.request.query_params or self.action == "retrieve":
            include_inactive = "true"

        if not include_inactive or include_inactive.lower() not in ["true", "1"]:
            queryset = queryset.active()

        return queryset

    def __get_objects_by_owner(self, queryset):
        """Method that returns queryset filtered by tag owner"""
        owner_type = self.request.query_params.get("owner_type")
        owner_information = self.__get_request_owner(owner_type)

        try:
            queryset_union = queryset.none()
            for owner in owner_information:
                queryset_union |= queryset.find_by_owner(**owner)

            return queryset_union
        except Exception:  # pylint: disable=broad-except
            return queryset.none()

    def __get_request_owner(self, owner_type):
        """Returns the owners of the tag to filter the queryset."""
        site = self.__get_site()
        user = self.__get_user()

        if not owner_type:
            return [site, user]

        if owner_type.lower() == "user":
            return [user]

        if owner_type.lower() == "site":
            return [site]

        return []

    def __get_site(self):
        """Returns the current site."""
        site = get_site()

        return {
            "owner_id": {"id": site.id},
            "owner_type": "site",
        }

    def __get_user(self):
        """Returns the current user."""
        user = self.request.user

        return {
            "owner_id": {"username": user.username},
            "owner_type": "user",
        }
