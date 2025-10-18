import os
import sys
import inspect
import typing as t
from types import ModuleType
from threading import Lock
from weakref import WeakKeyDictionary
from wsgiref.simple_server import make_server
from .routing import Router, Rule
from .request import Request
from .response import Response
from .config import Config, ConfigAttribute
from .globals import _app_ctx_stack, _request_ctx_stack, g, request, session
from .exceptions import HTTPException, NotFound, MethodNotAllowed, InternalServerError
from .middleware import Middleware, SessionMiddleware
from .templating import TemplateEngine
from .signals import signals, request_started, request_finished, got_request_exception
from .sessions import SessionInterface
from .json import JSONEncoder, JSONDecoder, json_provider
from .cli import cli

class starexx:
    __slots__ = (
        'import_name', 'name', 'root_path', 'static_folder', 'static_url_path',
        'template_folder', 'instance_path', 'instance_relative_config',
        'router', 'config', 'middleware', 'error_handlers', 'before_request_funcs',
        'after_request_funcs', 'teardown_request_funcs', 'url_builders',
        'url_default_functions', 'blueprints', 'extensions', 'view_functions',
        'jinja_environment', 'cli', 'json_provider', 'session_interface',
        '_static_folders', '_got_first_request', '_lock', '_before_request_lock'
    )

    config_class = Config
    request_class = Request
    response_class = Response
    router_class = Router
    json_provider_class = json_provider
    session_interface_class = SessionInterface

    static_folder = ConfigAttribute('STATIC_FOLDER')
    static_url_path = ConfigAttribute('STATIC_URL_PATH')
    template_folder = ConfigAttribute('TEMPLATE_FOLDER')
    secret_key = ConfigAttribute('SECRET_KEY')
    permanent_session_lifetime = ConfigAttribute('PERMANENT_SESSION_LIFETIME')
    debug = ConfigAttribute('DEBUG')
    testing = ConfigAttribute('TESTING')
    propagate_exceptions = ConfigAttribute('PROPAGATE_EXCEPTIONS')
    preserve_context_on_exception = ConfigAttribute('PRESERVE_CONTEXT_ON_EXCEPTION')
    trap_http_exceptions = ConfigAttribute('TRAP_HTTP_EXCEPTIONS')
    trap_bad_request_errors = ConfigAttribute('TRAP_BAD_REQUEST_ERRORS')
    preferred_url_scheme = ConfigAttribute('PREFERRED_URL_SCHEME')
    json_ascii = ConfigAttribute('JSON_AS_ASCII')
    json_sort_keys = ConfigAttribute('JSON_SORT_KEYS')
    jsonify_mimetype = ConfigAttribute('JSONIFY_MIMETYPE')
    jsonify_prettyprint_regular = ConfigAttribute('JSONIFY_PRETTYPRINT_REGULAR')
    max_content_length = ConfigAttribute('MAX_CONTENT_LENGTH')
    max_cookie_size = ConfigAttribute('MAX_COOKIE_SIZE')

    def __init__(self, import_name, static_folder='static', static_url_path=None,
                 template_folder='templates', instance_path=None, 
                 instance_relative_config=False, root_path=None):
        
        self.import_name = import_name
        self.name = import_name.split('.')[-1]
        
        if root_path is None:
            self.root_path = self._find_root_path()
        else:
            self.root_path = root_path
            
        self.static_folder = static_folder
        self.static_url_path = static_url_path
        self.template_folder = template_folder
        self.instance_path = instance_path
        self.instance_relative_config = instance_relative_config      
        self.router = self.router_class()
        self.config = self.make_config(instance_relative_config)
        self.middleware = []
        self.error_handlers = {}
        self.before_request_funcs = []
        self.after_request_funcs = []
        self.teardown_request_funcs = []
        self.url_builders = {}
        self.url_default_functions = {}
        self.blueprints = {}
        self.extensions = {}
        self.view_functions = {}        
        self._static_folders = {}
        self._got_first_request = False
        self._lock = Lock()
        self._before_request_lock = Lock()        
        self.cli = cli.AppGroup()
        self.json_provider = self.json_provider_class()
        self.session_interface = self.session_interface_class()       
        self._setup_default_config()
        self._setup_default_middleware()
        self._setup_default_error_handlers()
        self._setup_template_engine()
        self._setup_cli()

    def _find_root_path(self):
        module = sys.modules.get(self.import_name)
        if module is not None and hasattr(module, '__file__'):
            file_path = module.__file__
        else:
            loader = getattr(module, '__loader__', None)
            if loader is not None and hasattr(loader, 'get_filename'):
                file_path = loader.get_filename(self.import_name)
            else:
                file_path = __file__
                
        return os.path.dirname(os.path.abspath(file_path))

    def make_config(self, instance_relative=False):
        root_path = self.root_path
        if instance_relative:
            root_path = self.instance_path
        return self.config_class(root_path, self.default_config)

    @property
    def default_config(self):
        return {
            'DEBUG': False,
            'TESTING': False,
            'SECRET_KEY': os.urandom(24).hex(),
            'PERMANENT_SESSION_LIFETIME': 31 * 24 * 60 * 60,
            'PROPAGATE_EXCEPTIONS': None,
            'PRESERVE_CONTEXT_ON_EXCEPTION': None,
            'TRAP_HTTP_EXCEPTIONS': False,
            'TRAP_BAD_REQUEST_ERRORS': None,
            'PREFERRED_URL_SCHEME': 'http',
            'JSON_AS_ASCII': True,
            'JSON_SORT_KEYS': True,
            'JSONIFY_MIMETYPE': 'application/json',
            'JSONIFY_PRETTYPRINT_REGULAR': False,
            'MAX_CONTENT_LENGTH': 16 * 1024 * 1024,
            'MAX_COOKIE_SIZE': 4093,
            'STATIC_FOLDER': 'static',
            'STATIC_URL_PATH': None,
            'TEMPLATE_FOLDER': 'templates',
            'SERVER_NAME': None,
            'APPLICATION_ROOT': '/',
            'SESSION_COOKIE_NAME': 'session',
            'SESSION_COOKIE_DOMAIN': None,
            'SESSION_COOKIE_PATH': None,
            'SESSION_COOKIE_HTTPONLY': True,
            'SESSION_COOKIE_SECURE': False,
            'SESSION_COOKIE_SAMESITE': None,
            'SESSION_REFRESH_EACH_REQUEST': True,
            'USE_X_SENDFILE': False,
            'SEND_FILE_MAX_AGE_DEFAULT': 12 * 60 * 60,
            'ERROR_404_HELP': True
        }

    def _setup_default_config(self):
        self.config.from_mapping(self.default_config)

    def _setup_default_middleware(self):
        self.use(SessionMiddleware())

    def _setup_default_error_handlers(self):
        self.error_handler(404)(self._default_404_handler)
        self.error_handler(405)(self._default_405_handler)
        self.error_handler(500)(self._default_500_handler)

    def _setup_template_engine(self):
        self.jinja_environment = TemplateEngine(self)

    def _setup_cli(self):
        if hasattr(self, 'cli'):
            self.cli.name = self.name

    def route(self, rule, **options):
        def decorator(f):
            endpoint = options.pop('endpoint', None)
            self.add_url_rule(rule, endpoint, f, **options)
            return f
        return decorator

    def get(self, rule, **options):
        return self.route(rule, methods=['GET'], **options)

    def post(self, rule, **options):
        return self.route(rule, methods=['POST'], **options)

    def put(self, rule, **options):
        return self.route(rule, methods=['PUT'], **options)

    def delete(self, rule, **options):
        return self.route(rule, methods=['DELETE'], **options)

    def patch(self, rule, **options):
        return self.route(rule, methods=['PATCH'], **options)

    def add_url_rule(self, rule, endpoint=None, view_func=None, **options):
        if endpoint is None:
            endpoint = view_func.__name__
            
        options['endpoint'] = endpoint
        methods = options.pop('methods', None)
        
        if methods is None:
            methods = ['GET']
            
        rule_obj = Rule(rule, methods=methods, **options)
        self.router.add_rule(rule_obj, view_func)
        
        if view_func is not None:
            self.view_functions[endpoint] = view_func

    def endpoint(self, endpoint):
        def decorator(f):
            self.view_functions[endpoint] = f
            return f
        return decorator

    def error_handler(self, code_or_exception):
        def decorator(f):
            if isinstance(code_or_exception, int):
                self.error_handlers[code_or_exception] = f
            else:
                self.error_handlers[code_or_exception] = f
            return f
        return decorator

    def before_request(self, f):
        self.before_request_funcs.append(f)
        return f

    def after_request(self, f):
        self.after_request_funcs.append(f)
        return f

    def teardown_request(self, f):
        self.teardown_request_funcs.append(f)
        return f

    def use(self, middleware):
        if not isinstance(middleware, Middleware):
            raise TypeError("Middleware must be an instance of Middleware class")
        self.middleware.append(middleware)

    def static(self, url_path, folder, **options):
        self._static_folders[url_path] = (folder, options)

    def register_blueprint(self, blueprint, **options):
        blueprint.register(self, options)

    def create_global_jinja_loader(self):
        from .templating import DispatchingJinjaLoader
        return DispatchingJinjaLoader(self)

    def _default_404_handler(self, e):
        from .helpers import render_template_string
        return render_template_string('''
        <!DOCTYPE html>
        <html>
        <head><title>404 Not Found</title></head>
        <body>
            <h1>404 - Page Not Found</h1>
            <p>The requested URL was not found on this server.</p>
        </body>
        </html>
        ''', status=404)

    def _default_405_handler(self, e):
        from .helpers import render_template_string
        return render_template_string('''
        <!DOCTYPE html>
        <html>
        <head><title>405 Method Not Allowed</title></head>
        <body>
            <h1>405 - Method Not Allowed</h1>
            <p>The method is not allowed for the requested URL.</p>
        </body>
        </html>
        ''', status=405)

    def _default_500_handler(self, e):
        from .helpers import render_template_string
        return render_template_string('''
        <!DOCTYPE html>
        <html>
        <head><title>500 Server Error</title></head>
        <body>
            <h1>500 - Internal Server Error</h1>
            <p>Something went wrong on the server.</p>
        </body>
        </html>
        ''', status=500)

    def _handle_static_request(self, path):
        for url_path, (folder, options) in self._static_folders.items():
            if path.startswith(url_path):
                file_path = path[len(url_path):].lstrip('/')
                full_path = os.path.join(folder, file_path)
                
                if os.path.exists(full_path) and os.path.isfile(full_path):
                    from .helpers import send_file
                    return send_file(full_path, **options)
        return None

    def __call__(self, environ, start_response):
        return self.wsgi_app(environ, start_response)

    def wsgi_app(self, environ, start_response):
        ctx = self.request_context(environ)
        ctx.push()
        
        try:
            try:
                response = self.full_dispatch_request()
            except Exception as e:
                response = self.handle_exception(e)
            return response(environ, start_response)
        finally:
            if self.should_ignore_error(e):
                ctx.pop(e)

    def request_context(self, environ):
        return _RequestContext(self, environ)

    def full_dispatch_request(self):
        self.try_trigger_before_first_request_functions()
        request_started.send(self)
        
        try:
            rv = self.preprocess_request()
            if rv is None:
                rv = self.dispatch_request()
        except Exception as e:
            rv = self.handle_user_exception(e)
            
        response = self.make_response(rv)
        response = self.process_response(response)
        request_finished.send(self, response=response)
        return response

    def preprocess_request(self):
        for middleware in self.middleware:
            response = middleware.process_request(request)
            if response is not None:
                return response
                
        for func in self.before_request_funcs:
            rv = func()
            if rv is not None:
                return rv
        return None

    def dispatch_request(self):
        req = _request_ctx_stack.top.request
        rule = req.url_rule
        
        if rule is None:
            raise NotFound()
            
        return self.view_functions[rule.endpoint](**req.view_args)

    def make_response(self, rv):
        if isinstance(rv, self.response_class):
            return rv
        if isinstance(rv, str):
            return self.response_class(rv)
        if isinstance(rv, bytes):
            return self.response_class(rv)
        if isinstance(rv, dict):
            return self.json_provider.response(rv)
        if isinstance(rv, tuple):
            return self.response_class(*rv)
        return self.response_class.force_type(rv, request.environ)

    def process_response(self, response):
        ctx = _request_ctx_stack.top
        
        for func in reversed(self.after_request_funcs):
            response = func(response)
            
        for middleware in reversed(self.middleware):
            response = middleware.process_response(request, response)
            
        if not self.session_interface.is_null_session(ctx.session):
            self.session_interface.save_session(self, ctx.session, response)
            
        return response

    def handle_exception(self, e):
        got_request_exception.send(self, exception=e)
        
        if isinstance(e, HTTPException):
            return self.handle_http_exception(e)
            
        handler = self._find_error_handler(e)
        if handler is not None:
            return handler(e)
            
        return self._default_500_handler(e)

    def handle_http_exception(self, e):
        handler = self._find_error_handler(e)
        if handler is None:
            return e.get_response()
        return handler(e)

    def _find_error_handler(self, e):
        if isinstance(e, HTTPException):
            code = e.code
        else:
            code = 500
            
        return self.error_handlers.get(code, self.error_handlers.get(e.__class__))

    def try_trigger_before_first_request_functions(self):
        with self._before_request_lock:
            if not self._got_first_request:
                self._got_first_request = True
                try:
                    pass
                except:
                    self._got_first_request = False
                    raise

    def should_ignore_error(self, error):
        return False

    def run(self, host=None, port=None, debug=None, **options):
        if host is None:
            host = '127.0.0.1'
        if port is None:
            port = 5000
        if debug is not None:
            self.debug = bool(debug)
            
        print(f" * Running on http://{host}:{port} (Press CTRL+C to quit)")
        
        if self.debug:
            print(" * Debug mode: ON")
            print(" * WARNING: This is a development server.")
            
        server = make_server(host, port, self, **options)
        
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            print("\n * Shutting down the server...")