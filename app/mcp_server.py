#!/usr/bin/env python3
"""
Standard MCP Python SDK server implementation for Budget Cash Envelope MCP Server.
This provides stdio transport compatibility while FastMCP handles HTTP transport.
"""
import json
import logging
import os
from typing import Any

import mcp.types as types
from mcp.server.lowlevel import NotificationOptions, Server
from mcp.server.models import InitializationOptions

from app.config import config
from app.models.database import Database
from app.services.envelope_service import EnvelopeService
from app.services.transaction_service import TransactionService

logger = logging.getLogger(__name__)


def _create_envelope_tools(
    envelope_service: EnvelopeService,
) -> tuple[list[types.Tool], dict[str, Any]]:
    """Create envelope management tools and handlers."""

    tools = [
        types.Tool(
            name="create_envelope",
            description="Create a new budget envelope.",
            inputSchema={
                "type": "object",
                "properties": {
                    "category": {
                        "type": "string",
                        "description": "Name/category of the envelope (must be unique)",
                    },
                    "budgeted_amount": {
                        "type": "number",
                        "description": (
                            "Planned budget amount for this envelope (must be positive)"
                        ),
                    },
                    "starting_balance": {
                        "type": "number",
                        "description": (
                            "Initial balance for the envelope. Defaults to 0.0"
                        ),
                        "default": 0.0,
                    },
                    "description": {
                        "type": "string",
                        "description": (
                            "Optional description providing additional context about the "
                            "envelope's purpose. Defaults to empty string"
                        ),
                        "default": "",
                    },
                },
                "required": ["category", "budgeted_amount"],
            },
        ),
        types.Tool(
            name="list_envelopes",
            description="Get all budget envelopes with their current balances.",
            inputSchema={"type": "object", "properties": {}, "required": []},
        ),
        types.Tool(
            name="get_envelope",
            description="Get specific envelope details by ID.",
            inputSchema={
                "type": "object",
                "properties": {
                    "envelope_id": {
                        "type": "integer",
                        "description": "ID of the envelope to retrieve",
                    }
                },
                "required": ["envelope_id"],
            },
        ),
        types.Tool(
            name="update_envelope",
            description="Update an existing envelope's properties.",
            inputSchema={
                "type": "object",
                "properties": {
                    "envelope_id": {
                        "type": "integer",
                        "description": "ID of the envelope to update",
                    },
                    "category": {
                        "type": "string",
                        "description": "New category name (optional)",
                    },
                    "budgeted_amount": {
                        "type": "number",
                        "description": "New budgeted amount (optional)",
                    },
                    "starting_balance": {
                        "type": "number",
                        "description": "New starting balance (optional)",
                    },
                    "description": {
                        "type": "string",
                        "description": "New description (optional)",
                    },
                },
                "required": ["envelope_id"],
            },
        ),
        types.Tool(
            name="delete_envelope",
            description="Delete an envelope by ID.",
            inputSchema={
                "type": "object",
                "properties": {
                    "envelope_id": {
                        "type": "integer",
                        "description": "ID of the envelope to delete",
                    }
                },
                "required": ["envelope_id"],
            },
        ),
    ]

    handlers = {
        "create_envelope": _handle_create_envelope,
        "list_envelopes": _handle_list_envelopes,
        "get_envelope": _handle_get_envelope,
        "update_envelope": _handle_update_envelope,
        "delete_envelope": _handle_delete_envelope,
    }

    return tools, handlers


