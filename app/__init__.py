import os
from mcp.server import Server

from app.config import config
from app.models.database import Database
from app.services.envelope_service import EnvelopeService
from app.services.transaction_service import TransactionService
from app.mcp.envelope_tools import EnvelopeTools
from app.mcp.transaction_tools import TransactionTools
from app.mcp.utility_tools import UtilityTools


def create_mcp_server(config_name=None):
    """
    Application factory pattern for creating MCP server instances.
    Args:
        config_name (str): Configuration environment ('development', 'production', 'testing')
    Returns:
        Server: Configured MCP server instance
    """
    if config_name is None:
        config_name = os.getenv('APP_ENV', 'default')
    
    # Get configuration
    app_config = config[config_name]()
    
    # Initialize database and services
    db = Database(app_config.DATABASE_FILE)
    envelope_service = EnvelopeService(db)
    transaction_service = TransactionService(db)
    
    # Create MCP server
    server = Server("budget-envelope-server")
    
    # Initialize and register MCP tools
    envelope_tools = EnvelopeTools(envelope_service)
    transaction_tools = TransactionTools(transaction_service)
    utility_tools = UtilityTools(envelope_service, transaction_service, db)
    
    envelope_tools.register_tools(server)
    transaction_tools.register_tools(server)
    utility_tools.register_tools(server)
    
    # Store database instance for cleanup if needed
    server.db = db
    
    return server