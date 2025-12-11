import json

from config import PATH_TO_JSON_THUMBPRINTS


def get_users():
    with open(PATH_TO_JSON_THUMBPRINTS, 'r', encoding='utf-8') as f:
        users = json.loads(f.read())
        return users
