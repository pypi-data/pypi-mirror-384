"""
Swagger view generator
"""
from django.conf import settings
from django.urls import include, re_path, reverse
from drf_yasg.generators import OpenAPISchemaGenerator
from drf_yasg.openapi import SwaggerDict
from drf_yasg.views import get_schema_view
from edx_api_doc_tools import get_docs_cache_timeout, internal_utils, make_api_info
from rest_framework import permissions


class APISchemaGenerator(OpenAPISchemaGenerator):
    """
    Schema generator for eox-core.

    Define specific security definition using oauth without overwritting project wide
    settings.
    """

    def get_security_definitions(self):
        security_definitions = {
            "OAuth2": {
                "flow": "application",
                "tokenUrl": f"{settings.LMS_ROOT_URL}{reverse('access_token')}",
                "type": "oauth2",
            },
        }
        security_definitions = SwaggerDict.as_odict(security_definitions)
        return security_definitions


api_urls = [
    re_path(r"eox-tagging/api/", include("eox_tagging.api.urls"))
]

api_info = make_api_info(
    title="eox tagging",
    version="v1",
    email=" contact@edunext.co",
    description=internal_utils.dedent("""\
    **eox tagging REST API**

    eox-tagging is a small plugin that provides the ability to ‘tag’ or label\
    certain objects of the Open edX platform (Courses, Course Enrollments,\
    Users). The tag contains the object that is being tagged, its identifier, a\
    ‘tag_type’ indicating the set of values the tag can have and ‘tag_value’\
    which holds a value of type ‘tag_type’. Additionally one can provide extra\
    info such as: Access level, or timestamps for when the tag should be considered\
    active. \

    eox tagging is meant to be a lightweight plugin with emphasis on flexibility,\
    most of the logic regarding the deactivation of tags at a given time must be\
    handled separately.
    """),
)

docs_ui_view = get_schema_view(
    api_info,
    generator_class=APISchemaGenerator,
    public=True,
    permission_classes=[permissions.AllowAny],
    patterns=api_urls,
).with_ui("swagger", cache_timeout=get_docs_cache_timeout())
