"""Flask application factory."""

import os
from flask import Flask
from sta.database import init_db


def create_app():
    """Create and configure the Flask application."""
    app = Flask(__name__)
    app.config["SECRET_KEY"] = "sta-simulator-dev-key"

    upload_folder = os.path.join(app.root_path, "uploads")
    os.makedirs(upload_folder, exist_ok=True)
    app.config["UPLOAD_FOLDER"] = upload_folder
    app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024

    # Initialize database
    init_db()

    # Register blueprints
    from .routes.main import main_bp
    from .routes.encounters import encounters_bp
    from .routes.api import api_bp
    from .routes.campaigns import campaigns_bp
    from .routes.scenes import scenes_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(encounters_bp, url_prefix="/encounters")
    app.register_blueprint(api_bp, url_prefix="/api")
    app.register_blueprint(campaigns_bp, url_prefix="/campaigns")
    app.register_blueprint(scenes_bp, url_prefix="/scenes")

    return app
