from typing import List, Annotated
from mcp.types import TextContent
import json
from app.mcp.registry import register


class UtilityTools:
    """MCP tools for utility operations like balance checking and summaries."""
    
    def __init__(self, envelope_service, transaction_service, database):
        self.envelope_service = envelope_service
        self.transaction_service = transaction_service
        self.database = database # This is passed but not used by current tools. Kept for consistency.
    
    @register
    async def get_envelope_balance(self, envelope_id: Annotated[int, "ID of the envelope to get balance for"]) -> list[TextContent]:
        """Get current balance for a specific envelope."""
        try:
            envelope = self.envelope_service.get_envelope(envelope_id)
            if not envelope:
                return [TextContent(
                    type="text",
                    text="Error: Envelope not found"
                )]
            
            # The envelope object from envelope_service already contains 'current_balance'
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
            # import logging
            # logging.exception("An internal error occurred in get_envelope_balance")
            return [TextContent(
                type="text",
                text="Internal error: An unexpected error occurred. Please contact support if the issue persists."
            )]

    @register
    async def get_budget_summary(self) -> list[TextContent]:
        """Get overall budget status and summary."""
        try:
            envelopes = self.envelope_service.get_all_envelopes()

            total_budgeted = sum(env["budgeted_amount"] for env in envelopes)
            # current_balance already reflects deductions or additions from starting_balance
            total_current_balance = sum(env["current_balance"] for env in envelopes)
            total_starting_balance = sum(env["starting_balance"] for env in envelopes)

            # Total spent is the difference between what was budgeted (or started with, if considering that as initial budget)
            # and what is currently remaining.
            # A more direct way to think about spending might be sum of 'expense' transactions.
            # However, current_balance = starting_balance + income - expenses.
            # So, starting_balance - current_balance = expenses - income (net expenses)
            # If we want total "spent" against budget, it's more complex if income can add to an envelope.
            # For simplicity, let's assume "spent" means how much the balance has gone down from the starting point.
            # Or, how much of the budgeted amount has been utilized.

            # Let's define "total_spent_from_starting" as the reduction from initial balances.
            total_spent_from_starting = total_starting_balance - total_current_balance

            # Let's define "effective_budget_used" considering budgeted amounts.
            # This interpretation is a bit tricky without knowing exactly how income vs budgeted_amount is treated.
            # If budgeted_amount is a target spending limit, and current_balance can exceed starting_balance due to income,
            # then "spent" relative to "budgeted_amount" needs careful definition.
            # The original code had: total_spent = total_starting - total_current
            # remaining_budget = total_budgeted - total_spent
            # This implies "total_spent" is how much the balance has changed from the start.
            # And "remaining_budget" is how much of the "budgeted_amount" is left after this change.

            total_spent = total_starting_balance - total_current_balance # consistent with original logic
            remaining_budget = total_budgeted - total_spent # consistent with original logic

            summary = {
                "budget_summary": {
                    "total_budgeted_amount": total_budgeted,
                    "total_starting_balance": total_starting_balance,
                    "total_current_balance": total_current_balance,
                    "total_spent_from_starting_balance": total_spent, # Renamed for clarity
                    "remaining_budget_vs_budgeted_amount": remaining_budget, # Renamed for clarity
                    "budget_utilization_percent": round((total_spent / total_budgeted * 100) if total_budgeted > 0 else 0, 2)
                },
                "envelope_count": len(envelopes),
                "envelopes": envelopes # each envelope already has its current_balance
            }

            return [TextContent(
                type="text",
                text=json.dumps(summary, indent=2)
            )]
        except Exception as e:
            # import logging
            # logging.exception("An internal error occurred in get_budget_summary")
            return [TextContent(
                type="text",
                text=f"Internal error: An unexpected error occurred: {str(e)}"
            )]