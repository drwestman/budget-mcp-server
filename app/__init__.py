import os
from flask import Flask, jsonify

from app.config import config
from app.models.database import Database
from app.services.envelope_service import EnvelopeService
from app.services.transaction_service import TransactionService
from app.api.envelopes import envelopes_bp, init_envelope_service
from app.api.transactions import transactions_bp, init_transaction_service
from app.utils.auth import require_api_key
from app.utils.error_handlers import register_error_handlers


def create_app(config_name=None):
    """
    Application factory pattern for creating Flask app instances.
    Args:
        config_name (str): Configuration environment ('development', 'production', 'testing')
    Returns:
        Flask: Configured Flask application instance
    """
    if config_name is None:
        config_name = os.getenv('FLASK_ENV', 'default')
    
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    
    # Initialize database and services
    db = Database(app.config['DATABASE_FILE'])
    envelope_service = EnvelopeService(db)
    transaction_service = TransactionService(db)
    
    # Initialize services in blueprints
    init_envelope_service(envelope_service)
    init_transaction_service(transaction_service)
    
    # Register blueprints
    app.register_blueprint(envelopes_bp, url_prefix='/envelopes')
    app.register_blueprint(transactions_bp, url_prefix='/transactions')
    
    # Apply API key protection to all routes in the blueprints
    api_key_decorator = require_api_key(app.config['API_KEY'])
    for rule in app.url_map.iter_rules():
        if rule.endpoint.startswith('envelopes.') or rule.endpoint.startswith('transactions.'):
            view_func = app.view_functions[rule.endpoint]
            app.view_functions[rule.endpoint] = api_key_decorator(view_func)
    
    # Register error handlers
    register_error_handlers(app)
    
    # Health check endpoint (not protected by API key)
    @app.route('/health', methods=['GET'])
    def health_check():
        """Simple health check endpoint."""
        return jsonify({"status": "ok", "message": "API is running."}), 200
    
    # Store database instance for cleanup if needed
    app.db = db
    
    return app