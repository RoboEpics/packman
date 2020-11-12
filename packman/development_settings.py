from .common_settings import *

v.set_config_name('development')
v.read_in_config()

v.set_default('database.default.engine', 'django.db.backends.sqlite3')
v.set_default('database.default.name', 'db.sqlite3')

v.set_default('fusion.base_url', "http://localhost:9011")

v.set_default('gitlab.config_path', 'configs/gitlab.conf')

v.set_default('log.level', 'DEBUG')

DEBUG = True

EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

STATIC_ROOT = 'static'
MEDIA_URL = '/media/'
