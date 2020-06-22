import os

import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration

if os.environ.get('PRODUCTION', '0') == '1':
    from .production_settings import *
else:
    from .development_settings import *

SECRET_KEY = config['security']['SECRET_KEY']

# Message queue
QUEUE_CLIENT = config['queue']['CLIENT']
QUEUE_CLIENT_API_HOST = config['queue']['HOST']
QUEUE_NAME = config['queue']['NAME']

# Git
GIT_HOST = config['git']['HOST']
GIT_ADMIN_TOKEN = config['git']['ADMIN_TOKEN']

# Docker Registry
DOCKER_REGISTRY_HOST = config['registry']['HOST']
DOCKER_REGISTRY_USERNAME = config['registry']['USERNAME']
DOCKER_REGISTRY_PASSWORD_FILE = config['registry']['PASSWORD_FILE']

# Paths
PROBLEM_CONFIG_PATH = config['path']['PROBLEM_CONFIG']

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
    'root': {
        'level': (os.environ.get('LOGLEVEL', None) or config.get('log', 'LEVEL', fallback=None) or ('DEBUG' if DEBUG else 'INFO')).upper(),
        'handlers': ['console']
    }
}

# Sentry
sentry_sdk.init(
    dsn=config['sentry']['DSN'],
    integrations=[DjangoIntegration()]
)
