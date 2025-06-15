from ast import List
from mcp.server import Server
"""Implementation for creating a new budget envelope.
    Creates a new budget envelope with the specified parameters and returns the result
    as a list of TextContent objects suitable for MCP server responses.
        category (str): Name/category of the envelope (must be unique across all envelopes)
        budgeted_amount (float): Planned budget amount for this envelope (must be positive)
        starting_balance (float, optional): Initial balance for the envelope. Defaults to 0.0
        description (str, optional): Optional description providing additional context about 
            the envelope's purpose. Defaults to empty string
        list[TextContent]: A list containing a single TextContent object with:
            - On success: JSON-formatted envelope data including id, category, budgeted_amount,
            starting_balance, description, and creation timestamp
            - On ValueError: Error message describing validation failures (e.g., duplicate 
            category, invalid amount)
            - On unexpected error: Generic internal error message for security
    Raises:
        No exceptions are raised - all errors are caught and returned as TextContent
    error messages to maintain MCP protocol compliance.
"""
from mcp.types import Tool, TextContent
import json


class EnvelopeTools:
    """MCP tools for envelope management operations."""
    
    def __init__(self, envelope_service):
        self.envelope_service = envelope_service

    async def _create_envelope_impl(self, category: str, budgeted_amount: float, starting_balance: float = 0.0, description: str = "") -> list[TextContent]:
        """Implementation for creating a new budget envelope."""
        try:
            envelope = self.envelope_service.create_envelope(
                category, budgeted_amount, starting_balance, description
            )
            return [TextContent(type="text", text=json.dumps(envelope, indent=2))]
        except ValueError as e:
            return [TextContent(type="text", text=f"Error: {str(e)}")]
        except Exception as e:
            # Log the full exception for server-side debugging
            # import logging
            # logging.exception("An internal error occurred in _create_envelope_impl")
            return [TextContent(type="text", text="Internal error: An unexpected error occurred. Please contact support if the issue persists.")]

    def register_tools(self, server: Server):
        """Register all envelope-related MCP tools with the server."""
        
        create_envelope_input_schema = {
            "type": "object",
            "properties": {
                "category": {"type": "string", "description": "Name/category of the envelope (must be unique)"},
                "budgeted_amount": {"type": "number", "description": "Planned budget amount for this envelope"},
                "starting_balance": {"type": "number", "description": "Initial balance (default: 0.0)"},
                "description": {"type": "string", "description": "Optional description of the envelope"}
            },
            "required": ["category", "budgeted_amount"]
        }

        create_envelope_tool = Tool(
            name="create_envelope",
            description="Create a new budget envelope.",
            func=self._create_envelope_impl, # Point to the class method
            inputSchema=create_envelope_input_schema
        )

        if not hasattr(server, 'tools') or server.tools is None:
            server.tools = []
        server.tools.append(create_envelope_tool)
        
        # Keep original registration for other tools for now
        @server.tool("list_envelopes")
        async def list_envelopes() -> list[TextContent]: # Corrected to keep original signature
            """Get all budget envelopes with their current balances.
            
                Args: # Args was missing in a previous attempt, ensuring it's here.
                    # No arguments here for list_envelopes in this context.

                Returns:
                    List of all envelopes with current balance calculations
            """
            try:
                envelopes = self.envelope_service.get_all_envelopes() # Uses self
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