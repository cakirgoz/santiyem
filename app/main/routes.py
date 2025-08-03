from flask import render_template, request
from . import main
from datetime import datetime

def is_htmx_request():
    return 'HX-Request' in request.headers

@main.route('/')
def index():
    if is_htmx_request():
        return render_template('index_content.html')
    return render_template('index.html')

@main.route('/about')
def about():
    template = 'about.html' if is_htmx_request() else 'pages/about.html'
    return render_template(template)

@main.route('/contact')
def contact():
    template = 'contact.html' if is_htmx_request() else 'pages/contact.html'
    return render_template(template)
