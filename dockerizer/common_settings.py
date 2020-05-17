import os
import configparser

import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

config = configparser.ConfigParser(allow_no_value=True)

ALLOWED_HOSTS = ['localhost', '127.0.0.1']

# Application definition
INSTALLED_APPS = [
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.messages',
    'django.contrib.sites',

    'taggit',

    'authorization',
    'dataset',
    'problem'
]

AUTH_USER_MODEL = 'authorization.User'

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_L10N = True
USE_TZ = True

sentry_sdk.init(
    dsn="https://96f82fff5cfa468cabc7c63e52a99b51@o294289.ingest.sentry.io/5243511",
    integrations=[DjangoIntegration()],
)