def _create_transaction_tools(
    transaction_service: TransactionService,
) -> tuple[list[types.Tool], dict[str, Any]]:
    """Create transaction management tools and handlers."""

    tools = [
        types.Tool(
            name="create_transaction",
            description="Create a new transaction.",
            inputSchema={
                "type": "object",
                "properties": {
                    "envelope_id": {
                        "type": "integer",
                        "description": "ID of the envelope this transaction belongs to",
                    },
                    "amount": {
                        "type": "number",
                        "description": (
                            "Transaction amount (positive for income, negative for expense)"
                        ),
                    },
                    "description": {
                        "type": "string",
                        "description": "Description of the transaction",
                    },
                    "type": {
                        "type": "string",
                        "description": "Type of transaction: 'income' or 'expense'",
                    },
                    "date": {
                        "type": "string",
                        "description": (
                            "Transaction date in YYYY-MM-DD format. Defaults to current date"
                        ),
                    },
                },
                "required": ["envelope_id", "amount", "description", "type"],
            },
        ),
        types.Tool(
            name="list_transactions",
            description="Get transactions, optionally filtered by envelope.",
            inputSchema={
                "type": "object",
                "properties": {
                    "envelope_id": {
                        "type": "integer",
                        "description": "Filter transactions by envelope ID (optional)",
                    }
                },
                "required": [],
            },
        ),
        types.Tool(
            name="get_transaction",
            description="Get specific transaction details by ID.",
            inputSchema={
                "type": "object",
                "properties": {
                    "transaction_id": {
                        "type": "integer",
                        "description": "ID of the transaction to retrieve",
                    }
                },
                "required": ["transaction_id"],
            },
        ),
        types.Tool(
            name="update_transaction",
            description="Update an existing transaction's properties.",
            inputSchema={
                "type": "object",
                "properties": {
                    "transaction_id": {
                        "type": "integer",
                        "description": "ID of the transaction to update",
                    },
                    "envelope_id": {
                        "type": "integer",
                        "description": "New envelope ID (optional)",
                    },
                    "amount": {
                        "type": "number",
                        "description": "New amount (optional)",
                    },
                    "description": {
                        "type": "string",
                        "description": "New description (optional)",
                    },
                    "type": {
                        "type": "string",
                        "description": "New type: 'income' or 'expense' (optional)",
                    },
                    "date": {
                        "type": "string",
                        "description": "New date in YYYY-MM-DD format (optional)",
                    },
                },
                "required": ["transaction_id"],
            },
        ),
        types.Tool(
            name="delete_transaction",
            description="Delete a transaction by ID.",
            inputSchema={
                "type": "object",
                "properties": {
                    "transaction_id": {
                        "type": "integer",
                        "description": "ID of the transaction to delete",
                    }
                },
                "required": ["transaction_id"],
            },
        ),
    ]

    handlers = {
        "create_transaction": _handle_create_transaction,
        "list_transactions": _handle_list_transactions,
        "get_transaction": _handle_get_transaction,
        "update_transaction": _handle_update_transaction,
        "delete_transaction": _handle_delete_transaction,
    }

    return tools, handlers


def _create_utility_tools(
    envelope_service: EnvelopeService,
) -> tuple[list[types.Tool], dict[str, Any]]:
    """Create utility tools and handlers."""

    tools = [
        types.Tool(
            name="get_envelope_balance",
            description="Get current balance for specific envelope.",
            inputSchema={
                "type": "object",
                "properties": {
                    "envelope_id": {
                        "type": "integer",
                        "description": "ID of the envelope",
                    }
                },
                "required": ["envelope_id"],
            },
        ),
        types.Tool(
            name="get_budget_summary",
            description="Get overall budget status and summary.",
            inputSchema={"type": "object", "properties": {}, "required": []},
        ),
        types.Tool(
            name="get_cloud_status",
            description="Get MotherDuck cloud connection status and sync information.",
            inputSchema={"type": "object", "properties": {}, "required": []},
        ),
        types.Tool(
            name="sync_to_cloud",
            description="Synchronize local data to MotherDuck cloud database.",
            inputSchema={"type": "object", "properties": {}, "required": []},
        ),
        types.Tool(
            name="sync_from_cloud",
            description="Synchronize data from MotherDuck cloud to local database.",
            inputSchema={"type": "object", "properties": {}, "required": []},
        ),
    ]

    handlers = {
        "get_envelope_balance": _handle_get_envelope_balance,
        "get_budget_summary": _handle_get_budget_summary,
        "get_cloud_status": _handle_get_cloud_status,
        "sync_to_cloud": _handle_sync_to_cloud,
        "sync_from_cloud": _handle_sync_from_cloud,
    }

    return tools, handlers


