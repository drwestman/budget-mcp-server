#!/usr/bin/env python3
"""
FastMCP server implementation for Budget Cash Envelope MCP Server.
"""
import os
import logging
import json
from typing import Optional, Annotated
from fastmcp import FastMCP

from app.config import config
from app.models.database import Database
from app.services.envelope_service import EnvelopeService
from app.services.transaction_service import TransactionService

logger = logging.getLogger(__name__)


def _configure_authentication(mcp: FastMCP, app_config, enable_auth: bool):
    """Configure bearer token authentication middleware if enabled."""
    if enable_auth and app_config.BEARER_TOKEN:
        from app.auth import BearerTokenMiddleware

        # Create a wrapper function to add middleware when the HTTP app is first accessed
        original_http_app = mcp.http_app
        _http_app_instance = None

        def http_app_with_auth(*args, **kwargs):
            nonlocal _http_app_instance
            if _http_app_instance is None:
                _http_app_instance = original_http_app(*args, **kwargs)
                _http_app_instance.add_middleware(
                    BearerTokenMiddleware, bearer_token=app_config.BEARER_TOKEN
                )
            return _http_app_instance

        # Replace the http_app method to ensure consistent instance with middleware
        mcp.http_app = http_app_with_auth


def _register_envelope_tools(mcp: FastMCP, envelope_service: EnvelopeService):
    """Register all envelope management tools."""

    @mcp.tool()
    async def create_envelope(
        category: Annotated[str, "Name/category of the envelope (must be unique)"],
        budgeted_amount: Annotated[
            float, "Planned budget amount for this envelope (must be positive)"
        ],
        starting_balance: Annotated[
            Optional[float], "Initial balance for the envelope. Defaults to 0.0"
        ] = 0.0,
        description: Annotated[
            Optional[str],
            "Optional description providing additional context about the envelope's purpose. Defaults to empty string",
        ] = "",
    ) -> str:
        """Create a new budget envelope.

        Creates a new budget envelope with the specified parameters.
        """
        try:
            envelope = envelope_service.create_envelope(
                category, budgeted_amount, starting_balance, description
            )
            return json.dumps(envelope, indent=2)
        except ValueError as e:
            return f"Error: {str(e)}"
        except (TypeError, KeyError, AttributeError) as e:
            return f"Internal error: Data processing error: {str(e)}"
        except Exception:
            # Log unexpected errors for debugging while providing safe user message
            logger.exception("An unexpected error occurred in create_envelope")
            return "Internal error: An unexpected error occurred. Please contact support if the issue persists."

    @mcp.tool()
    async def list_envelopes() -> str:
        """Get all budget envelopes with their current balances.

        Returns:
            List of all envelopes with current balance calculations.
        """
        try:
            envelopes = envelope_service.get_all_envelopes()
            return json.dumps(envelopes, indent=2)
        except (TypeError, KeyError, AttributeError) as e:
            return f"Internal error: Data processing error: {str(e)}"
        except Exception as e:
            return f"Internal error: An unexpected error occurred: {str(e)}"

    @mcp.tool()
    async def get_envelope(
        envelope_id: Annotated[int, "ID of the envelope to retrieve"]
    ) -> str:
        """Get specific envelope details by ID.

        Returns:
            Envelope details with current balance.
        """
        try:
            envelope = envelope_service.get_envelope(envelope_id)
            if not envelope:
                return "Error: Envelope not found"
            return json.dumps(envelope, indent=2)
        except (TypeError, KeyError, AttributeError) as e:
            return f"Internal error: Data processing error: {str(e)}"
        except Exception as e:
            return f"Internal error: An unexpected error occurred: {str(e)}"

    @mcp.tool()
    async def update_envelope(
        envelope_id: Annotated[int, "ID of the envelope to update"],
        category: Annotated[Optional[str], "New category name (optional)"] = None,
        budgeted_amount: Annotated[
            Optional[float], "New budgeted amount (optional)"
        ] = None,
        starting_balance: Annotated[
            Optional[float], "New starting balance (optional)"
        ] = None,
        description: Annotated[Optional[str], "New description (optional)"] = None,
    ) -> str:
        """Update an existing envelope's properties.

        Returns:
            Updated envelope details.
        """
        try:
            envelope = envelope_service.update_envelope(
                envelope_id, category, budgeted_amount, starting_balance, description
            )
            return json.dumps(envelope, indent=2)
        except ValueError as e:
            return f"Error: {str(e)}"
        except (TypeError, KeyError, AttributeError) as e:
            return f"Internal error: Data processing error: {str(e)}"
        except Exception as e:
            return f"Internal error: An unexpected error occurred: {str(e)}"

    @mcp.tool()
    async def delete_envelope(
        envelope_id: Annotated[int, "ID of the envelope to delete"]
    ) -> str:
        """Delete an envelope by ID.

        Returns:
            Confirmation message.
        """
        try:
            result = envelope_service.delete_envelope(envelope_id)
            return json.dumps(result, indent=2)
        except ValueError as e:
            return f"Error: {str(e)}"
        except (TypeError, KeyError, AttributeError) as e:
            return f"Internal error: Data processing error: {str(e)}"
        except Exception as e:
            return f"Internal error: An unexpected error occurred: {str(e)}"


