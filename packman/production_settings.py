from gitlab import Gitlab

from .common_settings import *

config.read(os.environ.get('CONFIG_FILE', '').strip() or os.path.join(BASE_DIR, 'configs', 'production.cfg'))
DJANGO_HOST = "production"

ADMINS = [
    ('Ali Mirlou', 'alimirlou@gmail.com'),
    ('Ali Mirloo', 'alimirloohome2@gmail.com'),
]
MANAGERS = ADMINS

# Database
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

# Gitlab
GITLAB_ENABLED = True
GITLAB_ID = config['gitlab']['ID']
GITLAB_CONFIG_PATH = config.get('gitlab', 'CONFIG_PATH', fallback=None) or '/root/.gitlab/config.conf'
GITLAB_CLIENT = Gitlab.from_config(gitlab_id=GITLAB_ID, config_files=[GITLAB_CONFIG_PATH])
GITLAB_URL = GITLAB_CLIENT._base_url

# S3 storage
DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
AWS_ACCESS_KEY_ID = os.environ.get('S3_ACCESS_KEY', '') or config['s3']['ACCESS_KEY']
AWS_SECRET_ACCESS_KEY = os.environ.get('S3_SECRET_KEY', '') or config['s3']['SECRET_KEY']
AWS_S3_ENDPOINT_URL = os.environ.get('S3_HOST', '') or config['s3']['HOST']
AWS_STORAGE_BUCKET_NAME = os.environ.get('S3_BUCKET_NAME', '') or config['s3']['BUCKET_NAME']
AWS_DEFAULT_ACL = config.get('s3', 'DEFAULT_ACL', fallback=None)
AWS_S3_FILE_OVERWRITE = False
