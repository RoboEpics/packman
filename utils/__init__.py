from django.conf import settings
from django.utils.crypto import get_random_string
from django.utils.module_loading import import_string

__all__ = ['clients', 'random_path', 'empty_roles']


def random_path() -> str:
    return get_random_string(10)


def empty_roles() -> dict:
    return {"actor": {}, "director": []}


class ClientClass:
    queue_client = import_string(settings.QUEUE_CLIENT)(settings.QUEUE_SERVER_API_URL)


clients = ClientClass()
