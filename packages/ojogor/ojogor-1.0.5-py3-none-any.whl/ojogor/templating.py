import typing as t
import re
import os
from threading import Lock
from weakref import WeakKeyDictionary

class TemplateEngine:
    __slots__ = ('app', '_engines', '_lock')

    def __init__(self, app):
        self.app = app
        self._engines = {}
        self._lock = Lock()

    def render_template(self, template_name, **context):
        template = self._get_template(template_name)
        return template.render(**context)

    def render_template_string(self, source, **context):
        template = self._create_template_from_string(source)
        return template.render(**context)

    def _get_template(self, template_name):
        with self._lock:
            if template_name in self._engines:
                return self._engines[template_name]

            template_path = os.path.join(self.app.template_folder, template_name)
            with open(template_path, 'r') as f:
                source = f.read()

            template = Template(source)
            self._engines[template_name] = template
            return template

    def _create_template_from_string(self, source):
        return Template(source)

class Template:
    __slots__ = ('source', '_compiled')

    def __init__(self, source):
        self.source = source
        self._compiled = None

    def render(self, **context):
        if self._compiled is None:
            self._compiled = self._compile()

        return self._compiled(context)

    def _compile(self):
        code = self._parse_template()
        return self._create_render_function(code)

    def _parse_template(self):
        lines = self.source.split('\n')
        output = []
        in_block = False
        block_stack = []

        for line in lines:
            stripped = line.strip()

            if stripped.startswith('{% for'):
                match = re.match(r'\{% for (\w+) in (\w+) %\}', stripped)
                if match:
                    var_name, iter_name = match.groups()
                    output.append(f"for {var_name} in {iter_name}:")
                    in_block = True
                    block_stack.append('for')
            elif stripped == '{% endfor %}':
                if block_stack and block_stack[-1] == 'for':
                    block_stack.pop()
                    output.append("")
                in_block = False
            elif stripped.startswith('{% if'):
                match = re.match(r'\{% if (.*) %\}', stripped)
                if match:
                    condition = match.group(1)
                    output.append(f"if {condition}:")
                    in_block = True
                    block_stack.append('if')
            elif stripped == '{% endif %}':
                if block_stack and block_stack[-1] == 'if':
                    block_stack.pop()
                    output.append("")
                in_block = False
            elif stripped.startswith('{{') and stripped.endswith('}}'):
                expr = stripped[2:-2].strip()
                output.append(f"__output.append(str({expr}))")
            elif not in_block and stripped:
                escaped_line = line.replace('"', '\\"')
                output.append(f'__output.append("{escaped_line}")')

        return '\n'.join(output)

    def _create_render_function(self, code):
        def render_function(context):
            __output = []
            locals_dict = context.copy()
            locals_dict['__output'] = __output
            
            try:
                exec(code, {}, locals_dict)
            except Exception as e:
                raise TemplateError(f"Template rendering error: {e}")
            
            return '\n'.join(__output)

        return render_function

class TemplateContext:
    __slots__ = ('_dict',)

    def __init__(self, *args, **kwargs):
        self._dict = dict(*args, **kwargs)

    def __getitem__(self, key):
        return self._dict[key]

    def __setitem__(self, key, value):
        self._dict[key] = value

    def __delitem__(self, key):
        del self._dict[key]

    def __contains__(self, key):
        return key in self._dict

    def __iter__(self):
        return iter(self._dict)

    def __len__(self):
        return len(self._dict)

    def __repr__(self):
        return repr(self._dict)

class TemplateRenderer:
    __slots__ = ('engine',)

    def __init__(self, engine):
        self.engine = engine

    def render(self, template_name, **context):
        return self.engine.render_template(template_name, **context)

    def render_string(self, source, **context):
        return self.engine.render_template_string(source, **context)

class TemplateError(Exception):
    __slots__ = ('message',)

    def __init__(self, message):
        self.message = message
        super().__init__(self.message)

class DispatchingJinjaLoader:
    __slots__ = ('app',)

    def __init__(self, app):
        self.app = app

    def get_source(self, environment, template):
        for loader in self._get_loaders():
            try:
                return loader.get_source(environment, template)
            except Exception:
                continue
        raise TemplateError(f"Template not found: {template}")

    def _get_loaders(self):
        return []