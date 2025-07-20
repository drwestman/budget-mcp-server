import os
from mcp.server import Server

from app.config import config
from app.models.database import Database
from app.services.envelope_service import EnvelopeService
from app.services.transaction_service import TransactionService

# Explicitly import the tool modules first to ensure @register decorators run
import app.mcp.envelope_tools
import app.mcp.transaction_tools
import app.mcp.utility_tools

# Then import the classes and the registration utilities
from app.mcp.envelope_tools import EnvelopeTools
from app.mcp.transaction_tools import TransactionTools
from app.mcp.utility_tools import UtilityTools
from app.mcp.registry import register_all_tools  # Import the new registration function
from app.mcp.registry import TOOL_REGISTRY  # For debugging


def create_mcp_server(config_name=None):
    """
    Application factory pattern for creating MCP server instances.
    Args:
        config_name (str): Configuration environment ('development', 'production', 'testing')
    Returns:
        Server: Configured MCP server instance
    """
    if config_name is None:
        config_name = os.getenv("APP_ENV", "default")

    # Get configuration
    app_config = config[config_name]()

    # Initialize database and services
    db = Database(app_config.DATABASE_FILE)
    envelope_service = EnvelopeService(db)
    transaction_service = TransactionService(db)

    # Create MCP server
    server = Server("budget-envelope-server")

    # Initialize tool classes.
    # Importing these classes (as done above) executes their respective modules,
    # which in turn executes the @register decorators, populating TOOL_REGISTRY.
    envelope_tools_instance = EnvelopeTools(envelope_service)
    transaction_tools_instance = TransactionTools(transaction_service)
    utility_tools_instance = UtilityTools(envelope_service, transaction_service, db)

    # Register all tools from the TOOL_REGISTRY.
    # Pass all instances that contain registered methods.
    # register_all_tools will bind methods from TOOL_REGISTRY to these instances.
    all_tool_instances = [
        envelope_tools_instance,
        transaction_tools_instance,
        utility_tools_instance,
    ]

    register_all_tools(server, all_tool_instances)

    # Store database instance for cleanup if needed
    server.db = db

    return server
