"""
App configuration for eox_tagging.
"""
from __future__ import unicode_literals

from django.apps import AppConfig


class EoxTaggingConfig(AppConfig):
    """
    eox-tagging configuration.
    """
    name = 'eox_tagging'
    verbose_name = 'eduNEXT OpenedX Tagging'
    plugin_app = {
        'url_config': {
            'lms.djangoapp': {
                'namespace': 'eox-tagging',
                'regex': r'^eox-tagging/',
                'relative_path': 'urls',
            },
            'cms.djangoapp': {
                'namespace': 'eox-tagging',
                'regex': r'^eox-tagging/',
                'relative_path': 'urls',
            }
        },
        'settings_config': {
            'lms.djangoapp': {
                'common': {'relative_path': 'settings.common'},
                'test': {'relative_path': 'settings.test'},
                'production': {'relative_path': 'settings.production'},
            },
            'cms.djangoapp': {
                'common': {'relative_path': 'settings.common'},
                'test': {'relative_path': 'settings.test'},
                'production': {'relative_path': 'settings.production'},
            },
        }
    }
