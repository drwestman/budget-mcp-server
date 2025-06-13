from mcp.server import Server
from mcp.types import Tool, TextContent
import json


class TransactionTools:
    """MCP tools for transaction management operations."""
    
    def __init__(self, transaction_service):
        self.transaction_service = transaction_service
    
    def register_tools(self, server: Server):
        """Register all transaction-related MCP tools with the server."""
        
        @server.tool("create_transaction")
        async def create_transaction(
            envelope_id: int,
            amount: float,
            description: str,
            date: str,
            type: str
        ) -> list[TextContent]:
            """Create a new transaction.
            
            Args:
                envelope_id: ID of the envelope this transaction belongs to
                amount: Transaction amount (positive number)
                description: Description of the transaction
                date: Transaction date (YYYY-MM-DD format)
                type: Transaction type ('income' or 'expense')
            
            Returns:
                Created transaction details
            """
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
                return [TextContent(
                    type="text",
                    text=f"Internal error: {str(e)}"
                )]
        
        @server.tool("list_transactions")
        async def list_transactions(envelope_id: int = None) -> list[TextContent]:
            """Get all transactions, optionally filtered by envelope.
            
            Args:
                envelope_id: Optional envelope ID to filter transactions
                
            Returns:
                List of transactions (all or filtered by envelope)
            """
            try:
                if envelope_id:
                    transactions = self.transaction_service.get_transactions_by_envelope(envelope_id)
                else:
                    transactions = self.transaction_service.get_all_transactions()
                return [TextContent(
                    type="text",
                    text=json.dumps(transactions, indent=2)
                )]
            except ValueError as e:
                return [TextContent(
                    type="text",
                    text=f"Error: {str(e)}"
                )]
            except Exception as e:
                return [TextContent(
                    type="text",
                    text=f"Internal error: {str(e)}"
                )]
        
        @server.tool("get_transaction")
        async def get_transaction(transaction_id: int) -> list[TextContent]:
            """Get specific transaction details by ID.
            
            Args:
                transaction_id: ID of the transaction to retrieve
                
            Returns:
                Transaction details
            """
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
                    text=f"Internal error: {str(e)}"
                )]
        
        @server.tool("update_transaction")
        async def update_transaction(
            transaction_id: int,
            envelope_id: int = None,
            amount: float = None,
            description: str = None,
            date: str = None,
            type: str = None
        ) -> list[TextContent]:
            """Update an existing transaction's properties.
            
            Args:
                transaction_id: ID of the transaction to update
                envelope_id: New envelope ID (optional)
                amount: New amount (optional)
                description: New description (optional)
                date: New date in YYYY-MM-DD format (optional)
                type: New type 'income' or 'expense' (optional)
                
            Returns:
                Updated transaction details
            """
            try:
                transaction = self.transaction_service.update_transaction(
                    transaction_id, envelope_id, amount, description, date, type
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
                return [TextContent(
                    type="text",
                    text=f"Internal error: {str(e)}"
                )]
        
        @server.tool("delete_transaction")
        async def delete_transaction(transaction_id: int) -> list[TextContent]:
            """Delete a transaction by ID.
            
            Args:
                transaction_id: ID of the transaction to delete
                
            Returns:
                Confirmation message
            """
            try:
                result = self.transaction_service.delete_transaction(transaction_id)
                return [TextContent(
                    type="text",
                    text=json.dumps(result, indent=2)
                )]
            except ValueError as e:
                return [TextContent(
                    type="text",
                    text=f"Error: {str(e)}"
                )]
            except Exception as e:
                return [TextContent(
                    type="text",
                    text=f"Internal error: {str(e)}"
                )]