import unicodedata


def normalize_username(username):
    return unicodedata.normalize('NFKC', username) if isinstance(username, str) else username
