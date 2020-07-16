from kubernetes import client, config

from django.apps import AppConfig
from django.utils.module_loading import import_string


class ProblemConfig(AppConfig):
    name = 'problem'
    queue = None
    kubernetes = None

    def ready(self):
        from django.conf import settings

        # Initialize message queue client and assign it to app object
        self.queue = import_string(settings.QUEUE_CLIENT)(settings.QUEUE_SERVER_API_URL)

        # Initialize kubernetes client and assign it to app object
        config.load_kube_config()
        self.kubernetes = client.CustomObjectsApi()