def _register_transaction_tools(mcp: FastMCP, transaction_service: TransactionService):
    """Register all transaction management tools."""

    @mcp.tool()
    async def create_transaction(
        envelope_id: Annotated[int, "ID of the envelope this transaction belongs to"],
        amount: Annotated[
            float, "Transaction amount (positive for income, negative for expense)"
        ],
        description: Annotated[str, "Description of the transaction"],
        type: Annotated[str, "Type of transaction: 'income' or 'expense'"],
        date: Annotated[
            Optional[str],
            "Transaction date in YYYY-MM-DD format. Defaults to current date",
        ] = None,
    ) -> str:
        """Create a new transaction.

        Creates a new income or expense transaction for the specified envelope.
        """
        try:
            transaction = transaction_service.create_transaction(
                envelope_id, amount, description, date, type
            )
            return json.dumps(transaction, indent=2)
        except ValueError as e:
            return f"Error: {str(e)}"
        except (TypeError, KeyError, AttributeError) as e:
            return f"Internal error: Data processing error: {str(e)}"
        except Exception:
            # Log unexpected errors for debugging while providing safe user message
            logger.exception("An unexpected error occurred in create_transaction")
            return "Internal error: An unexpected error occurred. Please contact support if the issue persists."

    @mcp.tool()
    async def list_transactions(
        envelope_id: Annotated[
            Optional[int], "Filter transactions by envelope ID (optional)"
        ] = None
    ) -> str:
        """Get transactions, optionally filtered by envelope.

        Returns:
            List of transactions.
        """
        try:
            transactions = (
                transaction_service.get_transactions_by_envelope(envelope_id)
                if envelope_id
                else transaction_service.get_all_transactions()
            )
            return json.dumps(transactions, indent=2)
        except (TypeError, KeyError, AttributeError) as e:
            return f"Internal error: Data processing error: {str(e)}"
        except Exception as e:
            return f"Internal error: An unexpected error occurred: {str(e)}"

    @mcp.tool()
    async def get_transaction(
        transaction_id: Annotated[int, "ID of the transaction to retrieve"]
    ) -> str:
        """Get specific transaction details by ID.

        Returns:
            Transaction details.
        """
        try:
            transaction = transaction_service.get_transaction(transaction_id)
            if not transaction:
                return "Error: Transaction not found"
            return json.dumps(transaction, indent=2)
        except (TypeError, KeyError, AttributeError) as e:
            return f"Internal error: Data processing error: {str(e)}"
        except Exception as e:
            return f"Internal error: An unexpected error occurred: {str(e)}"

    @mcp.tool()
    async def update_transaction(
        transaction_id: Annotated[int, "ID of the transaction to update"],
        envelope_id: Annotated[Optional[int], "New envelope ID (optional)"] = None,
        amount: Annotated[Optional[float], "New amount (optional)"] = None,
        description: Annotated[Optional[str], "New description (optional)"] = None,
        type: Annotated[
            Optional[str], "New type: 'income' or 'expense' (optional)"
        ] = None,
        date: Annotated[
            Optional[str], "New date in YYYY-MM-DD format (optional)"
        ] = None,
    ) -> str:
        """Update an existing transaction's properties.

        Returns:
            Updated transaction details.
        """
        try:
            transaction = transaction_service.update_transaction(
                transaction_id, envelope_id, amount, description, date, type
            )
            return json.dumps(transaction, indent=2)
        except ValueError as e:
            return f"Error: {str(e)}"
        except (TypeError, KeyError, AttributeError) as e:
            return f"Internal error: Data processing error: {str(e)}"
        except Exception as e:
            return f"Internal error: An unexpected error occurred: {str(e)}"

    @mcp.tool()
    async def delete_transaction(
        transaction_id: Annotated[int, "ID of the transaction to delete"]
    ) -> str:
        """Delete a transaction by ID.

        Returns:
            Confirmation message.
        """
        try:
            result = transaction_service.delete_transaction(transaction_id)
            return json.dumps(result, indent=2)
        except ValueError as e:
            return f"Error: {str(e)}"
        except (TypeError, KeyError, AttributeError) as e:
            return f"Internal error: Data processing error: {str(e)}"
        except Exception as e:
            return f"Internal error: An unexpected error occurred: {str(e)}"


