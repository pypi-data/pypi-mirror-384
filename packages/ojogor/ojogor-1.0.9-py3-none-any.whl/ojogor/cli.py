import click

@click.group()
def cli():
    pass

@cli.command()
@click.option('--host', default='127.0.0.1')
@click.option('--port', default=5000)
def run(host, port):
    from .globals import current_app
    app = current_app
    
    print(f"Application at http://{host}:{port}")
    
    from wsgiref.simple_server import make_server
    server = make_server(host, port, app)
    server.serve_forever()

@cli.command()
def routes():
    from .globals import current_app
    app = current_app
    
    print("Routes:")
    for (method, path), handler in app.routes.items():
        print(f"{method} {path} -> {handler.__name__}")

def main():
    cli()

if __name__ == '__main__':
    main()