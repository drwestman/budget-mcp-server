import duckdb
from datetime import date

class Database:
    """
    Manages all interactions with the DuckDB database.
    Adheres to the Single Responsibility Principle (SRP) by focusing solely on data persistence.
    """
    def __init__(self, db_path):
        """
        Initializes the Database connection and ensures tables exist.
        Args:
            db_path (str): Path to the DuckDB database file.
        """
        self.db_path = db_path
        self.conn = None
        self._connect()
        self._create_tables()

    def _connect(self):
        """Establishes a connection to the DuckDB database."""
        try:
            self.conn = duckdb.connect(database=self.db_path, read_only=False)
            self.conn.execute("SET GLOBAL pandas_analyze_sample = 10000;") # Ensure proper type inference for pandas
        except Exception as e:
            print(f"Error connecting to database: {e}")
            raise

    def _create_tables(self):
        """Creates the 'envelopes' and 'transactions' tables if they don't exist."""
        try:
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS envelopes (
                    id INTEGER PRIMARY KEY,
                    category VARCHAR NOT NULL UNIQUE,
                    budgeted_amount DOUBLE NOT NULL,
                    starting_balance DOUBLE NOT NULL,
                    description VARCHAR
                );
            """)
            self.conn.execute("CREATE SEQUENCE IF NOT EXISTS envelopes_id_seq;")
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS transactions (
                    id INTEGER PRIMARY KEY,
                    envelope_id INTEGER NOT NULL,
                    amount DOUBLE NOT NULL,
                    description VARCHAR,
                    date DATE NOT NULL,
                    type VARCHAR NOT NULL, -- 'income' or 'expense'
                    FOREIGN KEY (envelope_id) REFERENCES envelopes(id)
                );
            """)
            self.conn.execute("CREATE SEQUENCE IF NOT EXISTS transactions_id_seq;")
            self.conn.commit()
            print("Database tables checked/created successfully.")
        except Exception as e:
            print(f"Error creating tables: {e}")
            raise

    def close(self):
        """Closes the database connection."""
        if self.conn:
            self.conn.close()
            print("Database connection closed.")

    # --- Envelope CRUD Operations ---
    def insert_envelope(self, category, budgeted_amount, starting_balance, description):
        """Inserts a new envelope into the database."""
        try:
            result = self.conn.execute(
                "INSERT INTO envelopes (id, category, budgeted_amount, starting_balance, description) VALUES (nextval('envelopes_id_seq'), ?, ?, ?, ?) RETURNING id;",
                (category, budgeted_amount, starting_balance, description)
            ).fetchone()
            self.conn.commit()
            return result[0] if result else None
        except duckdb.ConstraintException as e:
            error_str = str(e)
            if "violates unique constraint" in error_str.lower() and f"category: {category}" in error_str: # More robust check
                raise ValueError(f"Envelope with category '{category}' already exists.")
            # Re-raise other constraint exceptions that are not unique violations on category
            raise
        except Exception as e:
            print(f"Error inserting envelope: {e}")
            raise

    def get_envelope_by_id(self, envelope_id):
        """Retrieves an envelope by its ID."""
        try:
            result = self.conn.execute(
                "SELECT id, category, budgeted_amount, starting_balance, description FROM envelopes WHERE id = ?;",
                (envelope_id,)
            ).fetchone()
            if result:
                return {
                    "id": result[0],
                    "category": result[1],
                    "budgeted_amount": result[2],
                    "starting_balance": result[3],
                    "description": result[4]
                }
            return None
        except Exception as e:
            print(f"Error getting envelope by ID: {e}")
            raise

    def get_envelope_by_category(self, category):
        """Retrieves an envelope by its category name."""
        try:
            result = self.conn.execute(
                "SELECT id, category, budgeted_amount, starting_balance, description FROM envelopes WHERE category = ?;",
                (category,)
            ).fetchone()
            if result:
                return {
                    "id": result[0],
                    "category": result[1],
                    "budgeted_amount": result[2],
                    "starting_balance": result[3],
                    "description": result[4]
                }
            return None
        except Exception as e:
            print(f"Error getting envelope by category: {e}")
            raise

    def get_all_envelopes(self):
        """Retrieves all envelopes."""
        try:
            results = self.conn.execute(
                "SELECT id, category, budgeted_amount, starting_balance, description FROM envelopes;"
            ).fetchall()
            return [{
                "id": r[0],
                "category": r[1],
                "budgeted_amount": r[2],
                "starting_balance": r[3],
                "description": r[4]
            } for r in results]
        except Exception as e:
            print(f"Error getting all envelopes: {e}")
            raise

    def update_envelope(self, envelope_id, category=None, budgeted_amount=None, starting_balance=None, description=None):
        """Updates an existing envelope."""
        updates = []
        params = []
        if category is not None:
            updates.append("category = ?")
            params.append(category)
        if budgeted_amount is not None:
            updates.append("budgeted_amount = ?")
            params.append(budgeted_amount)
        if starting_balance is not None:
            updates.append("starting_balance = ?")
            params.append(starting_balance)
        if description is not None:
            updates.append("description = ?")
            params.append(description)

        if not updates:
            return False # No fields to update

        params.append(envelope_id)
        query = f"UPDATE envelopes SET {', '.join(updates)} WHERE id = ?;"
        try:
            self.conn.execute(query, tuple(params))
            self.conn.commit()
            return True
        except duckdb.ConstraintException as e:
            if "UNIQUE constraint failed: envelopes.category" in str(e):
                raise ValueError(f"Envelope with category '{category}' already exists.")
            raise
        except Exception as e:
            print(f"Error updating envelope: {e}")
            raise

    def delete_envelope(self, envelope_id):
        """Deletes an envelope by its ID."""
        try:
            self.conn.execute("DELETE FROM envelopes WHERE id = ?;", (envelope_id,))
            self.conn.commit()
            return True
        except Exception as e:
            print(f"Error deleting envelope: {e}")
            raise

    # --- Transaction CRUD Operations ---
    def insert_transaction(self, envelope_id, amount, description, date, type):
        """Inserts a new transaction into the database."""
        try:
            result = self.conn.execute(
                "INSERT INTO transactions (id, envelope_id, amount, description, date, type) VALUES (nextval('transactions_id_seq'), ?, ?, ?, ?, ?) RETURNING id;",
                (envelope_id, amount, description, date, type)
            ).fetchone()
            self.conn.commit()
            return result[0] if result else None
        except duckdb.ConstraintException as e:
            if "violates foreign key constraint" in str(e).lower(): # More robust check
                raise ValueError(f"Envelope with ID {envelope_id} does not exist.")
            # Re-raise other constraint exceptions that are not FK violations
            raise
        except Exception as e:
            print(f"Error inserting transaction: {e}")
            raise

    def get_transaction_by_id(self, transaction_id):
        """Retrieves a transaction by its ID."""
        try:
            result = self.conn.execute(
                "SELECT id, envelope_id, amount, description, date, type FROM transactions WHERE id = ?;",
                (transaction_id,)
            ).fetchone()
            if result:
                return {
                    "id": result[0],
                    "envelope_id": result[1],
                    "amount": result[2],
                    "description": result[3],
                    "date": result[4].isoformat() if isinstance(result[4], date) else result[4],
                    "type": result[5]
                }
            return None
        except Exception as e:
            print(f"Error getting transaction by ID: {e}")
            raise

    def get_transactions_for_envelope(self, envelope_id):
        """Retrieves all transactions for a given envelope ID."""
        try:
            results = self.conn.execute(
                "SELECT id, envelope_id, amount, description, date, type FROM transactions WHERE envelope_id = ? ORDER BY date DESC;",
                (envelope_id,)
            ).fetchall()
            return [{
                "id": r[0],
                "envelope_id": r[1],
                "amount": r[2],
                "description": r[3],
                "date": r[4].isoformat() if isinstance(r[4], date) else r[4],
                "type": r[5]
            } for r in results]
        except Exception as e:
            print(f"Error getting transactions for envelope: {e}")
            raise

    def get_all_transactions(self):
        """Retrieves all transactions."""
        try:
            results = self.conn.execute(
                "SELECT id, envelope_id, amount, description, date, type FROM transactions ORDER BY date DESC;"
            ).fetchall()
            return [{
                "id": r[0],
                "envelope_id": r[1],
                "amount": r[2],
                "description": r[3],
                "date": r[4].isoformat() if isinstance(r[4], date) else r[4],
                "type": r[5]
            } for r in results]
        except Exception as e:
            print(f"Error getting all transactions: {e}")
            raise

    def update_transaction(self, transaction_id, envelope_id=None, amount=None, description=None, date=None, type=None):
        """Updates an existing transaction."""
        updates = []
        params = []
        if envelope_id is not None:
            updates.append("envelope_id = ?")
            params.append(envelope_id)
        if amount is not None:
            updates.append("amount = ?")
            params.append(amount)
        if description is not None:
            updates.append("description = ?")
            params.append(description)
        if date is not None:
            updates.append("date = ?")
            params.append(date)
        if type is not None:
            updates.append("type = ?")
            params.append(type)

        if not updates:
            return False # No fields to update

        params.append(transaction_id)
        query = f"UPDATE transactions SET {', '.join(updates)} WHERE id = ?;"
        try:
            self.conn.execute(query, tuple(params))
            self.conn.commit()
            return True
        except duckdb.ConstraintException as e:
            if "FOREIGN KEY constraint failed" in str(e):
                raise ValueError(f"Envelope with ID {envelope_id} does not exist.")
            raise
        except Exception as e:
            print(f"Error updating transaction: {e}")
            raise

    def delete_transaction(self, transaction_id):
        """Deletes a transaction by its ID."""
        try:
            self.conn.execute("DELETE FROM transactions WHERE id = ?;", (transaction_id,))
            self.conn.commit()
            return True
        except Exception as e:
            print(f"Error deleting transaction: {e}")
            raise

    def get_envelope_current_balance(self, envelope_id):
        """Calculates the current balance for an envelope."""
        try:
            envelope = self.get_envelope_by_id(envelope_id)
            if not envelope:
                return None

            starting_balance = envelope['starting_balance']
            transactions = self.get_transactions_for_envelope(envelope_id)

            current_balance = starting_balance
            for t in transactions:
                if t['type'] == 'expense':
                    current_balance -= t['amount']
                elif t['type'] == 'income':
                    current_balance += t['amount']
            return current_balance
        except Exception as e:
            print(f"Error calculating current balance for envelope {envelope_id}: {e}")
            raise