# Tool handler functions (envelope tools)
async def _handle_create_envelope(
    envelope_service: EnvelopeService, arguments: dict[str, Any]
) -> list[types.Content]:
    """Handle create_envelope tool call."""
    try:
        category = arguments["category"]
        budgeted_amount = arguments["budgeted_amount"]
        starting_balance = arguments.get("starting_balance", 0.0)
        description = arguments.get("description", "")

        envelope = envelope_service.create_envelope(
            category, budgeted_amount, starting_balance, description
        )
        return [types.TextContent(type="text", text=json.dumps(envelope, indent=2))]
    except ValueError as e:
        return [types.TextContent(type="text", text=f"Error: {str(e)}")]
    except (TypeError, KeyError, AttributeError) as e:
        return [
            types.TextContent(
                type="text", text=f"Internal error: Data processing error: {str(e)}"
            )
        ]
    except Exception:
        logger.exception("An unexpected error occurred in create_envelope")
        return [
            types.TextContent(
                type="text",
                text=(
                    "Internal error: An unexpected error occurred. "
                    "Please contact support if the issue persists."
                ),
            )
        ]


async def _handle_list_envelopes(
    envelope_service: EnvelopeService, arguments: dict[str, Any]
) -> list[types.Content]:
    """Handle list_envelopes tool call."""
    try:
        envelopes = envelope_service.get_all_envelopes()
        return [types.TextContent(type="text", text=json.dumps(envelopes, indent=2))]
    except (TypeError, KeyError, AttributeError) as e:
        return [
            types.TextContent(
                type="text", text=f"Internal error: Data processing error: {str(e)}"
            )
        ]
    except Exception as e:
        return [
            types.TextContent(
                type="text",
                text=f"Internal error: An unexpected error occurred: {str(e)}",
            )
        ]


async def _handle_get_envelope(
    envelope_service: EnvelopeService, arguments: dict[str, Any]
) -> list[types.Content]:
    """Handle get_envelope tool call."""
    try:
        envelope_id = arguments["envelope_id"]
        envelope = envelope_service.get_envelope(envelope_id)
        if not envelope:
            return [types.TextContent(type="text", text="Error: Envelope not found")]
        return [types.TextContent(type="text", text=json.dumps(envelope, indent=2))]
    except (TypeError, KeyError, AttributeError) as e:
        return [
            types.TextContent(
                type="text", text=f"Internal error: Data processing error: {str(e)}"
            )
        ]
    except Exception as e:
        return [
            types.TextContent(
                type="text",
                text=f"Internal error: An unexpected error occurred: {str(e)}",
            )
        ]


async def _handle_update_envelope(
    envelope_service: EnvelopeService, arguments: dict[str, Any]
) -> list[types.Content]:
    """Handle update_envelope tool call."""
    try:
        envelope_id = arguments["envelope_id"]
        category = arguments.get("category")
        budgeted_amount = arguments.get("budgeted_amount")
        starting_balance = arguments.get("starting_balance")
        description = arguments.get("description")

        envelope = envelope_service.update_envelope(
            envelope_id, category, budgeted_amount, starting_balance, description
        )
        return [types.TextContent(type="text", text=json.dumps(envelope, indent=2))]
    except ValueError as e:
        return [types.TextContent(type="text", text=f"Error: {str(e)}")]
    except (TypeError, KeyError, AttributeError) as e:
        return [
            types.TextContent(
                type="text", text=f"Internal error: Data processing error: {str(e)}"
            )
        ]
    except Exception as e:
        return [
            types.TextContent(
                type="text",
                text=f"Internal error: An unexpected error occurred: {str(e)}",
            )
        ]


