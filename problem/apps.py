from kubernetes import client, config

from django.apps import AppConfig
from django.utils.module_loading import import_string


class ProblemConfig(AppConfig):
    name = 'problem'
    queue = None

    @property
    def kubernetes(self):
        # Initialize a kubernetes client each time this property is used because the library deletes the SSL files after some time
        config.load_kube_config()
        return client.CustomObjectsApi()

    def ready(self):
        from django.conf import settings

        # Initialize message queue client and assign it to app object
        self.queue = import_string(settings.QUEUE_CLIENT)(settings.QUEUE_SERVER_API_URL)
