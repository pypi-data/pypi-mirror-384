from xl_memory import Memory
from flask import current_app


TOKEN_EXPIRATION_SECONDS = 1800


_memory_instance = None


def get_instance():
    global _memory_instance
    if _memory_instance is None:
        _memory_instance = Memory(current_app.REDIS_CONFIG)
    return _memory_instance


def get_cache():
    return Memory({**current_app.REDIS_CONFIG, 'db': 15})


def set_token(token, user_info=None):
    memory = get_instance()
    token_key = f'access_token_{token}'
    memory.set(token_key, user_info, seconds=TOKEN_EXPIRATION_SECONDS)