async def _handle_delete_envelope(
    envelope_service: EnvelopeService, arguments: dict[str, Any]
) -> list[types.Content]:
    """Handle delete_envelope tool call."""
    try:
        envelope_id = arguments["envelope_id"]
        result = envelope_service.delete_envelope(envelope_id)
        return [types.TextContent(type="text", text=json.dumps(result, indent=2))]
    except ValueError as e:
        return [types.TextContent(type="text", text=f"Error: {str(e)}")]
    except (TypeError, KeyError, AttributeError) as e:
        return [
            types.TextContent(
                type="text", text=f"Internal error: Data processing error: {str(e)}"
            )
        ]
    except Exception as e:
        return [
            types.TextContent(
                type="text",
                text=f"Internal error: An unexpected error occurred: {str(e)}",
            )
        ]


# Tool handler functions (transaction tools)
async def _handle_create_transaction(
    transaction_service: TransactionService, arguments: dict[str, Any]
) -> list[types.Content]:
    """Handle create_transaction tool call."""
    try:
        envelope_id = arguments["envelope_id"]
        amount = arguments["amount"]
        description = arguments["description"]
        transaction_type = arguments["type"]
        date = arguments.get("date")

        # Use current date if not provided
        if date is None:
            from datetime import datetime

            date = datetime.now().strftime("%Y-%m-%d")

        transaction = transaction_service.create_transaction(
            envelope_id, amount, description, date, transaction_type
        )
        return [types.TextContent(type="text", text=json.dumps(transaction, indent=2))]
    except ValueError as e:
        return [types.TextContent(type="text", text=f"Error: {str(e)}")]
    except (TypeError, KeyError, AttributeError) as e:
        return [
            types.TextContent(
                type="text", text=f"Internal error: Data processing error: {str(e)}"
            )
        ]
    except Exception:
        logger.exception("An unexpected error occurred in create_transaction")
        return [
            types.TextContent(
                type="text",
                text=(
                    "Internal error: An unexpected error occurred. "
                    "Please contact support if the issue persists."
                ),
            )
        ]


async def _handle_list_transactions(
    transaction_service: TransactionService, arguments: dict[str, Any]
) -> list[types.Content]:
    """Handle list_transactions tool call."""
    try:
        envelope_id = arguments.get("envelope_id")
        transactions = (
            transaction_service.get_transactions_by_envelope(envelope_id)
            if envelope_id
            else transaction_service.get_all_transactions()
        )
        return [types.TextContent(type="text", text=json.dumps(transactions, indent=2))]
    except (TypeError, KeyError, AttributeError) as e:
        return [
            types.TextContent(
                type="text", text=f"Internal error: Data processing error: {str(e)}"
            )
        ]
    except Exception as e:
        return [
            types.TextContent(
                type="text",
                text=f"Internal error: An unexpected error occurred: {str(e)}",
            )
        ]


async def _handle_get_transaction(
    transaction_service: TransactionService, arguments: dict[str, Any]
) -> list[types.Content]:
    """Handle get_transaction tool call."""
    try:
        transaction_id = arguments["transaction_id"]
        transaction = transaction_service.get_transaction(transaction_id)
        if not transaction:
            return [types.TextContent(type="text", text="Error: Transaction not found")]
        return [types.TextContent(type="text", text=json.dumps(transaction, indent=2))]
    except (TypeError, KeyError, AttributeError) as e:
        return [
            types.TextContent(
                type="text", text=f"Internal error: Data processing error: {str(e)}"
            )
        ]
    except Exception as e:
        return [
            types.TextContent(
                type="text",
                text=f"Internal error: An unexpected error occurred: {str(e)}",
            )
        ]


async def _handle_update_transaction(
    transaction_service: TransactionService, arguments: dict[str, Any]
) -> list[types.Content]:
    """Handle update_transaction tool call."""
    try:
        transaction_id = arguments["transaction_id"]
        envelope_id = arguments.get("envelope_id")
        amount = arguments.get("amount")
        description = arguments.get("description")
        date = arguments.get("date")
        transaction_type = arguments.get("type")

        transaction = transaction_service.update_transaction(
            transaction_id, envelope_id, amount, description, date, transaction_type
        )
        return [types.TextContent(type="text", text=json.dumps(transaction, indent=2))]
    except ValueError as e:
        return [types.TextContent(type="text", text=f"Error: {str(e)}")]
    except (TypeError, KeyError, AttributeError) as e:
        return [
            types.TextContent(
                type="text", text=f"Internal error: Data processing error: {str(e)}"
            )
        ]
    except Exception as e:
        return [
            types.TextContent(
                type="text",
                text=f"Internal error: An unexpected error occurred: {str(e)}",
            )
        ]


