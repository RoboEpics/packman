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

DATABASES = {
    'default': {
        'ENGINE': config['postgresql']['ENGINE'],
        'NAME': config['postgresql']['NAME'],
        'USER': config['postgresql']['USER'],
        'PASSWORD': config['postgresql']['PASSWORD']
    }
}
