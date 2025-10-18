import typing as t
import os
import json

class ConfigAttribute:
    __slots__ = ('name', 'get_converter', 'set_converter')

    def __init__(self, name, get_converter=None, set_converter=None):
        self.name = name
        self.get_converter = get_converter
        self.set_converter = set_converter

    def __get__(self, obj, type=None):
        if obj is None:
            return self
        rv = obj.config.get(self.name)
        if self.get_converter is not None:
            rv = self.get_converter(rv)
        return rv

    def __set__(self, obj, value):
        if self.set_converter is not None:
            value = self.set_converter(value)
        obj.config[self.name] = value

class Config:
    __slots__ = ('_config', '_root_path')

    def __init__(self, root_path=None, defaults=None):
        self._config = {}
        self._root_path = root_path
        if defaults is not None:
            self.from_mapping(defaults)

    def __getitem__(self, key):
        return self._config[key]

    def __setitem__(self, key, value):
        self._config[key] = value

    def __delitem__(self, key):
        del self._config[key]

    def __contains__(self, key):
        return key in self._config

    def __iter__(self):
        return iter(self._config)

    def __len__(self):
        return len(self._config)

    def __repr__(self):
        return f"<Config {self._config!r}>"

    def get(self, key, default=None):
        return self._config.get(key, default)

    def setdefault(self, key, default=None):
        return self._config.setdefault(key, default)

    def from_mapping(self, mapping=None, **kwargs):
        mappings = []
        if mapping is not None:
            mappings.append(mapping)
        mappings.append(kwargs)
        for mapping in mappings:
            for key, value in mapping.items():
                self._config[key] = value

    def from_object(self, obj):
        if isinstance(obj, str):
            obj = self._import_string(obj)
        for key in dir(obj):
            if key.isupper():
                self._config[key] = getattr(obj, key)

    def from_file(self, filename, load=json.load, silent=False):
        filename = os.path.join(self._root_path, filename)
        try:
            with open(filename) as f:
                obj = load(f)
        except IOError as e:
            if silent:
                return False
            e.strerror = f'Unable to load configuration file ({e.strerror})'
            raise
        return self.from_mapping(obj)

    def from_envvar(self, variable_name, silent=False):
        rv = os.environ.get(variable_name)
        if not rv:
            if silent:
                return False
            raise RuntimeError(f'The environment variable {variable_name!r} is not set')
        return self.from_file(rv)

    def from_pyfile(self, filename, silent=False):
        filename = os.path.join(self._root_path, filename)
        d = type('Config', (), {})()
        with open(filename) as config_file:
            exec(compile(config_file.read(), filename, 'exec'), d.__dict__)
        self.from_object(d)
        return True

    def _import_string(self, import_name):
        import importlib
        try:
            module_name, obj_name = import_name.rsplit('.', 1)
            module = importlib.import_module(module_name)
            return getattr(module, obj_name)
        except (ImportError, AttributeError) as e:
            raise ImportError(import_name) from e

    def keys(self):
        return self._config.keys()

    def values(self):
        return self._config.values()

    def items(self):
        return self._config.items()

    def update(self, other):
        self._config.update(other)

    def clear(self):
        self._config.clear()

    def pop(self, key, default=None):
        return self._config.pop(key, default)