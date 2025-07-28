#!/usr/bin/env python3
"""
Shared tool handlers for Budget Cash Envelope MCP Server.
This module contains the business logic for all tools in a unified format.
"""
import logging
from datetime import datetime
from typing import Any

from app.services.envelope_service import EnvelopeService
from app.services.transaction_service import TransactionService

logger = logging.getLogger(__name__)

# Type alias for handler responses
HandlerResponse = str | dict[str, Any] | list[dict[str, Any]]


def format_error(error_msg: str) -> HandlerResponse:
    """Format error message consistently."""
    return f"Error: {error_msg}"


def format_internal_error(error_msg: str) -> HandlerResponse:
    """Format internal error message consistently."""
    return f"Internal error: {error_msg}"


def format_success(data: Any) -> HandlerResponse:
    """Format success response consistently."""
    if isinstance(data, dict | list):
        return data
    return str(data)


# Envelope handlers
async def handle_create_envelope(
    envelope_service: EnvelopeService, arguments: dict[str, Any]
) -> HandlerResponse:
    """Handle create_envelope tool call."""
    try:
        category = arguments["category"]
        budgeted_amount = arguments["budgeted_amount"]
        starting_balance = arguments.get("starting_balance", 0.0)
        description = arguments.get("description", "")

        envelope = envelope_service.create_envelope(
            category, budgeted_amount, starting_balance, description
        )
        return format_success(envelope)
    except ValueError as e:
        return format_error(str(e))
    except (TypeError, KeyError, AttributeError) as e:
        return format_internal_error(f"Data processing error: {str(e)}")
    except Exception:
        logger.exception("An unexpected error occurred in create_envelope")
        return format_internal_error(
            "An unexpected error occurred. Please contact support if the "
            "issue persists."
        )


async def handle_list_envelopes(
    envelope_service: EnvelopeService, arguments: dict[str, Any]
) -> HandlerResponse:
    """Handle list_envelopes tool call."""
    try:
        envelopes = envelope_service.get_all_envelopes()
        return format_success(envelopes)
    except (TypeError, KeyError, AttributeError) as e:
        return format_internal_error(f"Data processing error: {str(e)}")
    except Exception as e:
        return format_internal_error(f"An unexpected error occurred: {str(e)}")


async def handle_get_envelope(
    envelope_service: EnvelopeService, arguments: dict[str, Any]
) -> HandlerResponse:
    """Handle get_envelope tool call."""
    try:
        envelope_id = arguments["envelope_id"]
        envelope = envelope_service.get_envelope(envelope_id)
        if not envelope:
            return format_error("Envelope not found")
        return format_success(envelope)
    except (TypeError, KeyError, AttributeError) as e:
        return format_internal_error(f"Data processing error: {str(e)}")
    except Exception as e:
        return format_internal_error(f"An unexpected error occurred: {str(e)}")


async def handle_update_envelope(
    envelope_service: EnvelopeService, arguments: dict[str, Any]
) -> HandlerResponse:
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
        return format_success(envelope)
    except ValueError as e:
        return format_error(str(e))
    except (TypeError, KeyError, AttributeError) as e:
        return format_internal_error(f"Data processing error: {str(e)}")
    except Exception as e:
        return format_internal_error(f"An unexpected error occurred: {str(e)}")


async def handle_delete_envelope(
    envelope_service: EnvelopeService, arguments: dict[str, Any]
) -> HandlerResponse:
    """Handle delete_envelope tool call."""
    try:
        envelope_id = arguments["envelope_id"]
        result = envelope_service.delete_envelope(envelope_id)
        return format_success(result)
    except ValueError as e:
        return format_error(str(e))
    except (TypeError, KeyError, AttributeError) as e:
        return format_internal_error(f"Data processing error: {str(e)}")
    except Exception as e:
        return format_internal_error(f"An unexpected error occurred: {str(e)}")


# Transaction handlers
async def handle_create_transaction(
    transaction_service: TransactionService, arguments: dict[str, Any]
) -> HandlerResponse:
    """Handle create_transaction tool call."""
    try:
        envelope_id = arguments["envelope_id"]
        amount = arguments["amount"]
        description = arguments["description"]
        transaction_type = arguments["type"]
        date = arguments.get("date")

        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")

        transaction = transaction_service.create_transaction(
            envelope_id, amount, description, date, transaction_type
        )
        return format_success(transaction)
    except ValueError as e:
        return format_error(str(e))
    except (TypeError, KeyError, AttributeError) as e:
        return format_internal_error(f"Data processing error: {str(e)}")
    except Exception:
        logger.exception("An unexpected error occurred in create_transaction")
        return format_internal_error(
            "An unexpected error occurred. Please contact support if the "
            "issue persists."
        )


