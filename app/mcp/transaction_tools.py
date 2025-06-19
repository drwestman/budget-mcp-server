from typing import List, Optional, Annotated
from mcp.types import TextContent
import json
from app.mcp.registry import register


class TransactionTools:
    """MCP tools for transaction management operations."""
    
    def __init__(self, transaction_service):
        self.transaction_service = transaction_service
    
    @register
    async def create_transaction(
        self,
        envelope_id: Annotated[int, "ID of the envelope this transaction belongs to"],
        amount: Annotated[float, "Transaction amount (positive number)"],
        description: Annotated[str, "Description of the transaction"],
        date: Annotated[str, "Transaction date (YYYY-MM-DD format)"],
        type: Annotated[str, "Transaction type ('income' or 'expense')"]
    ) -> list[TextContent]:
        """Create a new transaction."""
        try:
            transaction = self.transaction_service.create_transaction(
                envelope_id, amount, description, date, type
            )
            return [TextContent(
                type="text",
                text=json.dumps(transaction, indent=2)
            )]
        except ValueError as e:
            return [TextContent(
                type="text",
                text=f"Error: {str(e)}"
            )]
        except Exception as e:
            # import logging
            # logging.exception("An internal error occurred in create_transaction")
            return [TextContent(
                type="text",
                text="Internal error: An unexpected error occurred. Please contact support if the issue persists."
            )]

    @register
    async def list_transactions(self, envelope_id: Annotated[Optional[int], "Optional envelope ID to filter transactions"] = None) -> list[TextContent]:
        """Get all transactions, optionally filtered by envelope."""
        try:
            if envelope_id:
                transactions = self.transaction_service.get_transactions_by_envelope(envelope_id)
            else:
                transactions = self.transaction_service.get_all_transactions()
            return [TextContent(
                type="text",
                text=json.dumps(transactions, indent=2)
            )]
        except ValueError as e: # Specific error from service
            return [TextContent(
                type="text",
                text=f"Error: {str(e)}"
            )]
        except Exception as e: # Catch-all for other unexpected errors
            return [TextContent(
                type="text",
                text=f"Internal error: An unexpected error occurred: {str(e)}"
            )]

    @register
    async def get_transaction(self, transaction_id: Annotated[int, "ID of the transaction to retrieve"]) -> list[TextContent]:
        """Get specific transaction details by ID."""
        try:
            transaction = self.transaction_service.get_transaction(transaction_id)
            if not transaction:
                return [TextContent(
                    type="text",
                    text="Error: Transaction not found"
                )]
            return [TextContent(
                type="text",
                text=json.dumps(transaction, indent=2)
            )]
        except Exception as e:
            return [TextContent(
                type="text",
                text=f"Internal error: An unexpected error occurred: {str(e)}"
            )]

    @register
    async def update_transaction(
        self,
        transaction_id: Annotated[int, "ID of the transaction to update"],
        envelope_id: Annotated[Optional[int], "New envelope ID (optional)"] = None,
        amount: Annotated[Optional[float], "New amount (optional)"] = None,
        description: Annotated[Optional[str], "New description (optional)"] = None,
        date: Annotated[Optional[str], "New date in YYYY-MM-DD format (optional)"] = None,
        type: Annotated[Optional[str], "New type 'income' or 'expense' (optional)"] = None
    ) -> list[TextContent]:
        """Update an existing transaction's properties."""
        try:
            transaction = self.transaction_service.update_transaction(
                transaction_id, envelope_id, amount, description, date, type
            )
            return [TextContent(
                type="text",
                text=json.dumps(transaction, indent=2)
            )]
        except ValueError as e: # Specific error from service
            return [TextContent(
                type="text",
                text=f"Error: {str(e)}"
            )]
        except Exception as e: # Catch-all for other unexpected errors
            return [TextContent(
                type="text",
                text=f"Internal error: An unexpected error occurred: {str(e)}"
            )]

    @register
    async def delete_transaction(self, transaction_id: Annotated[int, "ID of the transaction to delete"]) -> list[TextContent]:
        """Delete a transaction by ID."""
        try:
            result = self.transaction_service.delete_transaction(transaction_id)
            return [TextContent(
                type="text",
                text=json.dumps(result, indent=2)
            )]
        except ValueError as e: # Specific error from service
            return [TextContent(
                type="text",
                text=f"Error: {str(e)}"
            )]
        except Exception as e: # Catch-all for other unexpected errors
            return [TextContent(
                type="text",
                text=f"Internal error: An unexpected error occurred: {str(e)}"
            )]