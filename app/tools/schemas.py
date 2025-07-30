#!/usr/bin/env python3
"""
Shared tool schemas for Budget Cash Envelope MCP Server.
This module defines all tool schemas in one place to eliminate duplication.
"""

from typing import Any

# Envelope tool schemas
ENVELOPE_TOOLS_SCHEMAS: dict[str, dict[str, Any]] = {
    "create_envelope": {
        "name": "create_envelope",
        "description": "Create a new budget envelope.",
        "inputSchema": {
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
    },
    "list_envelopes": {
        "name": "list_envelopes",
        "description": "Get all budget envelopes with their current balances.",
        "inputSchema": {"type": "object", "properties": {}, "required": []},
    },
    "get_envelope": {
        "name": "get_envelope",
        "description": "Get specific envelope details by ID.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "envelope_id": {
                    "type": "integer",
                    "description": "ID of the envelope to retrieve",
                }
            },
            "required": ["envelope_id"],
        },
    },
    "update_envelope": {
        "name": "update_envelope",
        "description": "Update an existing envelope's properties.",
        "inputSchema": {
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
    },
    "delete_envelope": {
        "name": "delete_envelope",
        "description": "Delete an envelope by ID.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "envelope_id": {
                    "type": "integer",
                    "description": "ID of the envelope to delete",
                }
            },
            "required": ["envelope_id"],
        },
    },
}

# Transaction tool schemas
TRANSACTION_TOOLS_SCHEMAS: dict[str, dict[str, Any]] = {
    "create_transaction": {
        "name": "create_transaction",
        "description": "Create a new transaction.",
        "inputSchema": {
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
                        "Transaction date in YYYY-MM-DD format. Defaults to "
                        "current date"
                    ),
                },
            },
            "required": ["envelope_id", "amount", "description", "type"],
        },
    },
    "list_transactions": {
        "name": "list_transactions",
        "description": "Get transactions, optionally filtered by envelope.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "envelope_id": {
                    "type": "integer",
                    "description": "Filter transactions by envelope ID (optional)",
                }
            },
            "required": [],
        },
    },
    "get_transaction": {
        "name": "get_transaction",
        "description": "Get specific transaction details by ID.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "transaction_id": {
                    "type": "integer",
                    "description": "ID of the transaction to retrieve",
                }
            },
            "required": ["transaction_id"],
        },
    },
    "update_transaction": {
        "name": "update_transaction",
        "description": "Update an existing transaction's properties.",
        "inputSchema": {
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
    },
    "delete_transaction": {
        "name": "delete_transaction",
        "description": "Delete a transaction by ID.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "transaction_id": {
                    "type": "integer",
                    "description": "ID of the transaction to delete",
                }
            },
            "required": ["transaction_id"],
        },
    },
}

# Utility tool schemas
UTILITY_TOOLS_SCHEMAS: dict[str, dict[str, Any]] = {
    "get_envelope_balance": {
        "name": "get_envelope_balance",
        "description": "Get current balance for specific envelope.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "envelope_id": {
                    "type": "integer",
                    "description": "ID of the envelope",
                }
            },
            "required": ["envelope_id"],
        },
    },
    "get_budget_summary": {
        "name": "get_budget_summary",
        "description": "Get overall budget status and summary.",
        "inputSchema": {"type": "object", "properties": {}, "required": []},
    },
    "get_cloud_status": {
        "name": "get_cloud_status",
        "description": "Get MotherDuck cloud connection status and sync information.",
        "inputSchema": {"type": "object", "properties": {}, "required": []},
    },
    "sync_to_cloud": {
        "name": "sync_to_cloud",
        "description": "Synchronize local data to MotherDuck cloud database.",
        "inputSchema": {"type": "object", "properties": {}, "required": []},
    },
    "sync_from_cloud": {
        "name": "sync_from_cloud",
        "description": "Synchronize data from MotherDuck cloud to local database.",
        "inputSchema": {"type": "object", "properties": {}, "required": []},
    },
}

# Combined schemas for easy access
ALL_TOOL_SCHEMAS: dict[str, dict[str, Any]] = {
    **ENVELOPE_TOOLS_SCHEMAS,
    **TRANSACTION_TOOLS_SCHEMAS,
    **UTILITY_TOOLS_SCHEMAS,
}


def get_tool_schema(tool_name: str) -> dict[str, Any]:
    """Get schema for a specific tool."""
    if tool_name not in ALL_TOOL_SCHEMAS:
        raise ValueError(f"Unknown tool: {tool_name}")
    return ALL_TOOL_SCHEMAS[tool_name]


def get_envelope_tool_schemas() -> dict[str, dict[str, Any]]:
    """Get all envelope tool schemas."""
    return ENVELOPE_TOOLS_SCHEMAS


def get_transaction_tool_schemas() -> dict[str, dict[str, Any]]:
    """Get all transaction tool schemas."""
    return TRANSACTION_TOOLS_SCHEMAS


def get_utility_tool_schemas() -> dict[str, dict[str, Any]]:
    """Get all utility tool schemas."""
    return UTILITY_TOOLS_SCHEMAS


def get_all_tool_schemas() -> dict[str, dict[str, Any]]:
    """Get all tool schemas."""
    return ALL_TOOL_SCHEMAS