async def handle_list_transactions(
    transaction_service: TransactionService, arguments: dict[str, Any]
) -> HandlerResponse:
    """Handle list_transactions tool call."""
    try:
        envelope_id = arguments.get("envelope_id")
        transactions = (
            transaction_service.get_transactions_by_envelope(envelope_id)
            if envelope_id
            else transaction_service.get_all_transactions()
        )
        return format_success(transactions)
    except (TypeError, KeyError, AttributeError) as e:
        return format_internal_error(f"Data processing error: {str(e)}")
    except Exception as e:
        return format_internal_error(f"An unexpected error occurred: {str(e)}")


async def handle_get_transaction(
    transaction_service: TransactionService, arguments: dict[str, Any]
) -> HandlerResponse:
    """Handle get_transaction tool call."""
    try:
        transaction_id = arguments["transaction_id"]
        transaction = transaction_service.get_transaction(transaction_id)
        if not transaction:
            return format_error("Transaction not found")
        return format_success(transaction)
    except (TypeError, KeyError, AttributeError) as e:
        return format_internal_error(f"Data processing error: {str(e)}")
    except Exception as e:
        return format_internal_error(f"An unexpected error occurred: {str(e)}")


async def handle_update_transaction(
    transaction_service: TransactionService, arguments: dict[str, Any]
) -> HandlerResponse:
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
        return format_success(transaction)
    except ValueError as e:
        return format_error(str(e))
    except (TypeError, KeyError, AttributeError) as e:
        return format_internal_error(f"Data processing error: {str(e)}")
    except Exception as e:
        return format_internal_error(f"An unexpected error occurred: {str(e)}")


async def handle_delete_transaction(
    transaction_service: TransactionService, arguments: dict[str, Any]
) -> HandlerResponse:
    """Handle delete_transaction tool call."""
    try:
        transaction_id = arguments["transaction_id"]
        result = transaction_service.delete_transaction(transaction_id)
        return format_success(result)
    except ValueError as e:
        return format_error(str(e))
    except (TypeError, KeyError, AttributeError) as e:
        return format_internal_error(f"Data processing error: {str(e)}")
    except Exception as e:
        return format_internal_error(f"An unexpected error occurred: {str(e)}")


# Utility handlers
async def handle_get_envelope_balance(
    envelope_service: EnvelopeService, arguments: dict[str, Any]
) -> HandlerResponse:
    """Handle get_envelope_balance tool call."""
    try:
        envelope_id = arguments["envelope_id"]
        balance = envelope_service.get_envelope_balance(envelope_id)
        return format_success(balance)
    except ValueError as e:
        return format_error(str(e))
    except (TypeError, KeyError, AttributeError) as e:
        return format_internal_error(f"Data processing error: {str(e)}")
    except Exception as e:
        return format_internal_error(f"An unexpected error occurred: {str(e)}")


async def handle_get_budget_summary(
    envelope_service: EnvelopeService, arguments: dict[str, Any]
) -> HandlerResponse:
    """Handle get_budget_summary tool call."""
    try:
        envelopes = envelope_service.get_all_envelopes()

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
        return format_success(summary)
    except (TypeError, KeyError, AttributeError) as e:
        return format_internal_error(f"Data processing error: {str(e)}")
    except Exception as e:
        return format_internal_error(f"An unexpected error occurred: {str(e)}")


async def handle_get_cloud_status(
    envelope_service: EnvelopeService, arguments: dict[str, Any]
) -> HandlerResponse:
    """Handle get_cloud_status tool call."""
    try:
        status = envelope_service.db.get_connection_status()
        sync_status = envelope_service.db.get_sync_status()
        result = {"connection": status, "sync": sync_status}
        return format_success(result)
    except Exception as e:
        return format_internal_error(f"An unexpected error occurred: {str(e)}")


async def handle_sync_to_cloud(
    envelope_service: EnvelopeService, arguments: dict[str, Any]
) -> HandlerResponse:
    """Handle sync_to_cloud tool call."""
    try:
        results = envelope_service.db.sync_to_cloud()
        return format_success(results)
    except ValueError as e:
        return format_error(str(e))
    except Exception as e:
        return format_internal_error(f"An unexpected error occurred: {str(e)}")


async def handle_sync_from_cloud(
    envelope_service: EnvelopeService, arguments: dict[str, Any]
) -> HandlerResponse:
    """Handle sync_from_cloud tool call."""
    try:
        results = envelope_service.db.sync_from_cloud()
        return format_success(results)
    except ValueError as e:
        return format_error(str(e))
    except Exception as e:
        return format_internal_error(f"An unexpected error occurred: {str(e)}")
