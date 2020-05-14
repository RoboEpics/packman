from .common_settings import *

config.read(os.environ.get('CONFIG_FILE', '').strip() or os.path.join(BASE_DIR, 'configs', 'development.cfg'))
DJANGO_HOST = "development"

DEBUG = True

ALLOWED_HOSTS = ['*']

EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.environ.get('DATABASE_NAME', '').strip() or config.get('database', 'NAME', fallback=None) or 'db.sqlite3',
    }
}

STATIC_ROOT = 'static'
