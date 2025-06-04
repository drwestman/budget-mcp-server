class TransactionService:
    """
    Handles business logic related to transactions.
    Depends on the Database class (Dependency Inversion Principle).
    """
    def __init__(self, db):
        self.db = db

    def create_transaction(self, envelope_id, amount, description, date, type):
        """Creates a new transaction after validating input."""
        if not self.db.get_envelope_by_id(envelope_id):
            raise ValueError(f"Envelope with ID {envelope_id} does not exist.")
        if not isinstance(amount, (int, float)) or amount <= 0:
            raise ValueError("Amount is required and must be a positive number.")
        if not date or not isinstance(date, str):
            raise ValueError("Date is required and must be a string (YYYY-MM-DD).")
        if type not in ['income', 'expense']:
            raise ValueError("Type must be 'income' or 'expense'.")

        transaction_id = self.db.insert_transaction(envelope_id, amount, description, date, type)
        return self.get_transaction(transaction_id)

    def get_transaction(self, transaction_id):
        """Retrieves a transaction by ID."""
        return self.db.get_transaction_by_id(transaction_id)

    def get_transactions_by_envelope(self, envelope_id):
        """Retrieves all transactions for a specific envelope."""
        if not self.db.get_envelope_by_id(envelope_id):
            raise ValueError(f"Envelope with ID {envelope_id} does not exist.")
        return self.db.get_transactions_for_envelope(envelope_id)

    def get_all_transactions(self):
        """Retrieves all transactions."""
        return self.db.get_all_transactions()

    def update_transaction(self, transaction_id, envelope_id=None, amount=None, description=None, date=None, type=None):
        """Updates a transaction after validation."""
        if envelope_id is not None and not self.db.get_envelope_by_id(envelope_id):
            raise ValueError(f"Envelope with ID {envelope_id} does not exist.")
        if amount is not None and (not isinstance(amount, (int, float)) or amount <= 0):
            raise ValueError("Amount must be a positive number.")
        if date is not None and not isinstance(date, str):
            raise ValueError("Date must be a string (YYYY-MM-DD).")
        if type is not None and type not in ['income', 'expense']:
            raise ValueError("Type must be 'income' or 'expense'.")

        updated = self.db.update_transaction(transaction_id, envelope_id, amount, description, date, type)
        if not updated:
            raise ValueError(f"Transaction with ID {transaction_id} not found or no valid fields to update.")
        return self.get_transaction(transaction_id)

    def delete_transaction(self, transaction_id):
        """Deletes a transaction."""
        if not self.db.get_transaction_by_id(transaction_id):
            raise ValueError(f"Transaction with ID {transaction_id} not found.")
        self.db.delete_transaction(transaction_id)
        return {"message": f"Transaction with ID {transaction_id} deleted successfully."}