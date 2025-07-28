#!/usr/bin/env python3
"""
FastMCP server implementation for Budget Cash Envelope MCP Server.
"""
import json
import logging
import os
from typing import Any

from fastmcp import FastMCP

from app.config import config
from app.models.database import Database
from app.services.envelope_service import EnvelopeService
from app.services.transaction_service import TransactionService
from app.tools.registry import (
    ToolRegistry,
    create_tool_registry,
)

logger = logging.getLogger(__name__)


def _create_authenticated_http_app(original_http_app: Any, bearer_token: str) -> Any:
    """Create authenticated HTTP app using composition instead of monkey-patching."""
    _http_app_instance = None

    def http_app_with_auth(*args: Any, **kwargs: Any) -> Any:
        nonlocal _http_app_instance
        if _http_app_instance is None:
            from app.auth import BearerTokenMiddleware

            _http_app_instance = original_http_app(*args, **kwargs)
            _http_app_instance.add_middleware(
                BearerTokenMiddleware, bearer_token=bearer_token
            )
        return _http_app_instance

    return http_app_with_auth


def _create_initialization_checked_http_app(original_http_app: Any) -> Any:
    """Create HTTP app with MCP initialization check middleware using composition."""
    _http_app_instance = None

    def http_app_with_init_check(*args: Any, **kwargs: Any) -> Any:
        nonlocal _http_app_instance
        if _http_app_instance is None:
            from app.auth import create_mcp_initialization_middleware

            _http_app_instance = original_http_app(*args, **kwargs)
            _http_app_instance.add_middleware(create_mcp_initialization_middleware())
        return _http_app_instance

    return http_app_with_init_check


