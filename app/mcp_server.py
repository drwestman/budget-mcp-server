#!/usr/bin/env python3
"""
Standard MCP Python SDK server implementation for Budget Cash Envelope MCP Server.
This provides stdio transport compatibility while FastMCP handles HTTP transport.
"""
import logging
import os
from typing import Any

import mcp.types as types
from mcp.server.lowlevel import Server
from mcp.server.models import InitializationOptions

from app.config import config
from app.models.database import Database
from app.services.envelope_service import EnvelopeService
from app.services.transaction_service import TransactionService
from app.tools.registry import (
    MCPToolAdapter,
    create_mcp_adapter,
    create_tool_registry,
)

logger = logging.getLogger(__name__)


def create_mcp_server(config_name: str | None = None) -> "MCPServer":
    """
    Factory function to create standard MCP Python SDK server with all tools registered.

    Args:
        config_name (str): Configuration environment
            ('development', 'production', 'testing')

    Returns:
        MCPServer: Configured MCP server instance with all tools registered
    """
    if config_name is None:
        config_name = os.getenv("APP_ENV", "development")

    # Get configuration
    app_config = config[config_name]()

    # Validate MotherDuck configuration
    is_valid, error_msg = app_config.validate_motherduck_config()
    if not is_valid:
        logger.error(f"MotherDuck configuration error: {error_msg}")
        raise ValueError(f"MotherDuck configuration error: {error_msg}")

    # Prepare MotherDuck configuration
    motherduck_config = None
    if app_config.MOTHERDUCK_TOKEN:
        motherduck_config = {
            "token": app_config.MOTHERDUCK_TOKEN,
            "database": app_config.MOTHERDUCK_DATABASE,
        }

    # Initialize database and services with MotherDuck support
    db = Database(
        db_path=app_config.DATABASE_FILE,
        mode=app_config.DATABASE_MODE,
        motherduck_config=motherduck_config,
    )
    envelope_service = EnvelopeService(db)
    transaction_service = TransactionService(db)

    # Create tool registry and adapter
    tool_registry = create_tool_registry(envelope_service, transaction_service)
    mcp_adapter = create_mcp_adapter(tool_registry)

    # Create standard MCP server
    server: Server = Server("budget-envelope-server")

    # Create wrapper class to hold services and provide stdio-compatible interface
    mcp_server = MCPServer(server, db, mcp_adapter)

    return mcp_server


class MCPServer:
    """Wrapper class for standard MCP server with stdio transport compatibility."""

    def __init__(
        self,
        server: Server,
        db: Database,
        adapter: MCPToolAdapter,
    ):
        self.server = server
        self.db = db
        self.adapter = adapter
        self._register_handlers()

    def _register_handlers(self) -> None:
        """Register handlers with the server."""

        @self.server.list_tools()
        async def handle_list_tools() -> list[types.Tool]:
            """List available tools."""
            return self.adapter.get_mcp_tools()

        @self.server.call_tool()
        async def handle_call_tool(
            name: str, arguments: dict[str, Any]
        ) -> list[types.Content]:
            """Handle tool calls."""
            return await self.adapter.handle_tool_call(name, arguments)

    async def run(
        self,
        read_stream: Any,
        write_stream: Any,
        initialization_options: InitializationOptions,
    ) -> None:
        """Run the MCP server."""
        await self.server.run(read_stream, write_stream, initialization_options)

    def create_initialization_options(self) -> InitializationOptions:
        """Create initialization options for the server."""
        return self.server.create_initialization_options()
