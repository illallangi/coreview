from flask import Flask

from .frontend import blueprint as frontend_blueprint
from .v1 import blueprint as v1_blueprint


def create_app(configfile=None):
    app = Flask(__name__)
    app.config.from_prefixed_env(prefix=app.name.split(".")[-1].upper())
    app.register_blueprint(frontend_blueprint)
    app.register_blueprint(v1_blueprint)

    return app
