class EnvelopeService:
    """
    Handles business logic related to envelopes.
    Depends on the Database class (Dependency Inversion Principle).
    """
    def __init__(self, db):
        self.db = db

    def create_envelope(self, category, budgeted_amount, starting_balance, description):
        """Creates a new envelope after validating input."""
        if not category or not isinstance(category, str) or len(category.strip()) == 0:
            raise ValueError("Category is required and must be a non-empty string.")
        if not isinstance(budgeted_amount, (int, float)) or budgeted_amount < 0:
            raise ValueError("Budgeted amount must be a non-negative number.")
        if not isinstance(starting_balance, (int, float)):
            raise ValueError("Starting balance must be a number.")

        # Check if category already exists
        if self.db.get_envelope_by_category(category):
            raise ValueError(f"Envelope with category '{category}' already exists.")

        envelope_id = self.db.insert_envelope(category.strip(), budgeted_amount, starting_balance, description)
        return self.get_envelope(envelope_id)

    def get_envelope(self, envelope_id):
        """Retrieves an envelope by ID, including its current balance."""
        envelope = self.db.get_envelope_by_id(envelope_id)
        if envelope:
            envelope['current_balance'] = self.db.get_envelope_current_balance(envelope_id)
        return envelope

    def get_all_envelopes(self):
        """Retrieves all envelopes, each with its current balance."""
        envelopes = self.db.get_all_envelopes()
        for envelope in envelopes:
            envelope['current_balance'] = self.db.get_envelope_current_balance(envelope['id'])
        return envelopes

    def update_envelope(self, envelope_id, category=None, budgeted_amount=None, starting_balance=None, description=None):
        """Updates an envelope after validation."""
        if category is not None:
            if not isinstance(category, str) or len(category.strip()) == 0:
                raise ValueError("Category must be a non-empty string.")
            # Check if new category already exists for another envelope
            existing_envelope = self.db.get_envelope_by_category(category.strip())
            if existing_envelope and existing_envelope['id'] != envelope_id:
                raise ValueError(f"Envelope with category '{category}' already exists.")
            category = category.strip() # Strip whitespace for consistency

        if budgeted_amount is not None and (not isinstance(budgeted_amount, (int, float)) or budgeted_amount < 0):
            raise ValueError("Budgeted amount must be a non-negative number.")
        if starting_balance is not None and not isinstance(starting_balance, (int, float)):
            raise ValueError("Starting balance must be a number.")

        updated = self.db.update_envelope(envelope_id, category, budgeted_amount, starting_balance, description)
        if not updated:
            raise ValueError(f"Envelope with ID {envelope_id} not found or no valid fields to update.")
        return self.get_envelope(envelope_id)

    def delete_envelope(self, envelope_id):
        """Deletes an envelope."""
        if not self.db.get_envelope_by_id(envelope_id):
            raise ValueError(f"Envelope with ID {envelope_id} not found.")
        self.db.delete_envelope(envelope_id)
        return {"message": f"Envelope with ID {envelope_id} deleted successfully."}