import typing as t
from http import HTTPStatus

class HTTPException(Exception):
    __slots__ = ('code', 'name', 'description')

    def __init__(self, code=None, name=None, description=None):
        super().__init__()
        self.code = code or 500
        self.name = name or HTTPStatus(self.code).phrase
        self.description = description or HTTPStatus(self.code).description

    def get_response(self):
        from .response import Response
        return Response(f"{self.code} {self.name}: {self.description}", status=self.code)

    def __str__(self):
        return f"{self.code} {self.name}: {self.description}"

    def __repr__(self):
        return f"<{self.__class__.__name__} {self.code}>"

class BadRequest(HTTPException):
    def __init__(self, description=None):
        super().__init__(400, 'Bad Request', description)

class Unauthorized(HTTPException):
    def __init__(self, description=None):
        super().__init__(401, 'Unauthorized', description)

class Forbidden(HTTPException):
    def __init__(self, description=None):
        super().__init__(403, 'Forbidden', description)

class NotFound(HTTPException):
    def __init__(self, description=None):
        super().__init__(404, 'Not Found', description)

class MethodNotAllowed(HTTPException):
    def __init__(self, description=None):
        super().__init__(405, 'Method Not Allowed', description)

class InternalServerError(HTTPException):
    def __init__(self, description=None):
        super().__init__(500, 'Internal Server Error', description)

class ServiceUnavailable(HTTPException):
    def __init__(self, description=None):
        super().__init__(503, 'Service Unavailable', description)

class GatewayTimeout(HTTPException):
    def __init__(self, description=None):
        super().__init__(504, 'Gateway Timeout', description)

def abort(code, description=None):
    exception_classes = {
        400: BadRequest,
        401: Unauthorized,
        403: Forbidden,
        404: NotFound,
        405: MethodNotAllowed,
        500: InternalServerError,
        503: ServiceUnavailable,
        504: GatewayTimeout
    }
    
    exception_class = exception_classes.get(code, HTTPException)
    raise exception_class(description)