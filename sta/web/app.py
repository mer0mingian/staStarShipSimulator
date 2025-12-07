"""Flask application factory."""

from flask import Flask
from sta.database import init_db


def create_app():
    """Create and configure the Flask application."""
    app = Flask(__name__)
    app.config["SECRET_KEY"] = "sta-simulator-dev-key"

    # Initialize database
    init_db()

    # Register blueprints
    from .routes.main import main_bp
    from .routes.encounters import encounters_bp
    from .routes.api import api_bp
    from .routes.campaigns import campaigns_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(encounters_bp, url_prefix="/encounters")
    app.register_blueprint(api_bp, url_prefix="/api")
    app.register_blueprint(campaigns_bp, url_prefix="/campaigns")

    return app
