import typing as t
import json
import warnings
from io import BytesIO
from urllib.parse import parse_qs, urlparse
from http import cookies as http_cookies

from .exceptions import BadRequest

class Request:
    __slots__ = (
        'environ', 'method', 'path', 'query_string', 'content_type',
        'content_length', 'stream', 'form', 'files', 'json', 'args',
        'cookies', 'headers', 'data', 'endpoint', 'view_args', 'url_rule',
        'routing_exception', '_parsed_content_type'
    )

    def __init__(self, environ):
        self.environ = environ
        self.method = environ.get('REQUEST_METHOD', 'GET').upper()
        self.path = environ.get('PATH_INFO', '/')
        self.query_string = environ.get('QUERY_STRING', '')
        self.content_type = environ.get('CONTENT_TYPE', '')
        self.content_length = self._get_content_length()
        self.stream = self._get_stream()
        self.form = None
        self.files = None
        self.json = None
        self.args = self._parse_query_string()
        self.cookies = self._parse_cookies()
        self.headers = self._parse_headers()
        self.data = None
        self.endpoint = None
        self.view_args = None
        self.url_rule = None
        self.routing_exception = None
        self._parsed_content_type = None

    def _get_content_length(self):
        try:
            return int(self.environ.get('CONTENT_LENGTH', 0))
        except (ValueError, TypeError):
            return 0

    def _get_stream(self):
        return self.environ['wsgi.input']

    def _parse_query_string(self):
        return parse_qs(self.query_string, keep_blank_values=True)

    def _parse_cookies(self):
        cookie_header = self.environ.get('HTTP_COOKIE', '')
        cookie = http_cookies.SimpleCookie()
        cookie.load(cookie_header)
        return {k: v.value for k, v in cookie.items()}

    def _parse_headers(self):
        headers = {}
        for key, value in self.environ.items():
            if key.startswith('HTTP_'):
                header_name = key[5:].replace('_', '-').title()
                headers[header_name] = value
        return headers

    @property
    def url(self):
        return self._get_url()

    @property
    def base_url(self):
        return self._get_base_url()

    @property
    def host(self):
        return self.environ.get('HTTP_HOST')

    @property
    def host_url(self):
        return self._get_host_url()

    @property
    def remote_addr(self):
        return self.environ.get('REMOTE_ADDR')

    @property
    def user_agent(self):
        return self.headers.get('User-Agent')

    @property
    def is_secure(self):
        return self.environ.get('wsgi.url_scheme') == 'https'

    @property
    def is_json(self):
        mt = self.content_type
        return mt and (mt == 'application/json' or mt.startswith('application/') and mt.endswith('+json'))

    def _get_url(self):
        scheme = self.environ.get('wsgi.url_scheme', 'http')
        host = self.environ.get('HTTP_HOST')
        if host is None:
            host = self.environ.get('SERVER_NAME', 'localhost')
            port = self.environ.get('SERVER_PORT')
            if port and port not in ('80', '443'):
                host = f"{host}:{port}"
        return f"{scheme}://{host}{self.path}"

    def _get_base_url(self):
        return self._get_url().rsplit('?', 1)[0]

    def _get_host_url(self):
        scheme = self.environ.get('wsgi.url_scheme', 'http')
        host = self.environ.get('HTTP_HOST')
        if host is None:
            host = self.environ.get('SERVER_NAME', 'localhost')
            port = self.environ.get('SERVER_PORT')
            if port and port not in ('80', '443'):
                host = f"{host}:{port}"
        return f"{scheme}://{host}"

    def get_json(self, force=False, silent=False, cache=True):
        if cache and self.json is not None:
            return self.json

        if not (force or self.is_json):
            if not silent:
                raise BadRequest('Request is not JSON')
            return None

        data = self.get_data(cache=cache)
        try:
            if data:
                self.json = json.loads(data.decode('utf-8'))
            else:
                self.json = None
        except json.JSONDecodeError as e:
            if not silent:
                raise BadRequest(f'Failed to decode JSON: {e}')
            return None

        return self.json

    def get_data(self, cache=True, as_text=False, parse_form_data=False):
        if cache and self.data is not None:
            if as_text:
                return self.data.decode('utf-8')
            return self.data

        if parse_form_data:
            self._load_form_data()

        if self.content_length == 0:
            self.data = b''
        else:
            self.data = self.stream.read(self.content_length)

        if as_text:
            return self.data.decode('utf-8')
        return self.data

    def _load_form_data(self):
        if self.form is not None:
            return

        self.form = {}
        self.files = {}

        if self.content_type == 'application/x-www-form-urlencoded':
            data = self.get_data(cache=False, as_text=True)
            self.form = parse_qs(data, keep_blank_values=True)
        elif self.content_type.startswith('multipart/form-data'):
            self._parse_multipart_form_data()

    def _parse_multipart_form_data(self):
        pass

    def __getitem__(self, key):
        return self.args.get(key)

    def get(self, key, default=None, type=None):
        value = self.args.get(key, default)
        if value is default:
            return value
        if type is not None:
            try:
                return type(value[0] if isinstance(value, list) else value)
            except (ValueError, TypeError):
                return default
        return value

    def __contains__(self, key):
        return key in self.args

    def __iter__(self):
        return iter(self.args)

    def __len__(self):
        return len(self.args)

    def __repr__(self):
        return f"<Request '{self.method} {self.path}'>"