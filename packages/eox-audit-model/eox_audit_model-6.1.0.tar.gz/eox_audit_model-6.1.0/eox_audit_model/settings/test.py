"""
Test Django settings for eox_audit_model project.
"""

from __future__ import unicode_literals

import codecs
import os

import yaml

from .common import *  # pylint: disable=wildcard-import

ALLOWED_HOSTS = ['*']

INSTALLED_APPS = [
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sites',
    'eox_audit_model.apps.EoxAuditModelConfig',
]

TIME_ZONE = 'UTC'

# This key needs to be defined so that the check_apps_ready passes and the
# AppRegistry is loaded
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': 'db.sqlite3',
    }
}

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}

ALLOW_EOX_AUDIT_MODEL = True
CELERY_TASK_ALWAYS_EAGER = False


def plugin_settings(settings):  # pylint: disable=function-redefined
    """
    Defines eox-core settings when app is used as a plugin to edx-platform.
    See: https://github.com/edx/edx-platform/blob/master/openedx/core/djangoapps/plugins/README.rst
    """
    # setup the databases used in the tutor local environment
    lms_cfg = os.environ.get('LMS_CFG')
    if lms_cfg:
        with codecs.open(lms_cfg, encoding='utf-8') as file:
            env_tokens = yaml.safe_load(file)
        settings.DATABASES = env_tokens['DATABASES']
