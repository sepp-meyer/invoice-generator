from flask import Flask
from .config import DefaultConfig

def create_app():
    app = Flask(__name__)
    app.config.from_object(DefaultConfig)

    # Blueprints
    from .routes.main import bp as main_bp
    app.register_blueprint(main_bp)

    return app
