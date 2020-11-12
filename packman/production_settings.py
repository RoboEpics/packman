from .common_settings import *

v.set_config_name('production')
v.read_in_config()

v.set_default('database.default.engine', 'django.db.backends.postgresql')
v.set_default('database.default.name', 'roboepics')
v.set_default('database.default.user', 'roboepics')

v.set_default('gitlab.config_path', '/root/.gitlab/config.conf')

v.set_default('log.level', 'INFO')
