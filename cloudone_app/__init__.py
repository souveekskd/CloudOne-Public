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
    
    # Import ALL new API Blueprints from the 'api' package
    from .blueprints.api.account import account_bp
    from .blueprints.api.security import security_bp
    from .blueprints.api.advisor import advisor_bp
    from .blueprints.api.migrate import migrate_bp
    # from .blueprints.api.terraform import terraform_bp  <-- REMOVE THIS
    from .blueprints.api.resources import resources_bp
    from .blueprints.api.ai import ai_bp
    from .blueprints.api.policy import policy_bp
    from .blueprints.api.carbon import carbon_bp
    from .blueprints.api.dashboard import dashboard_bp
    from .blueprints.api.monitoring import monitoring_bp
    from .blueprints.api.iac import iac_bp # <-- ADD THIS

    # Register ALL new API Blueprints
    app.register_blueprint(account_bp)
    app.register_blueprint(security_bp)
    app.register_blueprint(advisor_bp)
    app.register_blueprint(migrate_bp)
    # app.register_blueprint(terraform_bp) # <-- REMOVE THIS
    app.register_blueprint(resources_bp)
    app.register_blueprint(ai_bp)
    app.register_blueprint(policy_bp)
    app.register_blueprint(carbon_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(monitoring_bp)
    app.register_blueprint(iac_bp) # <-- ADD THIS

    return app