# Ojogor
Ojogor is a simple python web application framework. It is designed to provide a quick and intuitive startup experience while offering powerful scalability for complex enterprise applications. Built as an intelligent wrapper around Werkzeug and Jinja, ojogor introduces middleware-first architecture and enhanced developer ergonomics, positioning itself as the next evolution in python web frameworks.


### A Simple Example
```py
# save this as app.py
from starexx import starexx, jsonify

app = starexx(__name__)

@app.get('/')
def hello():
    return "Hello, World!"

if __name__ == '__main__':
    app.run(debug=True)
```
