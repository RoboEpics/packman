from .common_settings import *

config.read(os.environ.get('CONFIG_FILE', '').strip() or os.path.join(BASE_DIR, 'configs', 'production.cfg'))
DJANGO_HOST = "production"

ADMINS = [
    ('Ali Mirlou', 'alimirlou@gmail.com'),
    ('Ali Mirloo', 'alimirloohome2@gmail.com'),
]
MANAGERS = ADMINS

DATABASES = {
    'default': {
        'ENGINE': config.get('database', 'ENGINE', fallback=None) or 'django.db.backends.postgresql',
        'HOST': os.environ.get('DATABASE_HOST', '') or config.get('database', 'HOST', fallback=None),
        'PORT': os.environ.get('DATABASE_PORT', '') or config.get('database', 'PORT', fallback=None),
        'NAME': config.get('database', 'NAME', fallback=None) or 'roboepics',
        'USER': config.get('database', 'USER', fallback=None) or 'roboepics',
        'PASSWORD': os.environ.get('DATABASE_PASSWORD', '') or config['database']['PASSWORD']
    }
}
