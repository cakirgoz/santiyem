from flask import Blueprint

engineering_apps = Blueprint('engineering_apps', __name__, template_folder='templates')

from . import routes
