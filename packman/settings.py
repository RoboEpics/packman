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
DATASET_FILLER_QUEUE_NAME = v.get('queue.dataset_filler_queue_name')
SUBMISSION_BUILDER_QUEUE_NAME = v.get('queue.submission_builder_queue_name')

# Docker Registry
DOCKER_REGISTRY_HOST = v.get('registry.host')

# Logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'default': {'format': '%(asctime)s - %(name)s (%(levelname)s): %(message)s', 'datefmt': '%Y-%m-%d %H:%M:%S'}
    },
    'handlers': {
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'default',
            'stream': 'ext://sys.stdout'
        },
    },
    'root': {
        'level': v.get('log.level').upper(),
        'handlers': ['console']
    }
}
