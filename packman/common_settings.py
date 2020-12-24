from os import environ
from pathlib import Path
from vyper import v

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = Path(__file__).resolve(strict=True).parent.parent

SECRET_KEY = 'a'

ALLOWED_HOSTS = ['*']

# Application definition
INSTALLED_APPS = [
    'django.contrib.auth',
    'django.contrib.contenttypes',

    'taggit',

    'account',
    'code_metadata',
    'dataset',
    'problem',
    'competition',
]

AUTH_USER_MODEL = 'account.User'

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_L10N = True
USE_TZ = True

TAGGIT_CASE_INSENSITIVE = True

if 'CONFIG_DIR' in environ:
    v.add_config_path(environ['CONFIG_DIR'])
v.add_config_path('configs')
v.add_config_path('/configs')
v.watch_config()

v.automatic_env()
v.set_env_prefix('roboepics')
