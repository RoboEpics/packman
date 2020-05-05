from .common_settings import *

config.read('%s/configs/production.cfg' % BASE_DIR)
DJANGO_HOST = "production"

SECRET_KEY = config['security']['SECRET_KEY']
DEBUG = True

ALLOWED_HOSTS += [l.strip() for l in open('configs/temporary-hosts.txt').readlines()]

ADMINS = [
    ('Ali Mirlou', 'alimirlou@gmail.com'),
    ('Ali Mirloo', 'alimirloohome2@gmail.com'),
]
MANAGERS = ADMINS
SERVER_EMAIL = 'log@cards.bio'  # FIXME change when correct domain is set

EMAIL_HOST = config['mail']['HOST']
EMAIL_PORT = config['mail']['PORT']
EMAIL_HOST_USER = config['mail']['USER']
EMAIL_HOST_PASSWORD = config['mail']['PASSWORD']
EMAIL_USE_TLS = True

DATABASES = {
    'default': {
        'ENGINE': config['postgresql']['ENGINE'],
        'NAME': config['postgresql']['NAME'],
        'USER': config['postgresql']['USER'],
        'PASSWORD': config['postgresql']['PASSWORD']
    }
}

GITLAB_HOST = "https://gitlab.xerac.syfract.com"
GITLAB_ADMIN_USERNAME = 'root'
GITLAB_ADMIN_PASSWORD_FILE = 'configs/gitlab-admin-password.txt'
DOCKER_REGISTRY_HOST = "gitlab.xerac.syfract.com:5050"
