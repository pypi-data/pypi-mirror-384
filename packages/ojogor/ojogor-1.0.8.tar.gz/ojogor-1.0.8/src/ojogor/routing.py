import typing as t
import re
import warnings
from threading import Lock
from urllib.parse import quote
from weakref import WeakKeyDictionary

class Rule:
    __slots__ = ('rule', 'methods', 'endpoint', 'defaults', 'subdomain', 'strict_slashes', 'merge_slashes', 'redirect_to', 'alias', 'host')

    def __init__(self, rule, methods=None, endpoint=None, defaults=None, subdomain=None, strict_slashes=True, merge_slashes=True, redirect_to=None, alias=None, host=None):
        self.rule = rule
        self.methods = methods
        self.endpoint = endpoint
        self.defaults = defaults
        self.subdomain = subdomain
        self.strict_slashes = strict_slashes
        self.merge_slashes = merge_slashes
        self.redirect_to = redirect_to
        self.alias = alias
        self.host = host

    def compile(self):
        return RuleCompiler().compile(self.rule)

    def match(self, path):
        return self.compile().match(path)

    def build(self, values, append_unknown=True):
        return self.compile().build(values, append_unknown)

    def __str__(self):
        return self.rule

    def __repr__(self):
        return f"<Rule '{self.rule}' -> {self.endpoint}>"

class RuleCompiler:
    __slots__ = ('_cache', '_lock')

    def __init__(self):
        self._cache = {}
        self._lock = Lock()

    def compile(self, rule):
        with self._lock:
            if rule in self._cache:
                return self._cache[rule]

            regex_parts = []
            converter_parts = []
            is_static = True
            pos = 0
            rule_len = len(rule)

            while pos < rule_len:
                match = re.search(r'<(.+?)>', rule[pos:])
                if not match:
                    regex_parts.append(re.escape(rule[pos:]))
                    break

                start, end = match.span()
                regex_parts.append(re.escape(rule[pos:pos + start]))
                pos += start

                converter = match.group(1)
                if ':' in converter:
                    converter_name, arg = converter.split(':', 1)
                    if converter_name == 'int':
                        regex = r'\d+'
                    elif converter_name == 'float':
                        regex = r'\d+\.\d+'
                    elif converter_name == 'path':
                        regex = r'.*?'
                    elif converter_name == 'uuid':
                        regex = r'[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}'
                    else:
                        regex = r'[^/]+'
                    converter_parts.append((converter_name, arg))
                else:
                    regex = r'[^/]+'
                    converter_parts.append((converter, None))

                regex_parts.append(f'({regex})')
                pos += end - start
                is_static = False

            regex_pattern = '^' + ''.join(regex_parts)
            if not rule.endswith('/'):
                regex_pattern += '/?'

            compiled_rule = CompiledRule(regex_pattern, converter_parts, is_static)
            self._cache[rule] = compiled_rule
            return compiled_rule

class CompiledRule:
    __slots__ = ('regex', 'converters', 'is_static', '_compiled_regex')

    def __init__(self, regex, converters, is_static):
        self.regex = regex
        self.converters = converters
        self.is_static = is_static
        self._compiled_regex = re.compile(regex)

    def match(self, path):
        match = self._compiled_regex.match(path)
        if not match:
            return None, {}

        groups = match.groups()
        values = {}
        for (name, arg), value in zip(self.converters, groups):
            if name == 'int':
                try:
                    values[name] = int(value)
                except ValueError:
                    return None, {}
            elif name == 'float':
                try:
                    values[name] = float(value)
                except ValueError:
                    return None, {}
            elif name == 'path':
                values[name] = value
            else:
                values[name] = value

        return self, values

    def build(self, values, append_unknown=True):
        path = self.regex
        for (name, arg), value in zip(self.converters, values.values()):
            path = path.replace(f'({re.escape(str(value))})', str(value), 1)
        return path

class Router:
    __slots__ = ('rules', '_rules_by_endpoint', '_rules_by_method', '_lock')

    def __init__(self):
        self.rules = []
        self._rules_by_endpoint = {}
        self._rules_by_method = {}
        self._lock = Lock()

    def add_rule(self, rule, view_func):
        with self._lock:
            self.rules.append((rule, view_func))
            self._rules_by_endpoint[rule.endpoint] = (rule, view_func)
            
            for method in rule.methods:
                if method not in self._rules_by_method:
                    self._rules_by_method[method] = []
                self._rules_by_method[method].append((rule, view_func))

    def match(self, method, path):
        if method not in self._rules_by_method:
            return None, {}

        for rule, view_func in self._rules_by_method[method]:
            matched_rule, values = rule.match(path)
            if matched_rule:
                return view_func, values

        return None, {}

    def build(self, endpoint, values=None, method=None):
        if endpoint not in self._rules_by_endpoint:
            return None

        rule, view_func = self._rules_by_endpoint[endpoint]
        return rule.build(values or {})

    def create_url_adapter(self, request):
        return URLAdapter(self, request)

class URLAdapter:
    __slots__ = ('router', 'request')

    def __init__(self, router, request):
        self.router = router
        self.request = request

    def build(self, endpoint, values=None, method=None, force_external=False):
        return self.router.build(endpoint, values, method)

    def match(self, path=None, method=None):
        if path is None:
            path = self.request.path
        if method is None:
            method = self.request.method
        return self.router.match(method, path)

class Blueprint:
    __slots__ = ('name', 'import_name', 'url_prefix', 'subdomain', 'url_defaults', 'root_path', 'deferred_functions', 'rules')

    def __init__(self, name, import_name, url_prefix=None, subdomain=None, url_defaults=None):
        self.name = name
        self.import_name = import_name
        self.url_prefix = url_prefix
        self.subdomain = subdomain
        self.url_defaults = url_defaults or {}
        self.root_path = self._find_root_path()
        self.deferred_functions = []
        self.rules = []

    def _find_root_path(self):
        module = __import__(self.import_name)
        return module.__file__

    def route(self, rule, **options):
        def decorator(f):
            endpoint = options.pop("endpoint", f.__name__)
            self.add_url_rule(rule, endpoint, f, **options)
            return f
        return decorator

    def add_url_rule(self, rule, endpoint=None, view_func=None, **options):
        if endpoint is None:
            endpoint = view_func.__name__
            
        if self.url_prefix is not None:
            rule = self.url_prefix + rule
            
        options['endpoint'] = endpoint
        self.rules.append((rule, view_func, options))

    def register(self, app, options):
        url_prefix = options.get('url_prefix') or self.url_prefix
        for rule, view_func, opts in self.rules:
            app.add_url_rule(rule, view_func=view_func, **opts)