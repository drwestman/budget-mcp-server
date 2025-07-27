from typing import Any

from app.models.database import Database


class EnvelopeService:
    """
    Handles business logic related to envelopes.
    Depends on the Database class (Dependency Inversion Principle).
    """

    def __init__(self, db: Database) -> None:
        self.db = db

    def create_envelope(
        self,
        category: str,
        budgeted_amount: float,
        starting_balance: float,
        description: str,
    ) -> dict[str, Any]:
        """Creates a new envelope after validating input."""
        if not category or not isinstance(category, str) or len(category.strip()) == 0:
            raise ValueError("Category is required and must be a non-empty string.")
        if not isinstance(budgeted_amount, int | float) or budgeted_amount < 0:
            raise ValueError("Budgeted amount must be a non-negative number.")
        if not isinstance(starting_balance, int | float):
            raise ValueError("Starting balance must be a number.")

        # Check if category already exists
        if self.db.get_envelope_by_category(category):
            raise ValueError(f"Envelope with category '{category}' already exists.")

        envelope_id = self.db.insert_envelope(
            category.strip(), budgeted_amount, starting_balance, description
        )
        if envelope_id is None:
            raise ValueError("Failed to create envelope.")
        return self.get_envelope(envelope_id)

    def get_envelope(self, envelope_id: int) -> dict[str, Any]:
        """Retrieves an envelope by ID, including its current balance."""
        envelope = self.db.get_envelope_by_id(envelope_id)
        if envelope is None:
            raise ValueError(f"Envelope with ID {envelope_id} not found.")
        envelope["current_balance"] = self.db.get_envelope_current_balance(envelope_id)
        return envelope

    def get_all_envelopes(self) -> list[dict[str, Any]]:
        """Retrieves all envelopes, each with its current balance."""
        envelopes = self.db.get_all_envelopes()
        for envelope in envelopes:
            envelope["current_balance"] = self.db.get_envelope_current_balance(
                envelope["id"]
            )
        return envelopes

    def update_envelope(
        self,
        envelope_id: int,
        category: str | None = None,
        budgeted_amount: float | None = None,
        starting_balance: float | None = None,
        description: str | None = None,
    ) -> dict[str, Any]:
        """Updates an envelope after validation."""
        if category is not None:
            if not isinstance(category, str) or len(category.strip()) == 0:
                raise ValueError("Category must be a non-empty string.")
            # Check if new category already exists for another envelope
            existing_envelope = self.db.get_envelope_by_category(category.strip())
            if existing_envelope and existing_envelope["id"] != envelope_id:
                raise ValueError(f"Envelope with category '{category}' already exists.")
            category = category.strip()  # Strip whitespace for consistency

        if budgeted_amount is not None and (
            not isinstance(budgeted_amount, int | float) or budgeted_amount < 0
        ):
            raise ValueError("Budgeted amount must be a non-negative number.")
        if starting_balance is not None and not isinstance(
            starting_balance, int | float
        ):
            raise ValueError("Starting balance must be a number.")

        updated = self.db.update_envelope(
            envelope_id,
            category=category,
            budgeted_amount=budgeted_amount,
            starting_balance=starting_balance,
            description=description,
        )
        if not updated:
            raise ValueError(
                f"Envelope with ID {envelope_id} not found or no valid fields to update."
            )
        result = self.get_envelope(envelope_id)
        return result

    def delete_envelope(self, envelope_id: int) -> dict[str, str]:
        """Deletes an envelope."""
        if not self.db.get_envelope_by_id(envelope_id):
            raise ValueError(f"Envelope with ID {envelope_id} not found.")
        self.db.delete_envelope(envelope_id)
        return {"message": f"Envelope with ID {envelope_id} deleted successfully."}

    def get_envelope_balance(self, envelope_id: int) -> dict[str, Any]:
        """Gets the current balance for a specific envelope.

        Returns:
            A dictionary containing the envelope ID, category, current balance, starting balance, and budgeted amount.
        """
        if not self.db.get_envelope_by_id(envelope_id):
            raise ValueError(f"Envelope with ID {envelope_id} not found.")

        current_balance = self.db.get_envelope_current_balance(envelope_id)
        envelope = self.db.get_envelope_by_id(envelope_id)
        if envelope is None:
            raise ValueError(f"Envelope with ID {envelope_id} not found.")

        return {
            "envelope_id": envelope_id,
            "category": envelope["category"],
            "current_balance": current_balance,
            "starting_balance": envelope["starting_balance"],
            "budgeted_amount": envelope["budgeted_amount"],
        }
