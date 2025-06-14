from mcp.server import Server
from mcp.types import Tool, TextContent
import json


class UtilityTools:
    """MCP tools for utility operations like balance checking and summaries."""
    
    def __init__(self, envelope_service, transaction_service, database):
        self.envelope_service = envelope_service
        self.transaction_service = transaction_service
        self.database = database
    
    def register_tools(self, server: Server):
        """Register all utility MCP tools with the server."""
        
        @server.tool("get_envelope_balance")
        async def get_envelope_balance(envelope_id: int) -> list[TextContent]:
            """Get current balance for a specific envelope.
            
            Args:
                envelope_id: ID of the envelope to get balance for
                
            Returns:
                Current balance information for the envelope
            """
            try:
                envelope = self.envelope_service.get_envelope(envelope_id)
                if not envelope:
                    return [TextContent(
                        type="text",
                        text="Error: Envelope not found"
                    )]
                
                balance_info = {
                    "envelope_id": envelope_id,
                    "category": envelope["category"],
                    "starting_balance": envelope["starting_balance"],
                    "budgeted_amount": envelope["budgeted_amount"],
                    "current_balance": envelope["current_balance"]
                }
                
                return [TextContent(
                    type="text",
                    text=json.dumps(balance_info, indent=2)
                )]
            except Exception as e:  
                # Log the full exception for server-side debugging  
                # import logging  
                # logging.exception("An internal error occurred in get_envelope_balance")  
                return [TextContent(  
                    type="text",  
                    text="Internal error: An unexpected error occurred. Please contact support if the issue persists."  
                )]
        
        @server.tool("get_budget_summary")
        async def get_budget_summary() -> list[TextContent]:
            """Get overall budget status and summary.
            
            Returns:
                Complete budget summary with all envelopes and totals
            """
            try:
                envelopes = self.envelope_service.get_all_envelopes()
                
                total_budgeted = sum(env["budgeted_amount"] for env in envelopes)
                total_current = sum(env["current_balance"] for env in envelopes)
                total_starting = sum(env["starting_balance"] for env in envelopes)
                
                # Calculate spending vs budget
                total_spent = total_starting - total_current
                remaining_budget = total_budgeted - total_spent
                
                summary = {
                    "budget_summary": {
                        "total_budgeted_amount": total_budgeted,
                        "total_starting_balance": total_starting,
                        "total_current_balance": total_current,
                        "total_spent": total_spent,
                        "remaining_budget": remaining_budget,
                        "budget_utilization_percent": round((total_spent / total_budgeted * 100) if total_budgeted > 0 else 0, 2)
                    },
                    "envelope_count": len(envelopes),
                    "envelopes": envelopes
                }
                
                return [TextContent(
                    type="text",
                    text=json.dumps(summary, indent=2)
                )]
            except Exception as e:
                return [TextContent(
                    type="text",
                    text=f"Internal error: {str(e)}"
                )]