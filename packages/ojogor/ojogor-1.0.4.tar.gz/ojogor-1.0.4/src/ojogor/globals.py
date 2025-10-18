import typing as t
from threading import Lock
from weakref import WeakKeyDictionary

class _AppCtxGlobals:
    __slots__ = ()

    def __init__(self):
        self._data = {}

    def get(self, name, default=None):
        return self._data.get(name, default)

    def pop(self, name, default=None):
        return self._data.pop(name, default)

    def setdefault(self, name, default=None):
        return self._data.setdefault(name, default)

    def __contains__(self, item):
        return item in self._data

    def __getitem__(self, item):
        return self._data[item]

    def __setitem__(self, key, value):
        self._data[key] = value

    def __delitem__(self, key):
        del self._data[key]

    def __iter__(self):
        return iter(self._data)

    def __repr__(self):
        return f"<AppCtxGlobals {self._data!r}>"

class _AppContext:
    __slots__ = ('app', 'g', '_refcnt')

    def __init__(self, app):
        self.app = app
        self.g = app.app_ctx_globals_class()
        self._refcnt = 0

class _RequestContext:
    __slots__ = ('app', 'request', 'session', 'url_adapter', '_implicit_app_ctx_stack', '_preserved')

    def __init__(self, app, environ):
        self.app = app
        self.request = app.request_class(environ)
        self.session = None
        self.url_adapter = None
        self._implicit_app_ctx_stack = []
        self._preserved = False

    def push(self):
        top = _request_ctx_stack.top
        if top is not None and top.preserved:
            top.pop(top._preserved_exc)

        app_ctx = _app_ctx_stack.top
        if app_ctx is None or app_ctx.app != self.app:
            app_ctx = self.app.app_context()
            app_ctx.push()
            self._implicit_app_ctx_stack.append(app_ctx)
        else:
            self._implicit_app_ctx_stack.append(None)

        _request_ctx_stack.push(self)

        if self.session is None:
            session_interface = self.app.session_interface
            self.session = session_interface.open_session(self.app, self.request)
            if self.session is None:
                self.session = session_interface.make_null_session(self.app)

        if self.url_adapter is None:
            self.url_adapter = self.app.create_url_adapter(self.request)

    def pop(self, exc=None):
        app_ctx = self._implicit_app_ctx_stack.pop()
        try:
            if not self._preserved:
                self.app.do_teardown_request(exc)
            request_ctx = _request_ctx_stack.pop()
            if request_ctx is not self:
                raise AssertionError("Popped wrong request context.")
        finally:
            if app_ctx is not None:
                app_ctx.pop(exc)

    def __enter__(self):
        self.push()
        return self

    def __exit__(self, exc_type, exc_value, tb):
        self.pop(exc_value)

class _AppCtxStack:
    __slots__ = ('_stack',)

    def __init__(self):
        self._stack = []

    def push(self, obj):
        self._stack.append(obj)

    def pop(self):
        return self._stack.pop()

    @property
    def top(self):
        if self._stack:
            return self._stack[-1]
        return None

    def __len__(self):
        return len(self._stack)

    def __iter__(self):
        return iter(self._stack)

class _RequestCtxStack(_AppCtxStack):
    __slots__ = ()

_app_ctx_stack = _AppCtxStack()
_request_ctx_stack = _RequestCtxStack()

class _Lookup:
    __slots__ = ('name', 'description')

    def __init__(self, name, description):
        self.name = name
        self.description = description

    def __get__(self, obj, type=None):
        if obj is None:
            return self
        return getattr(obj, f"_get_{self.name}")()

    def __set__(self, obj, value):
        raise AttributeError(f"can't set attribute {self.name!r}")

    def __delete__(self, obj):
        raise AttributeError(f"can't delete attribute {self.name!r}")

def _lookup_req_object(name):
    top = _request_ctx_stack.top
    if top is None:
        raise RuntimeError(f"Working outside of request context: {name}")
    return getattr(top, name)

