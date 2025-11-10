from flask import Flask
from flask_cors import CORS
import logging

def create_app(config_object='cloudone_app.config.Config'):
    """
    Application factory pattern.
    """
    app = Flask(__name__)
    
    # Load configuration from config.py
    app.config.from_object(config_object)
    
    # Initialize CORS
    CORS(app)
    
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    app.logger.setLevel(logging.INFO)
    
    app.logger.info(f"Flask app created with DEBUG={app.config['DEBUG']}")

    # --- Register Blueprints ---
    
    # Import View Blueprint
    from .blueprints.views import views_bp
    app.register_blueprint(views_bp)
    
    # Import ALL new API Blueprints
    from .blueprints.api.account import account_bp
    from .blueprints.api.security import security_bp
    from .blueprints.api.advisor import advisor_bp
    from .blueprints.api.migrate import migrate_bp
    from .blueprints.api.terraform import terraform_bp
    from .blueprints.api.resources import resources_bp

    # Register ALL new API Blueprints
    app.register_blueprint(account_bp)
    app.register_blueprint(security_bp)
    app.register_blueprint(advisor_bp)
    app.register_blueprint(migrate_bp)
    app.register_blueprint(terraform_bp)
    app.register_blueprint(resources_bp)

    return app