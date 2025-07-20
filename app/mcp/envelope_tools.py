from typing import Optional, Annotated
from mcp.types import TextContent
import json
import logging
from app.mcp.registry import register

logger = logging.getLogger(__name__)


class EnvelopeTools:
    """MCP tools for envelope management operations."""

    def __init__(self, envelope_service):
        self.envelope_service = envelope_service

    @register
    async def _create_envelope_impl(
        self,
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
    ) -> list[TextContent]:
        """Create a new budget envelope.

        Creates a new budget envelope with the specified parameters.
        """
        try:
            envelope = self.envelope_service.create_envelope(
                category, budgeted_amount, starting_balance, description
            )
            return [TextContent(type="text", text=json.dumps(envelope, indent=2))]
        except ValueError as e:
            return [TextContent(type="text", text=f"Error: {str(e)}")]
        except (TypeError, KeyError, AttributeError) as e:
            return [
                TextContent(
                    type="text", text=f"Internal error: Data processing error: {str(e)}"
                )
            ]
        except Exception as e:
            logger.exception("An internal error occurred in _create_envelope_impl")
            return [
                TextContent(
                    type="text",
                    text="Internal error: An unexpected error occurred. Please contact support if the issue persists.",
                )
            ]

    @register
    async def list_envelopes(self) -> list[TextContent]:
        """Get all budget envelopes with their current balances.

        Returns:
            List of all envelopes with current balance calculations.
        """
        try:
            envelopes = self.envelope_service.get_all_envelopes()
            return [TextContent(type="text", text=json.dumps(envelopes, indent=2))]
        except (TypeError, KeyError, AttributeError) as e:
            return [
                TextContent(
                    type="text", text=f"Internal error: Data processing error: {str(e)}"
                )
            ]
        except Exception as e:
            return [
                TextContent(
                    type="text",
                    text=f"Internal error: An unexpected error occurred: {str(e)}",
                )
            ]

    @register
    async def get_envelope(
        self, envelope_id: Annotated[int, "ID of the envelope to retrieve"]
    ) -> list[TextContent]:
        """Get specific envelope details by ID.

        Returns:
            Envelope details with current balance.
        """
        try:
            envelope = self.envelope_service.get_envelope(envelope_id)
            if not envelope:
                return [TextContent(type="text", text="Error: Envelope not found")]
            return [TextContent(type="text", text=json.dumps(envelope, indent=2))]
        except (TypeError, KeyError, AttributeError) as e:
            return [
                TextContent(
                    type="text", text=f"Internal error: Data processing error: {str(e)}"
                )
            ]
        except Exception as e:
            return [
                TextContent(
                    type="text",
                    text=f"Internal error: An unexpected error occurred: {str(e)}",
                )
            ]

    @register
    async def update_envelope(
        self,
        envelope_id: Annotated[int, "ID of the envelope to update"],
        category: Annotated[Optional[str], "New category name (optional)"] = None,
        budgeted_amount: Annotated[
            Optional[float], "New budgeted amount (optional)"
        ] = None,
        starting_balance: Annotated[
            Optional[float], "New starting balance (optional)"
        ] = None,
        description: Annotated[Optional[str], "New description (optional)"] = None,
    ) -> list[TextContent]:
        """Update an existing envelope's properties.

        Returns:
            Updated envelope details.
        """
        try:
            envelope = self.envelope_service.update_envelope(
                envelope_id, category, budgeted_amount, starting_balance, description
            )
            return [TextContent(type="text", text=json.dumps(envelope, indent=2))]
        except ValueError as e:
            return [TextContent(type="text", text=f"Error: {str(e)}")]
        except (TypeError, KeyError, AttributeError) as e:
            return [
                TextContent(
                    type="text", text=f"Internal error: Data processing error: {str(e)}"
                )
            ]
        except Exception as e:
            return [
                TextContent(
                    type="text",
                    text=f"Internal error: An unexpected error occurred: {str(e)}",
                )
            ]

    @register
    async def delete_envelope(
        self, envelope_id: Annotated[int, "ID of the envelope to delete"]
    ) -> list[TextContent]:
        """Delete an envelope by ID.

        Returns:
            Confirmation message.
        """
        try:
            result = self.envelope_service.delete_envelope(envelope_id)
            return [TextContent(type="text", text=json.dumps(result, indent=2))]
        except ValueError as e:
            return [TextContent(type="text", text=f"Error: {str(e)}")]
        except (TypeError, KeyError, AttributeError) as e:
            return [
                TextContent(
                    type="text", text=f"Internal error: Data processing error: {str(e)}"
                )
            ]
        except Exception as e:
            return [
                TextContent(
                    type="text",
                    text=f"Internal error: An unexpected error occurred: {str(e)}",
                )
            ]
