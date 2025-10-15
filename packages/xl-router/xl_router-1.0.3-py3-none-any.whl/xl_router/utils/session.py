from xl_router.utils import memory
from flask import request


class Session(object):
    """用户登录会话"""

    def __init__(self):
        token = request.headers.get('token')
        if self.is_test_token(token):
            return
        m = memory.get_instance()
        if token:
            key = f'access_token_{token}'
            try:
                self.data = m.get(key)
            except TypeError:
                self.data = {}
            self.key = key
        else:
            self.key = None
            self.data = {}

    def is_test_token(self, token):
        if token == '999999':
            self.key = ''
            self.data = {
                'id': 999999,
                'username': 'test'
            }
            return True
        else:
            return False

    @property
    def is_mobile(self):
        user_agent = request.user_agent.string.lower()
        if 'windows' in user_agent:
            return False
        if 'mac os' in user_agent and 'iphone' not in user_agent:
            return False
        return True

    @property
    def is_authorized(self):
        return bool(self.token)

    @property
    def token(self):
        return self.data.get('token')

    @property
    def user_id(self):
        return self.data.get('id')

    @property
    def username(self):
        return self.data.get('username')
    
    # def set_token(token, user_info=None):
    #     memory = get_instance()
    #     token_key = f'access_token_{token}'
    #     memory.set(token_key, user_info, seconds=TOKEN_EXPIRATION_SECONDS)

    def refresh_token(self):
        m = memory.get_instance()
        if self.key:
            m.expire(self.key, 1800)