def _register_utility_tools(mcp: FastMCP, envelope_service: EnvelopeService):
    """Register all utility tools."""

    @mcp.tool()
    async def get_envelope_balance(
        envelope_id: Annotated[int, "ID of the envelope"]
    ) -> str:
        """Get current balance for specific envelope.

        Returns:
            Current balance information for the envelope.
        """
        try:
            balance = envelope_service.get_envelope_balance(envelope_id)
            return json.dumps(balance, indent=2)
        except ValueError as e:
            return f"Error: {str(e)}"
        except (TypeError, KeyError, AttributeError) as e:
            return f"Internal error: Data processing error: {str(e)}"
        except Exception as e:
            return f"Internal error: An unexpected error occurred: {str(e)}"

    @mcp.tool()
    async def get_budget_summary() -> str:
        """Get overall budget status and summary.

        Returns:
            Summary of all envelopes and overall budget status.
        """
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
            return json.dumps(summary, indent=2)
        except (TypeError, KeyError, AttributeError) as e:
            return f"Internal error: Data processing error: {str(e)}"
        except Exception as e:
            return f"Internal error: An unexpected error occurred: {str(e)}"


def create_fastmcp_server(config_name=None, enable_auth=True):
    """
    Factory function to create FastMCP server with all tools registered.

    Args:
        config_name (str): Configuration environment ('development', 'production', 'testing')
        enable_auth (bool): Whether to enable bearer token authentication for HTTP transport
    Returns:
        FastMCP: Configured FastMCP server instance with middleware properly configured
    """
    if config_name is None:
        config_name = os.getenv("APP_ENV", "development")

    # Get configuration
    app_config = config[config_name]()

    # Initialize database and services
    db = Database(app_config.DATABASE_FILE)
    envelope_service = EnvelopeService(db)
    transaction_service = TransactionService(db)

    # Create FastMCP server
    mcp = FastMCP("budget-envelope-server")

    # Store services for tool access
    mcp.envelope_service = envelope_service
    mcp.transaction_service = transaction_service
    mcp.db = db

    # Configure authentication
    _configure_authentication(mcp, app_config, enable_auth)

    # Register all tools
    _register_envelope_tools(mcp, envelope_service)
    _register_transaction_tools(mcp, transaction_service)
    _register_utility_tools(mcp, envelope_service)

    return mcp