async def _handle_delete_transaction(
    transaction_service: TransactionService, arguments: dict[str, Any]
) -> list[types.Content]:
    """Handle delete_transaction tool call."""
    try:
        transaction_id = arguments["transaction_id"]
        result = transaction_service.delete_transaction(transaction_id)
        return [types.TextContent(type="text", text=json.dumps(result, indent=2))]
    except ValueError as e:
        return [types.TextContent(type="text", text=f"Error: {str(e)}")]
    except (TypeError, KeyError, AttributeError) as e:
        return [
            types.TextContent(
                type="text", text=f"Internal error: Data processing error: {str(e)}"
            )
        ]
    except Exception as e:
        return [
            types.TextContent(
                type="text",
                text=f"Internal error: An unexpected error occurred: {str(e)}",
            )
        ]


# Tool handler functions (utility tools)
async def _handle_get_envelope_balance(
    envelope_service: EnvelopeService, arguments: dict[str, Any]
) -> list[types.Content]:
    """Handle get_envelope_balance tool call."""
    try:
        envelope_id = arguments["envelope_id"]
        balance = envelope_service.get_envelope_balance(envelope_id)
        return [types.TextContent(type="text", text=json.dumps(balance, indent=2))]
    except ValueError as e:
        return [types.TextContent(type="text", text=f"Error: {str(e)}")]
    except (TypeError, KeyError, AttributeError) as e:
        return [
            types.TextContent(
                type="text", text=f"Internal error: Data processing error: {str(e)}"
            )
        ]
    except Exception as e:
        return [
            types.TextContent(
                type="text",
                text=f"Internal error: An unexpected error occurred: {str(e)}",
            )
        ]


async def _handle_get_budget_summary(
    envelope_service: EnvelopeService, arguments: dict[str, Any]
) -> list[types.Content]:
    """Handle get_budget_summary tool call."""
    try:
        # Get all envelopes with balances
        envelopes = envelope_service.get_all_envelopes()

        # Calculate totals
        total_budget = sum(env.get("budgeted_amount", 0) for env in envelopes)
        total_balance = sum(env.get("current_balance", 0) for env in envelopes)
        total_starting_balance = sum(
            env.get("starting_balance", 0) for env in envelopes
        )
        total_spent = total_starting_balance - total_balance

        summary = {
            "total_envelopes": len(envelopes),
            "total_budgeted": total_budget,
            "total_current_balance": total_balance,
            "total_spent": total_spent,
            "envelopes": envelopes,
        }
        return [types.TextContent(type="text", text=json.dumps(summary, indent=2))]
    except (TypeError, KeyError, AttributeError) as e:
        return [
            types.TextContent(
                type="text", text=f"Internal error: Data processing error: {str(e)}"
            )
        ]
    except Exception as e:
        return [
            types.TextContent(
                type="text",
                text=f"Internal error: An unexpected error occurred: {str(e)}",
            )
        ]


async def _handle_get_cloud_status(
    envelope_service: EnvelopeService, arguments: dict[str, Any]
) -> list[types.Content]:
    """Handle get_cloud_status tool call."""
    try:
        status = envelope_service.db.get_connection_status()
        sync_status = envelope_service.db.get_sync_status()

        result = {"connection": status, "sync": sync_status}
        return [types.TextContent(type="text", text=json.dumps(result, indent=2))]
    except Exception as e:
        return [
            types.TextContent(
                type="text",
                text=f"Internal error: An unexpected error occurred: {str(e)}",
            )
        ]


