import typing as t
import json
import base64
import hmac
import hashlib
from datetime import datetime, timedelta

class SessionInterface:
    __slots__ = ()

    def open_session(self, app, request):
        return None

    def save_session(self, app, session, response):
        pass

    def is_null_session(self, obj):
        return False

    def make_null_session(self, app):
        return SecureCookieSession()

class SecureCookieSessionInterface(SessionInterface):
    __slots__ = ('salt', 'digest_method')

    def __init__(self, salt='cookie-session', digest_method='sha1'):
        self.salt = salt
        self.digest_method = digest_method

    def open_session(self, app, request):
        s = request.cookies.get(app.session_cookie_name)
        if not s:
            return self.make_null_session(app)
        return SecureCookieSession.decode(s, app.secret_key, self.salt, self.digest_method)

    def save_session(self, app, session, response):
        if session:
            if not session:
                response.delete_cookie(app.session_cookie_name)
            else:
                s = session.encode(app.secret_key, self.salt, self.digest_method)
                response.set_cookie(app.session_cookie_name, s)

    def is_null_session(self, obj):
        return obj is None or not obj

class SecureCookieSession(dict):
    __slots__ = ('_modified',)

    def __init__(self, initial=None):
        super().__init__(initial or ())
        self._modified = False

    def __setitem__(self, key, value):
        super().__setitem__(key, value)
        self._modified = True

    def __delitem__(self, key):
        super().__delitem__(key)
        self._modified = True

    def pop(self, key, default=None):
        self._modified = True
        return super().pop(key, default)

    def clear(self):
        self._modified = True
        super().clear()

    def update(self, *args, **kwargs):
        self._modified = True
        super().update(*args, **kwargs)

    def setdefault(self, key, default=None):
        self._modified = True
        return super().setdefault(key, default)

    def encode(self, secret_key, salt, digest_method='sha1'):
        if not self:
            return ''
        
        data = json.dumps(dict(self))
        
        if digest_method == 'sha1':
            h = hmac.new(secret_key.encode(), digestmod=hashlib.sha1)
        else:
            h = hmac.new(secret_key.encode(), digestmod=hashlib.sha256)
        
        h.update(salt.encode())
        h.update(data.encode())
        signature = h.hexdigest()
        
        payload = base64.b64encode(data.encode()).decode()
        return f"{payload}.{signature}"

    @classmethod
    def decode(cls, s, secret_key, salt, digest_method='sha1'):
        try:
            payload, signature = s.rsplit('.', 1)
            data = base64.b64decode(payload).decode()
            
            if digest_method == 'sha1':
                h = hmac.new(secret_key.encode(), digestmod=hashlib.sha1)
            else:
                h = hmac.new(secret_key.encode(), digestmod=hashlib.sha256)
            
            h.update(salt.encode())
            h.update(data.encode())
            
            if not hmac.compare_digest(h.hexdigest(), signature):
                return cls()
            
            return cls(json.loads(data))
        except Exception:
            return cls()

    @property
    def modified(self):
        return self._modified

    def __repr__(self):
        return f"<SecureCookieSession {dict(self)!r}>"

class Session(dict):
    __slots__ = ('_modified',)

    def __init__(self, initial=None):
        super().__init__(initial or ())
        self._modified = False

    def __setitem__(self, key, value):
        super().__setitem__(key, value)
        self._modified = True

    def __delitem__(self, key):
        super().__delitem__(key)
        self._modified = True

    def pop(self, key, default=None):
        self._modified = True
        return super().pop(key, default)

    def clear(self):
        self._modified = True
        super().clear()

    def update(self, *args, **kwargs):
        self._modified = True
        super().update(*args, **kwargs)

    def setdefault(self, key, default=None):
        self._modified = True
        return super().setdefault(key, default)

    @property
    def modified(self):
        return self._modified

    def __repr__(self):
        return f"<Session {dict(self)!r}>"