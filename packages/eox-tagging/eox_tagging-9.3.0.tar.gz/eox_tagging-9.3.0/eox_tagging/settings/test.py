"""
Test Django settings for eox_tagging project.
"""
from __future__ import unicode_literals

import codecs
import os

import yaml

from .common import *  # pylint: disable=wildcard-import, unused-wildcard-import


class SettingsClass:
    """ dummy settings class """


SETTINGS = SettingsClass()
# This is executing the plugin_settings method imported from common module
plugin_settings(SETTINGS)
vars().update(SETTINGS.__dict__)
INSTALLED_APPS = vars().get("INSTALLED_APPS", [])
TEST_INSTALLED_APPS = [
    "django.contrib.sites",
]
for app in TEST_INSTALLED_APPS:
    if app not in INSTALLED_APPS:
        INSTALLED_APPS.append(app)

# For testing
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': 'db.sqlite3',
    },
}


def plugin_settings(settings):  # pylint: disable=function-redefined
    """
    Set of plugin settings used by the Open Edx platform.
    More info: https://github.com/openedx/edx-platform/blob/master/openedx/core/djangoapps/plugins/README.rst
    """
    settings.EOX_TAGGING_SKIP_VALIDATIONS = True
    settings.EOX_TAGGING_LOAD_PERMISSIONS = False
    settings.EOX_TAGGING_BEARER_AUTHENTICATION = 'eox_tagging.edxapp_wrappers.backends.bearer_authentication_i_v1_test'
    settings.DATA_API_DEF_PAGE_SIZE = 1000
    settings.DATA_API_MAX_PAGE_SIZE = 5000
    settings.EOX_CORE_CERTIFICATES_BACKEND = "eox_core.edxapp_wrapper.backends.certificates_h_v1_test"
    settings.EOX_TAGGING_GET_COURSE_OVERVIEW = "eox_tagging.edxapp_wrappers.backends.course_overview_i_v1_test"
    settings.EOX_TAGGING_GET_ENROLLMENT_OBJECT = "eox_tagging.edxapp_wrappers.backends.enrollment_l_v1_test"
    settings.TEST_SITE = 1

    # setup the databases used in the tutor local environment
    lms_cfg = os.environ.get('LMS_CFG')
    if lms_cfg:
        with codecs.open(lms_cfg, encoding='utf-8') as file:
            env_tokens = yaml.safe_load(file)
        settings.DATABASES = env_tokens['DATABASES']


SETTINGS = SettingsClass()
plugin_settings(SETTINGS)
vars().update(SETTINGS.__dict__)


# Integration test settings
INTEGRATION_TEST_SETTINGS = {
    # Retrieved from the Tutor environment where the integration tests run
    "EOX_TAGGING_BASE_URL": f"http://{os.environ.get('LMS_HOST', 'local.edly.io')}/eox-tagging",
    "API_TIMEOUT": 5,
}