async def _handle_sync_to_cloud(
    envelope_service: EnvelopeService, arguments: dict[str, Any]
) -> list[types.Content]:
    """Handle sync_to_cloud tool call."""
    try:
        results = envelope_service.db.sync_to_cloud()
        return [types.TextContent(type="text", text=json.dumps(results, indent=2))]
    except ValueError as e:
        return [types.TextContent(type="text", text=f"Error: {str(e)}")]
    except Exception as e:
        return [
            types.TextContent(
                type="text",
                text=f"Internal error: An unexpected error occurred: {str(e)}",
            )
        ]


async def _handle_sync_from_cloud(
    envelope_service: EnvelopeService, arguments: dict[str, Any]
) -> list[types.Content]:
    """Handle sync_from_cloud tool call."""
    try:
        results = envelope_service.db.sync_from_cloud()
        return [types.TextContent(type="text", text=json.dumps(results, indent=2))]
    except ValueError as e:
        return [types.TextContent(type="text", text=f"Error: {str(e)}")]
    except Exception as e:
        return [
            types.TextContent(
                type="text",
                text=f"Internal error: An unexpected error occurred: {str(e)}",
            )
        ]


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

    # Create standard MCP server
    server: Server = Server("budget-envelope-server")

    # Create wrapper class to hold services and provide stdio-compatible interface
    mcp_server = MCPServer(server, db, envelope_service, transaction_service)

    return mcp_server


class MCPServer:
    """Wrapper class for standard MCP server with stdio transport compatibility."""

    def __init__(
        self,
        server: Server,
        db: Database,
        envelope_service: EnvelopeService,
        transaction_service: TransactionService,
    ):
        self.server = server
        self.db = db
        self.envelope_service = envelope_service
        self.transaction_service = transaction_service
        self._all_tools: list[types.Tool] = []
        self._tool_handlers: dict[str, Any] = {}

        self._register_all_tools()

    def _register_all_tools(self) -> None:
        """Register all tools with the server."""
        # Get envelope tools
        envelope_tools, envelope_handlers = _create_envelope_tools(
            self.envelope_service
        )
        self._all_tools.extend(envelope_tools)
        self._tool_handlers.update(envelope_handlers)

        # Get transaction tools
        transaction_tools, transaction_handlers = _create_transaction_tools(
            self.transaction_service
        )
        self._all_tools.extend(transaction_tools)
        self._tool_handlers.update(transaction_handlers)

        # Get utility tools
        utility_tools, utility_handlers = _create_utility_tools(self.envelope_service)
        self._all_tools.extend(utility_tools)
        self._tool_handlers.update(utility_handlers)

        # Register handlers with the server
        @self.server.list_tools()
        async def handle_list_tools() -> list[types.Tool]:
            """List available tools."""
            return self._all_tools

        @self.server.call_tool()
        async def handle_call_tool(
            name: str, arguments: dict[str, Any]
        ) -> list[types.Content]:
            """Handle tool calls."""
            if name not in self._tool_handlers:
                raise ValueError(f"Unknown tool: {name}")

            handler = self._tool_handlers[name]

            # Call the appropriate handler based on tool category
            if name in [
                "create_envelope",
                "list_envelopes",
                "get_envelope",
                "update_envelope",
                "delete_envelope",
                "get_envelope_balance",
                "get_budget_summary",
                "get_cloud_status",
                "sync_to_cloud",
                "sync_from_cloud",
            ]:
                return await handler(self.envelope_service, arguments)
            else:
                return await handler(self.transaction_service, arguments)

    async def run(
        self, read_stream: Any, write_stream: Any, initialization_options: Any
    ) -> None:
        """Run the MCP server with stdio transport."""
        await self.server.run(read_stream, write_stream, initialization_options)

    def create_initialization_options(self) -> InitializationOptions:
        """Create initialization options for the server."""
        return InitializationOptions(
            server_name="budget-envelope-server",
            server_version="0.1.0",
            capabilities=self.server.get_capabilities(
                notification_options=NotificationOptions(),
                experimental_capabilities={},
            ),
        )
