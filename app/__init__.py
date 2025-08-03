from flask import Flask

def create_app():
    app = Flask(__name__)

    # Register Blueprints
    from .main import main as main_blueprint
    app.register_blueprint(main_blueprint)

    from .engineering_apps import engineering_apps as engineering_apps_blueprint
    app.register_blueprint(engineering_apps_blueprint, url_prefix='/apps')

    return app
