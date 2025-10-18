import os
import typing as t
from urllib.parse import urljoin

from .globals import request, current_app
from .response import Response
from .exceptions import abort

def url_for(endpoint, **values):
    app = current_app._get_current_app()
    return app.router.build(endpoint, values)

def redirect(location, code=302):
    response = Response('', status=code)
    response.headers['Location'] = location
    return response

def jsonify(*args, **kwargs):
    if args and kwargs:
        raise TypeError('jsonify() behavior undefined when passed both args and kwargs')
    elif len(args) == 1:
        data = args[0]
    else:
        data = args or kwargs

    return current_app.json_provider.response(data)

def render_template(template_name, **context):
    return current_app.jinja_environment.render_template(template_name, **context)

def render_template_string(source, **context):
    return current_app.jinja_environment.render_template_string(source, **context)

def send_file(filename, **options):
    with open(filename, 'rb') as f:
        content = f.read()
    
    response = Response(content)
    
    mimetype = options.get('mimetype')
    if mimetype is None:
        if filename.endswith('.css'):
            mimetype = 'text/css'
        elif filename.endswith('.js'):
            mimetype = 'application/javascript'
        elif filename.endswith('.html'):
            mimetype = 'text/html'
        elif filename.endswith('.json'):
            mimetype = 'application/json'
        else:
            mimetype = 'application/octet-stream'
    
    response.headers['Content-Type'] = mimetype
    response.headers['Content-Disposition'] = f'attachment; filename="{os.path.basename(filename)}"'
    
    return response

def send_from_directory(directory, filename, **options):
    filename = os.path.join(directory, filename)
    return send_file(filename, **options)

def make_response(rv):
    if isinstance(rv, Response):
        return rv
    if isinstance(rv, str):
        return Response(rv)
    if isinstance(rv, bytes):
        return Response(rv)
    if isinstance(rv, dict):
        return jsonify(rv)
    if isinstance(rv, tuple):
        return Response(*rv)
    return Response(str(rv))

def flash(message, category='message'):
    import ojogor.globals as globals
    globals.flash(message, category)

def get_flashed_messages(with_categories=False):
    import ojogor.globals as globals
    return globals.get_flashed_messages(with_categories)