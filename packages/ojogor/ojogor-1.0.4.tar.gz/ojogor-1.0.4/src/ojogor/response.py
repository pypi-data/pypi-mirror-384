import typing as t
import json
import datetime
from http import HTTPStatus
from urllib.parse import quote
from email.utils import formatdate

from .json import JSONEncoder

class Response:
    __slots__ = (
        'response', 'status', 'status_code', 'headers', 'mimetype',
        'content_type', 'direct_passthrough', '_on_close'
    )

    default_mimetype = 'text/html'
    json_provider = JSONEncoder

    def __init__(self, response=None, status=None, headers=None, mimetype=None,
                 content_type=None, direct_passthrough=False):
        
        if isinstance(response, (tuple, list)):
            response = ''.join(str(x) for x in response)

        self.response = response
        self.status = status
        self.status_code = status
        self.headers = headers or {}
        self.mimetype = mimetype
        self.content_type = content_type or mimetype
        self.direct_passthrough = direct_passthrough
        self._on_close = []

        if self.content_type is None:
            self.content_type = self.default_mimetype

        if self.status_code is None:
            self.status_code = 200

    def set_cookie(self, key, value='', max_age=None, expires=None, path='/',
                   domain=None, secure=False, httponly=False, samesite=None):
        
        self.headers.setdefault('Set-Cookie', [])
        cookie = f"{quote(key)}={quote(value)}"

        if path is not None:
            cookie += f"; Path={path}"
        if domain is not None:
            cookie += f"; Domain={domain}"
        if max_age is not None:
            cookie += f"; Max-Age={max_age}"
        if expires is not None:
            if isinstance(expires, datetime.datetime):
                expires = expires.timestamp()
            cookie += f"; Expires={formatdate(expires, usegmt=True)}"
        if secure:
            cookie += "; Secure"
        if httponly:
            cookie += "; HttpOnly"
        if samesite is not None:
            cookie += f"; SameSite={samesite}"

        self.headers['Set-Cookie'].append(cookie)

    def delete_cookie(self, key, path='/', domain=None, secure=False, 
                      httponly=False, samesite=None):
        self.set_cookie(key, expires=0, max_age=0, path=path, domain=domain,
                       secure=secure, httponly=httponly, samesite=samesite)

    def set_data(self, value):
        if isinstance(value, str):
            value = value.encode('utf-8')
        self.response = value

    def get_data(self, as_text=False):
        if as_text:
            return self.response.decode('utf-8') if self.response else ''
        return self.response or b''

    data = property(get_data, set_data)

    def json(self, data):
        self.response = self.json_provider.encode(data)
        self.content_type = 'application/json'
        return self

    def make_conditional(self, request):
        return self

    def __call__(self, environ, start_response):
        status = f"{self.status_code} {HTTPStatus(self.status_code).phrase}"
        headers = [(k, v) for k, v in self.headers.items() if k != 'Set-Cookie']
        
        for cookie in self.headers.get('Set-Cookie', []):
            headers.append(('Set-Cookie', cookie))

        headers.append(('Content-Type', self.content_type))

        start_response(status, headers)

        if self.response is None:
            return [b'']
        elif isinstance(self.response, bytes):
            return [self.response]
        elif isinstance(self.response, str):
            return [self.response.encode('utf-8')]
        else:
            return self.response

    def __repr__(self):
        return f"<Response {self.status_code} {self.content_type}>"

    @classmethod
    def force_type(cls, response, environ=None):
        if not isinstance(response, cls):
            response = cls(response)
        return response