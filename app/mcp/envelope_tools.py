from mcp.server import Server
from mcp.types import Tool, TextContent
import json


class EnvelopeTools:
    """MCP tools for envelope management operations."""
    
    def __init__(self, envelope_service):
        self.envelope_service = envelope_service
    
    def register_tools(self, server: Server):
        """Register all envelope-related MCP tools with the server."""
        
        @server.tool("create_envelope")
        async def create_envelope(
            category: str,
            budgeted_amount: float,
            starting_balance: float = 0.0,
            description: str = ""
        ) -> list[TextContent]:
            """Create a new budget envelope.
            
            Args:
                category: Name/category of the envelope (must be unique)
                budgeted_amount: Planned budget amount for this envelope
                starting_balance: Initial balance (default: 0.0)
                description: Optional description of the envelope
            
            Returns:
                Created envelope details with current balance
            """
            try:
                envelope = self.envelope_service.create_envelope(
                    category, budgeted_amount, starting_balance, description
                )
                return [TextContent(
                    type="text",
                    text=json.dumps(envelope, indent=2)
                )]
            except ValueError as e:
                return [TextContent(
                    type="text", 
                    text=f"Error: {str(e)}"
                )]
            except Exception as e:  
                # Log the full exception for server-side debugging  
                # import logging  
                # logging.exception("An internal error occurred in create_envelope")  
                return [TextContent(  
                    type="text",  
                    text="Internal error: An unexpected error occurred. Please contact support if the issue persists."  
                )]
        
        @server.tool("list_envelopes")
        async def list_envelopes() -> list[TextContent]:
            """Get all budget envelopes with their current balances.
            
            Returns:
                List of all envelopes with current balance calculations
            """
            try:
                envelopes = self.envelope_service.get_all_envelopes()
                return [TextContent(
                    type="text",
                    text=json.dumps(envelopes, indent=2)
                )]
            except Exception as e:
                return [TextContent(
                    type="text",
                    text=f"Internal error: {str(e)}"
                )]
        
        @server.tool("get_envelope")
        async def get_envelope(envelope_id: int) -> list[TextContent]:
            """Get specific envelope details by ID.
            
            Args:
                envelope_id: ID of the envelope to retrieve
                
            Returns:
                Envelope details with current balance
            """
            try:
                envelope = self.envelope_service.get_envelope(envelope_id)
                if not envelope:
                    return [TextContent(
                        type="text",
                        text="Error: Envelope not found"
                    )]
                return [TextContent(
                    type="text",
                    text=json.dumps(envelope, indent=2)
                )]
            except Exception as e:
                return [TextContent(
                    type="text",
                    text=f"Internal error: {str(e)}"
                )]
        
        @server.tool("update_envelope")
        async def update_envelope(
            envelope_id: int,
            category: str = None,
            budgeted_amount: float = None,
            starting_balance: float = None,
            description: str = None
        ) -> list[TextContent]:
            """Update an existing envelope's properties.
            
            Args:
                envelope_id: ID of the envelope to update
                category: New category name (optional)
                budgeted_amount: New budgeted amount (optional)
                starting_balance: New starting balance (optional)
                description: New description (optional)
                
            Returns:
                Updated envelope details
            """
            try:
                envelope = self.envelope_service.update_envelope(
                    envelope_id, category, budgeted_amount, starting_balance, description
                )
                return [TextContent(
                    type="text",
                    text=json.dumps(envelope, indent=2)
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
        
        @server.tool("delete_envelope")
        async def delete_envelope(envelope_id: int) -> list[TextContent]:
            """Delete an envelope by ID.
            
            Args:
                envelope_id: ID of the envelope to delete
                
            Returns:
                Confirmation message
            """
            try:
                result = self.envelope_service.delete_envelope(envelope_id)
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