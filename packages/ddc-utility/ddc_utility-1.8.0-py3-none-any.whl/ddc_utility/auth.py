import requests
import time

class OAuth2BearerHandler(requests.auth.AuthBase):
    """OAuth 2.0 Bearer Token authentication handler"""

    def __init__(self, bearer_token: str, expires_at=None):
        self.bearer_token = bearer_token
        self.expires_at = expires_at

    def __call__(self, request: requests.Request):
        request.headers['Authorization'] = 'Bearer ' + self.bearer_token
        return request

    def is_expired(self) -> bool:
        now = round(time.time())
        return self.expires_at - now < 60
    