import os

if os.environ.get('PRODUCTION', '0') == '1':
    from .production_settings import *
else:
    from .development_settings import *

SECRET_KEY = config['security']['SECRET_KEY']

# Message queue
QUEUE_CLIENT = config['queue']['CLIENT']
QUEUE_CLIENT_API_HOST = config['queue']['HOST']
QUEUE_NAME = config['queue']['NAME']

# Gitlab
GITLAB_HOST = "https://gitlab.xerac.syfract.com"
GITLAB_ADMIN_USERNAME = 'root'
GITLAB_ADMIN_PASSWORD_FILE = 'configs/gitlab-admin-password.txt'

# Docker Registry
DOCKER_REGISTRY_HOST = "gitlab.xerac.syfract.com:5050"
DOCKER_REGISTRY_USERNAME = 'root'
DOCKER_REGISTRY_PASSWORD_FILE = 'configs/gitlab-admin-password.txt'

# Paths
PROBLEM_CONFIG_PATH = config['path']['PROBLEM_CONFIG']
