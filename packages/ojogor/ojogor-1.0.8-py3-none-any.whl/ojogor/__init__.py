from .app import starexx
from .globals import request, session, g, current_app
from .helpers import url_for, abort, redirect, jsonify, render_template_string
from .routing import Router, Rule
from .request import Request
from .response import Response
from .config import Config
from .exceptions import HTTPException, BadRequest, NotFound, InternalServerError
from .middleware import Middleware
from .templating import TemplateEngine
from .signals import signals, request_started, request_finished, got_request_exception
from .sessions import SessionInterface, SecureCookieSession, Session

__version__ = "1.0.8"
__author__ = "Starexx"
__license__ = "MIT"

def create_app(import_name, **kwargs):
    app = starexx(import_name, **kwargs)
    return app

def __getattr__(name):
    if name == '__version__':
        return __version__
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")