def _lookup_app_object(name):
    top = _app_ctx_stack.top
    if top is None:
        raise RuntimeError(f"Working outside of application context: {name}")
    return getattr(top, name)

def _find_app():
    top = _app_ctx_stack.top
    if top is None:
        raise RuntimeError("Working outside of application context.")
    return top.app

class _RequestProxy:
    __slots__ = ()

    def _get_request(self):
        return _lookup_req_object('request')

    def __getattr__(self, name):
        return getattr(self._get_request(), name)

    def __setattr__(self, name, value):
        setattr(self._get_request(), name, value)

    def __delattr__(self, name):
        delattr(self._get_request(), name)

    def __getitem__(self, key):
        return self._get_request()[key]

    def __setitem__(self, key, value):
        self._get_request()[key] = value

    def __delitem__(self, key):
        del self._get_request()[key]

    def __contains__(self, key):
        return key in self._get_request()

    def __iter__(self):
        return iter(self._get_request())

    def __len__(self):
        return len(self._get_request())

    def __repr__(self):
        return repr(self._get_request())

class _SessionProxy:
    __slots__ = ()

    def _get_session(self):
        return _lookup_req_object('session')

    def __getattr__(self, name):
        return getattr(self._get_session(), name)

    def __setattr__(self, name, value):
        setattr(self._get_session(), name, value)

    def __delattr__(self, name):
        delattr(self._get_session(), name)

    def __getitem__(self, key):
        return self._get_session()[key]

    def __setitem__(self, key, value):
        self._get_session()[key] = value

    def __delitem__(self, key):
        del self._get_session()[key]

    def __contains__(self, key):
        return key in self._get_session()

    def __iter__(self):
        return iter(self._get_session())

    def __len__(self):
        return len(self._get_session())

    def __repr__(self):
        return repr(self._get_session())

class _GProxy:
    __slots__ = ()

    def _get_g(self):
        return _lookup_app_object('g')

    def __getattr__(self, name):
        return getattr(self._get_g(), name)

    def __setattr__(self, name, value):
        setattr(self._get_g(), name, value)

    def __delattr__(self, name):
        delattr(self._get_g(), name)

    def __getitem__(self, key):
        return self._get_g()[key]

    def __setitem__(self, key, value):
        self._get_g()[key] = value

    def __delitem__(self, key):
        del self._get_g()[key]

    def __contains__(self, key):
        return key in self._get_g()

    def __iter__(self):
        return iter(self._get_g())

    def __len__(self):
        return len(self._get_g())

    def __repr__(self):
        return repr(self._get_g())

class _CurrentAppProxy:
    __slots__ = ()

    def _get_current_app(self):
        return _find_app()

    def __getattr__(self, name):
        return getattr(self._get_current_app(), name)

    def __setattr__(self, name, value):
        setattr(self._get_current_app(), name, value)

    def __delattr__(self, name):
        delattr(self._get_current_app(), name)

    def __repr__(self):
        return repr(self._get_current_app())

request = _RequestProxy()
session = _SessionProxy()
g = _GProxy()
current_app = _CurrentAppProxy()

def has_request_context():
    return _request_ctx_stack.top is not None

def has_app_context():
    return _app_ctx_stack.top is not None

def _get_flashed_messages():
    return session.get('_flashes', [])

def _set_flashed_messages(messages):
    session['_flashes'] = messages

def flash(message, category='message'):
    flashes = session.get('_flashes', [])
    flashes.append((category, message))
    session['_flashes'] = flashes

def get_flashed_messages(with_categories=False):
    flashes = _get_flashed_messages()
    if flashes:
        _set_flashed_messages([])
    if with_categories:
        return flashes
    return [msg for _, msg in flashes]

from .helpers import url_for, abort, redirect, jsonify, render_template
from .helpers import send_file, send_from_directory, make_response