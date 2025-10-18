from .request import Request
from .response import Response

class EnvironBuilder:
    def __init__(self, method='GET', path='/', headers=None, data=None, json=None):
        self.method = method
        self.path = path
        self.headers = headers or {}
        self.data = data
        self.json = json

    def get_environ(self):
        environ = {
            'REQUEST_METHOD': self.method,
            'PATH_INFO': self.path,
            'QUERY_STRING': '',
            'SERVER_NAME': 'localhost',
            'SERVER_PORT': '8000',
            'wsgi.version': (1, 0),
            'wsgi.url_scheme': 'http',
            'wsgi.input': None,
            'wsgi.errors': None,
            'wsgi.multithread': False,
            'wsgi.multiprocess': False,
            'wsgi.run_once': False,
        }
        return environ

class ResponseStream:
    def __init__(self):
        self._data = []

    def write(self, data):
        self._data.append(data)

    def get_data(self):
        return b''.join(self._data)