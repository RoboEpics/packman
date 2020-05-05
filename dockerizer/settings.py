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

PROBLEM_CONFIG_PATH = config['path']['PROBLEM_CONFIG']
