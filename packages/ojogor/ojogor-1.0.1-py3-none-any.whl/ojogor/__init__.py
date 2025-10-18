from .app import starexx
from .globals import request, session, g, current_app, has_request_context, has_app_context
from .globals import url_for, abort, redirect, jsonify, render_template, send_file
from .globals import send_from_directory, make_response, flash, get_flashed_messages
from .routing import Router, Rule, Blueprint
from .request import Request
from .response import Response
from .config import Config
from .exceptions import HTTPException, BadRequest, Unauthorized, Forbidden, NotFound
from .exceptions import MethodNotAllowed, InternalServerError, ServiceUnavailable
from .middleware import Middleware, SessionMiddleware, CORSMiddleware, CompressionMiddleware
from .templating import TemplateEngine, TemplateContext, TemplateRenderer
from .signals import signals, request_started, request_finished, got_request_exception
from .signals import before_render_template, template_rendered
from .sessions import SessionInterface, SecureCookieSession, Session
from .testing import TestClient, TestCase, Client
from .cli import cli, AppGroup, with_appcontext, pass_script_info
from .json import JSONEncoder, JSONDecoder, json_provider
from .wrappers import EnvironBuilder, ResponseStream

__version__ = "1.0.0"
__author__ = "Starexx"
__license__ = "MIT"

__all__ = [
    'starexx', 'Request', 'Response', 'Config',
    'request', 'session', 'g', 'current_app',
    'has_request_context', 'has_app_context',
    'Router', 'Rule', 'Blueprint',
    'url_for', 'abort', 'redirect', 'jsonify',
    'render_template', 'send_file', 'send_from_directory',
    'make_response', 'flash', 'get_flashed_messages',
    'HTTPException', 'BadRequest', 'Unauthorized', 'Forbidden',
    'NotFound', 'MethodNotAllowed', 'InternalServerError',
    'ServiceUnavailable',
    'Middleware', 'SessionMiddleware', 'CORSMiddleware',
    'CompressionMiddleware',
    'TemplateEngine', 'TemplateContext', 'TemplateRenderer',
    'signals', 'request_started', 'request_finished',
    'got_request_exception', 'before_render_template',
    'template_rendered',
    'SessionInterface', 'SecureCookieSession', 'Session',
    'TestClient', 'TestCase', 'Client',
    'cli', 'AppGroup', 'with_appcontext', 'pass_script_info',
    'JSONEncoder', 'JSONDecoder', 'json_provider',
    'EnvironBuilder', 'ResponseStream'
]

def create_app(import_name, **kwargs):
    app = Mehta(import_name, **kwargs)
    return app

def __getattr__(name):
    if name == '__version__':
        return __version__
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")