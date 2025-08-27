from flask import Flask
from .config import Config
from .routes.main import bp as main_bp

def create_app(config_class: type[Config] = Config) -> Flask:
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Blueprints
    app.register_blueprint(main_bp)

    # config in Jinja verfügbar machen ({{ config.XYZ }})
    @app.context_processor
    def inject_config():
        return dict(config=app.config)

    return app
