"""
Common Django settings for eox_tagging project.

For more information on this file, see
https://docs.djangoproject.com/en/1.11/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.11/ref/settings/
"""
from __future__ import unicode_literals

from importlib.util import find_spec

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.11/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'secret-key'


# Application definition

INSTALLED_APPS = [
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'rest_framework',
    'eox_tagging',
]

EOX_AUDIT_MODEL_APP = 'eox_audit_model.apps.EoxAuditModelConfig'

ROOT_URLCONF = 'eox_tagging.urls'

# Internationalization
# https://docs.djangoproject.com/en/1.11/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_TZ = True

ALLOWED_HOSTS = ['*']

# Define AutoField to generate primary keys
# https://docs.djangoproject.com/en/3.2/releases/3.2/#customizing-type-of-auto-created-primary-keys
DEFAULT_AUTO_FIELD = 'django.db.models.AutoField'


def plugin_settings(settings):
    """
    Set of plugin settings used by the Open Edx platform.
    More info: https://github.com/openedx/edx-platform/blob/master/openedx/core/djangoapps/plugins/README.rst
    """
    # Plugin settings
    settings.EOX_TAGGING_GET_ENROLLMENT_OBJECT = "eox_tagging.edxapp_wrappers.backends.enrollment_l_v1"
    settings.EOX_TAGGING_GET_COURSE_OVERVIEW = "eox_tagging.edxapp_wrappers.backends.course_overview_i_v1"
    settings.EOX_TAGGING_DEFINITIONS = []
    settings.EOX_TAGGING_LOAD_PERMISSIONS = True
    settings.DATA_API_DEF_PAGE_SIZE = 1000
    settings.DATA_API_MAX_PAGE_SIZE = 5000
    settings.EOX_TAGGING_BEARER_AUTHENTICATION = 'eox_tagging.edxapp_wrappers.backends.bearer_authentication_i_v1'
    if hasattr(settings, 'INSTALLED_APPS'):
        if find_spec('eox_audit_model') and EOX_AUDIT_MODEL_APP not in settings.INSTALLED_APPS:
            settings.INSTALLED_APPS.append(EOX_AUDIT_MODEL_APP)
