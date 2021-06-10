from django.utils.crypto import get_random_string


def random_path() -> str:
    return get_random_string(10)
