from datetime import datetime
from typing import Any

from app.models.database import Database


class TransactionService:
    """
    Handles business logic related to transactions.
    Depends on the Database class (Dependency Inversion Principle).
    """

    def __init__(self, db: Database) -> None:
        self.db = db

    def create_transaction(
        self, envelope_id: int, amount: float, description: str, date: str, type: str
    ) -> dict[str, Any]:
        """Creates a new transaction after validating input."""
        if not self.db.get_envelope_by_id(envelope_id):
            raise ValueError(f"Envelope with ID {envelope_id} does not exist.")
        if not isinstance(amount, int | float) or amount <= 0:
            raise ValueError("Amount is required and must be a positive number.")
        if not date or not isinstance(date, str):
            raise ValueError("Date is required and must be a string (YYYY-MM-DD).")
        if type not in ["income", "expense"]:
            raise ValueError("Type must be 'income' or 'expense'.")

        # Convert string date to date object
        try:
            parsed_date = datetime.strptime(date, "%Y-%m-%d").date()
        except ValueError:
            raise ValueError("Date must be in YYYY-MM-DD format.")

        transaction_id = self.db.insert_transaction(
            envelope_id, amount, description, parsed_date, type
        )
        if transaction_id is None:
            raise ValueError("Failed to create transaction.")
        return self.get_transaction(transaction_id)

    def get_transaction(self, transaction_id: int) -> dict[str, Any]:
        """Retrieves a transaction by ID."""
        result = self.db.get_transaction_by_id(transaction_id)
        if result is None:
            raise ValueError(f"Transaction with ID {transaction_id} not found.")
        return result

    def get_transactions_by_envelope(self, envelope_id: int) -> list[dict[str, Any]]:
        """Retrieves all transactions for a specific envelope."""
        if not self.db.get_envelope_by_id(envelope_id):
            raise ValueError(f"Envelope with ID {envelope_id} does not exist.")
        return self.db.get_transactions_for_envelope(envelope_id)

    def get_all_transactions(self) -> list[dict[str, Any]]:
        """Retrieves all transactions."""
        return self.db.get_all_transactions()

    def update_transaction(
        self,
        transaction_id: int,
        envelope_id: int | None = None,
        amount: float | None = None,
        description: str | None = None,
        date: str | None = None,
        type: str | None = None,
    ) -> dict[str, Any]:
        """Updates a transaction after validation."""
        if envelope_id is not None and not self.db.get_envelope_by_id(envelope_id):
            raise ValueError(f"Envelope with ID {envelope_id} does not exist.")
        if amount is not None and (not isinstance(amount, int | float) or amount <= 0):
            raise ValueError("Amount must be a positive number.")
        if date is not None and (not isinstance(date, str) or len(date.strip()) == 0):
            raise ValueError("Date must be a string (YYYY-MM-DD).")
        if type is not None and type not in ["income", "expense"]:
            raise ValueError("Type must be 'income' or 'expense'.")

        # Convert string date to date object if provided
        parsed_date = None
        if date is not None:
            try:
                parsed_date = datetime.strptime(date, "%Y-%m-%d").date()
            except ValueError:
                raise ValueError("Date must be in YYYY-MM-DD format.")

        updated = self.db.update_transaction(
            transaction_id,
            envelope_id=envelope_id,
            amount=amount,
            description=description,
            date=parsed_date,
            type=type,
        )
        if not updated:
            raise ValueError(
                f"Transaction with ID {transaction_id} not found or no valid "
                f"fields to update."
            )
        return self.get_transaction(transaction_id)

    def delete_transaction(self, transaction_id: int) -> dict[str, str]:
        """Deletes a transaction."""
        if not self.db.get_transaction_by_id(transaction_id):
            raise ValueError(f"Transaction with ID {transaction_id} not found.")
        self.db.delete_transaction(transaction_id)
        return {
            "message": f"Transaction with ID {transaction_id} deleted successfully."
        }