def _register_fastmcp_tools(mcp: FastMCP, registry: ToolRegistry) -> None:
    """Register tools with FastMCP using individual functions (no **kwargs)."""

    # Envelope tools
    @mcp.tool()
    async def create_envelope(
        category: str,
        budgeted_amount: float,
        starting_balance: float = 0.0,
        description: str = "",
    ) -> str:
        """Create a new budget envelope."""
        result = await registry.call_tool(
            "create_envelope",
            {
                "category": category,
                "budgeted_amount": budgeted_amount,
                "starting_balance": starting_balance,
                "description": description,
            },
        )
        return (
            json.dumps(result, indent=2)
            if isinstance(result, dict | list)
            else str(result)
        )

    @mcp.tool()
    async def list_envelopes() -> str:
        """Get all budget envelopes with their current balances."""
        result = await registry.call_tool("list_envelopes", {})
        return (
            json.dumps(result, indent=2)
            if isinstance(result, dict | list)
            else str(result)
        )

    @mcp.tool()
    async def get_envelope(envelope_id: int) -> str:
        """Get specific envelope details by ID."""
        result = await registry.call_tool("get_envelope", {"envelope_id": envelope_id})
        return (
            json.dumps(result, indent=2)
            if isinstance(result, dict | list)
            else str(result)
        )

    @mcp.tool()
    async def update_envelope(
        envelope_id: int,
        category: str = None,
        budgeted_amount: float = None,
        starting_balance: float = None,
        description: str = None,
    ) -> str:
        """Update an existing envelope's properties."""
        args = {"envelope_id": envelope_id}
        if category is not None:
            args["category"] = category
        if budgeted_amount is not None:
            args["budgeted_amount"] = budgeted_amount
        if starting_balance is not None:
            args["starting_balance"] = starting_balance
        if description is not None:
            args["description"] = description
        result = await registry.call_tool("update_envelope", args)
        return (
            json.dumps(result, indent=2)
            if isinstance(result, dict | list)
            else str(result)
        )

    @mcp.tool()
    async def delete_envelope(envelope_id: int) -> str:
        """Delete an envelope by ID."""
        result = await registry.call_tool(
            "delete_envelope", {"envelope_id": envelope_id}
        )
        return (
            json.dumps(result, indent=2)
            if isinstance(result, dict | list)
            else str(result)
        )

    # Transaction tools
    @mcp.tool()
    async def create_transaction(
        envelope_id: int,
        amount: float,
        description: str,
        type: str,
        date: str = None,
    ) -> str:
        """Create a new transaction."""
        args = {
            "envelope_id": envelope_id,
            "amount": amount,
            "description": description,
            "type": type,
        }
        if date is not None:
            args["date"] = date
        result = await registry.call_tool("create_transaction", args)
        return (
            json.dumps(result, indent=2)
            if isinstance(result, dict | list)
            else str(result)
        )

    @mcp.tool()
    async def list_transactions(envelope_id: int = None) -> str:
        """Get transactions, optionally filtered by envelope."""
        args = {}
        if envelope_id is not None:
            args["envelope_id"] = envelope_id
        result = await registry.call_tool("list_transactions", args)
        return (
            json.dumps(result, indent=2)
            if isinstance(result, dict | list)
            else str(result)
        )

    @mcp.tool()
    async def get_transaction(transaction_id: int) -> str:
        """Get specific transaction details by ID."""
        result = await registry.call_tool(
            "get_transaction", {"transaction_id": transaction_id}
        )
        return (
            json.dumps(result, indent=2)
            if isinstance(result, dict | list)
            else str(result)
        )

    @mcp.tool()
    async def update_transaction(
        transaction_id: int,
        envelope_id: int = None,
        amount: float = None,
        description: str = None,
        type: str = None,
        date: str = None,
    ) -> str:
        """Update an existing transaction's properties."""
        args = {"transaction_id": transaction_id}
        if envelope_id is not None:
            args["envelope_id"] = envelope_id
        if amount is not None:
            args["amount"] = amount
        if description is not None:
            args["description"] = description
        if type is not None:
            args["type"] = type
        if date is not None:
            args["date"] = date
        result = await registry.call_tool("update_transaction", args)
        return (
            json.dumps(result, indent=2)
            if isinstance(result, dict | list)
            else str(result)
        )

    @mcp.tool()
    async def delete_transaction(transaction_id: int) -> str:
        """Delete a transaction by ID."""
        result = await registry.call_tool(
            "delete_transaction", {"transaction_id": transaction_id}
        )
        return (
            json.dumps(result, indent=2)
            if isinstance(result, dict | list)
            else str(result)
        )

    # Utility tools
    @mcp.tool()
    async def get_envelope_balance(envelope_id: int) -> str:
        """Get current balance for specific envelope."""
        result = await registry.call_tool(
            "get_envelope_balance", {"envelope_id": envelope_id}
        )
        return (
            json.dumps(result, indent=2)
            if isinstance(result, dict | list)
            else str(result)
        )

    @mcp.tool()
    async def get_budget_summary() -> str:
        """Get overall budget status and summary."""
        result = await registry.call_tool("get_budget_summary", {})
        return (
            json.dumps(result, indent=2)
            if isinstance(result, dict | list)
            else str(result)
        )

    @mcp.tool()
    async def get_cloud_status() -> str:
        """Get MotherDuck cloud connection status and sync information."""
        result = await registry.call_tool("get_cloud_status", {})
        return (
            json.dumps(result, indent=2)
            if isinstance(result, dict | list)
            else str(result)
        )

    @mcp.tool()
    async def sync_to_cloud() -> str:
        """Synchronize local data to MotherDuck cloud database."""
        result = await registry.call_tool("sync_to_cloud", {})
        return (
            json.dumps(result, indent=2)
            if isinstance(result, dict | list)
            else str(result)
        )

    @mcp.tool()
    async def sync_from_cloud() -> str:
        """Synchronize data from MotherDuck cloud to local database."""
        result = await registry.call_tool("sync_from_cloud", {})
        return (
            json.dumps(result, indent=2)
            if isinstance(result, dict | list)
            else str(result)
        )


def create_fastmcp_server(
    config_name: str | None = None,
    enable_auth: bool = True,
    enable_init_check: bool = True,
) -> FastMCP:
    """
    Factory function to create FastMCP server with all tools registered.

    Args:
        config_name (str): Configuration environment
            ('development', 'production', 'testing')
        enable_auth (bool): Whether to enable bearer token authentication
            for HTTP transport
        enable_init_check (bool): Whether to enable MCP initialization check
            middleware to ensure proper protocol handshake
    Returns:
        FastMCP: Configured FastMCP server instance with middleware properly configured
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

    # Create tool registry
    tool_registry = create_tool_registry(envelope_service, transaction_service)

    # Create FastMCP instance
    mcp = FastMCP("budget-envelope-server")

    # Add service attributes for compatibility with tests and external access
    mcp.envelope_service = envelope_service
    mcp.transaction_service = transaction_service
    mcp.db = db

    # Register tools manually since FastMCP doesn't support **kwargs
    _register_fastmcp_tools(mcp, tool_registry)

    # Add authentication middleware if enabled
    if enable_auth and hasattr(app_config, "BEARER_TOKEN") and app_config.BEARER_TOKEN:
        mcp.http_app = _create_authenticated_http_app(
            mcp.http_app, app_config.BEARER_TOKEN
        )

    # Add MCP initialization check middleware if enabled
    if enable_init_check:
        mcp.http_app = _create_initialization_checked_http_app(mcp.http_app)

    return mcp
