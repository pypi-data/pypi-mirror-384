import typing as t
import gzip
import json
from io import BytesIO

class Middleware:
    __slots__ = ()

    def process_request(self, request):
        return None

    def process_response(self, request, response):
        return response

    def process_exception(self, request, exception):
        return None

class SessionMiddleware(Middleware):
    __slots__ = ('session_cookie_name', 'session_cookie_domain', 'session_cookie_path', 'session_cookie_httponly', 'session_cookie_secure', 'session_cookie_samesite')

    def __init__(self, session_cookie_name='session', session_cookie_domain=None, session_cookie_path=None, session_cookie_httponly=True, session_cookie_secure=False, session_cookie_samesite=None):
        self.session_cookie_name = session_cookie_name
        self.session_cookie_domain = session_cookie_domain
        self.session_cookie_path = session_cookie_path
        self.session_cookie_httponly = session_cookie_httponly
        self.session_cookie_secure = session_cookie_secure
        self.session_cookie_samesite = session_cookie_samesite

    def process_request(self, request):
        from .sessions import SecureCookieSession
        session_cookie = request.cookies.get(self.session_cookie_name)
        if session_cookie:
            try:
                request.session = SecureCookieSession.decode(session_cookie)
            except Exception:
                request.session = SecureCookieSession()
        else:
            request.session = SecureCookieSession()
        return None

    def process_response(self, request, response):
        if hasattr(request, 'session') and request.session:
            session_data = request.session.encode()
            response.set_cookie(
                self.session_cookie_name,
                session_data,
                domain=self.session_cookie_domain,
                path=self.session_cookie_path,
                httponly=self.session_cookie_httponly,
                secure=self.session_cookie_secure,
                samesite=self.session_cookie_samesite
            )
        return response

class CORSMiddleware(Middleware):
    __slots__ = ('origins', 'methods', 'headers', 'credentials')

    def __init__(self, origins='*', methods=None, headers=None, credentials=False):
        self.origins = origins
        self.methods = methods or ['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'OPTIONS']
        self.headers = headers or ['Content-Type', 'Authorization']
        self.credentials = credentials

    def process_request(self, request):
        if request.method == 'OPTIONS':
            from .response import Response
            response = Response()
            self._set_cors_headers(response)
            return response
        return None

    def process_response(self, request, response):
        self._set_cors_headers(response)
        return response

    def _set_cors_headers(self, response):
        response.headers['Access-Control-Allow-Origin'] = self.origins
        response.headers['Access-Control-Allow-Methods'] = ', '.join(self.methods)
        response.headers['Access-Control-Allow-Headers'] = ', '.join(self.headers)
        if self.credentials:
            response.headers['Access-Control-Allow-Credentials'] = 'true'

class CompressionMiddleware(Middleware):
    __slots__ = ('min_size', 'content_types')

    def __init__(self, min_size=500, content_types=None):
        self.min_size = min_size
        self.content_types = content_types or [
            'text/plain', 'text/html', 'text/css', 'application/javascript',
            'application/json', 'application/xml'
        ]

    def process_response(self, request, response):
        accept_encoding = request.headers.get('Accept-Encoding', '')
        content_type = response.headers.get('Content-Type', '').split(';')[0]
        
        if ('gzip' not in accept_encoding or 
            len(response.data) < self.min_size or
            content_type not in self.content_types):
            return response

        compressed_data = gzip.compress(response.data)
        response.data = compressed_data
        response.headers['Content-Encoding'] = 'gzip'
        response.headers['Content-Length'] = str(len(compressed_data))
        
        return response

class LoggingMiddleware(Middleware):
    __slots__ = ()

    def process_request(self, request):
        print(f"[{request.method}] {request.path} - {request.remote_addr}")
        return None

    def process_response(self, request, response):
        print(f"[{response.status_code}] {request.path}")
        return response

    def process_exception(self, request, exception):
        print(f"[EXCEPTION] {request.path}: {exception}")
        return None