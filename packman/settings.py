import os

import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration

from gitlab import Gitlab

if os.environ.get('PRODUCTION', None) == '1':
    from .production_settings import *
else:
    from .development_settings import *

# Sentry
sentry_sdk.init(
    dsn=v.get('sentry.packman_dsn'),
    integrations=[DjangoIntegration()],
    send_default_pii=True
)

# Database
DATABASES = {
    'default': {
        'ENGINE': v.get('database.default.engine'),
        'HOST': v.get('database.default.host'),
        'PORT': v.get('database.default.port'),
        'NAME': v.get('database.default.name'),
        'USER': v.get('database.default.user'),
        'PASSWORD': v.get('database.default.password')
    }
}

# Hub
HUB_NAMESPACE = v.get('hub.namespace')

# Gitlab
GITLAB_ENABLED = v.get('gitlab.enabled')
GITLAB_ID = v.get('gitlab.id')
GITLAB_CONFIG_PATH = v.get('gitlab.config_path')
GITLAB_CLIENT = Gitlab.from_config(gitlab_id=GITLAB_ID, config_files=[GITLAB_CONFIG_PATH])
GITLAB_URL = GITLAB_CLIENT._base_url

GIT_HOST = v.get('git.host')
GIT_ADMIN_NAME = v.get('git.admin_name')
GIT_ADMIN_EMAIL = v.get('git.admin_email')
GIT_ADMIN_TOKEN = v.get('git.admin_token')
GIT_URL = f"https://oauth2:{GIT_ADMIN_TOKEN}@{GIT_HOST}"

# Message Queue
QUEUE_CLIENT = v.get('queue.client')
QUEUE_SERVER_HOST = v.get('queue.host')
QUEUE_SERVER_USERNAME = v.get('queue.username')
QUEUE_SERVER_PASSWORD = v.get('queue.password')
QUEUE_SERVER_API_URL = f"amqp://{'%s:%s@' % (QUEUE_SERVER_USERNAME, QUEUE_SERVER_PASSWORD) if QUEUE_SERVER_USERNAME else ''}{QUEUE_SERVER_HOST}"
SUBMISSION_BUILDER_QUEUE_NAME = v.get('queue.submission_builder_queue_name')
ROOM_QUEUE_NAME_PREFIX = v.get('queue.room_queue_name_prefix')

# S3
S3_ACCESS_KEY_ID = v.get('s3.access_key_id')
S3_SECRET_ACCESS_KEY = v.get('s3.secret_access_key')
S3_ENDPOINT_URL = v.get('s3.endpoint_url')
S3_RESULT_BUCKET_NAME = v.get('s3.result_bucket_name')

# Docker Registry
DOCKER_REGISTRY_HOST = v.get('registry.host')
RESULT_ONLY_IMAGE_PATH = v.get('registry.result_only_image_path')

# Logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'default': {'format': '%(asctime)s - %(name)s (%(levelname)s): %(message)s', 'datefmt': '%Y-%m-%d %H:%M:%S'}
    },
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'default',
            'stream': 'ext://sys.stdout'
        },
    },
    'loggers': {
        'pika': {
            'level': 'INFO'
        },
        'urllib3': {
            'level': 'INFO'
        }
    },
    'root': {
        'level': v.get('log.level').upper(),
        'handlers': ['console']
    }
}
