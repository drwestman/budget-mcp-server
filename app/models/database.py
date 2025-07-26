import logging
from datetime import date
from typing import Any, cast

import duckdb

# Set up logger for this module
logger = logging.getLogger(__name__)


class Database:
    """
    Manages all interactions with the DuckDB database.
    Supports local, cloud (MotherDuck), and hybrid connection modes.
    Adheres to the Single Responsibility Principle (SRP) by focusing solely on data persistence.
    """

    def __init__(
        self,
        db_path: str,
        mode: str = "local",
        motherduck_config: dict[str, str] | None = None,
    ):
        """
        Initializes the Database connection and ensures tables exist.

        Args:
            db_path (str): Path to the DuckDB database file (for local mode) or database name (for cloud mode)
            mode (str): Connection mode - 'local', 'cloud', or 'hybrid'
            motherduck_config (dict, optional): MotherDuck configuration containing token and database name
        """
        self.db_path = db_path
        self.mode = mode
        self.motherduck_config = motherduck_config or {}
        self.conn: duckdb.DuckDBPyConnection | None = None
        self.is_cloud_connected = False
        self.connection_info: dict[str, Any] = {}

        # Validate configuration before attempting connection
        self._validate_config()

        # Establish connection
        self._connect()
        self._create_tables()

        logger.info(f"Database initialized in '{mode}' mode")

    def _validate_config(self):
        """Validate configuration before attempting connection."""
        if self.mode not in ["local", "cloud", "hybrid"]:
            raise ValueError(
                f"Invalid database mode '{self.mode}'. Must be 'local', 'cloud', or 'hybrid'"
            )

        if self.mode in ["cloud", "hybrid"]:
            token = self.motherduck_config.get("token")
            if not token:
                raise ValueError(f"MotherDuck token is required for '{self.mode}' mode")

    def _get_connection_string(self) -> str:
        """
        Build the appropriate connection string based on mode.

        Returns:
            str: Connection string for DuckDB/MotherDuck
        """
        if self.mode == "local":
            return self.db_path

        elif self.mode == "cloud":
            token = self.motherduck_config.get("token")
            database = self.motherduck_config.get("database", "budget_app")
            return f"md:{database}?motherduck_token={token}"

        elif self.mode == "hybrid":
            # Hybrid mode starts with local connection
            return self.db_path

        else:
            raise ValueError(f"Unsupported database mode: {self.mode}")

    def _ensure_motherduck_db_exists(self):
        """
        Ensures the MotherDuck database exists by creating it if necessary.
        Supports both cloud and hybrid modes.
        """
        if self.mode not in ["cloud", "hybrid"] or not self.motherduck_config.get(
            "token"
        ):
            return

        token = self.motherduck_config.get("token")
        database = self.motherduck_config.get("database", "budget_app")

        try:
            logger.info(
                f"Ensuring MotherDuck database '{database}' exists for {self.mode} mode..."
            )

            # First, connect to MotherDuck without specifying a database to create it
            conn = duckdb.connect(f"md:?motherduck_token={token}")

            # Create the database if it doesn't exist
            conn.execute(f"CREATE DATABASE IF NOT EXISTS {database}")
            logger.info(f"MotherDuck database '{database}' created/verified.")

            conn.close()  # Close the creation connection

        except duckdb.Error as e:
            logger.error(
                f"Failed to ensure MotherDuck database '{database}' exists: {e}"
            )
            # Let the main connection logic handle the fallback

    def _connect(self):
        """Establishes a connection to the DuckDB database based on the configured mode."""
        try:
            connection_string = self._get_connection_string()

            logger.info(f"Connecting to database in '{self.mode}' mode...")

            if self.mode == "cloud":
                # Ensure MotherDuck DB exists before connecting
                self._ensure_motherduck_db_exists()

                # Direct cloud connection
                self.conn = duckdb.connect(connection_string)
                self.is_cloud_connected = True
                self.connection_info["primary"] = "cloud"
                logger.info(
                    f"Connected to MotherDuck database: {self.motherduck_config.get('database', 'budget_app')}"
                )

            elif self.mode == "hybrid":
                # Ensure MotherDuck DB exists
                self._ensure_motherduck_db_exists()

                # Start with local connection
                self.conn = duckdb.connect(database=self.db_path, read_only=False)
                self.connection_info["primary"] = "local"

                # Verify MotherDuck connectivity (without attachment due to alias limitation)
                try:
                    token = self.motherduck_config.get("token")
                    database = self.motherduck_config.get("database", "budget_app")
                    test_connection_string = f"md:{database}?motherduck_token={token}"

                    # Test connection to verify cloud database is accessible
                    test_conn = duckdb.connect(test_connection_string)
                    test_conn.close()

                    self.is_cloud_connected = True
                    self.connection_info["cloud_available"] = True
                    logger.info(
                        f"MotherDuck database '{database}' is accessible for hybrid operations"
                    )

                except Exception as e:
                    logger.warning(f"MotherDuck not available in hybrid mode: {e}")
                    logger.info("Continuing with local-only connection")
                    self.is_cloud_connected = False
                    self.connection_info["cloud_available"] = False

            else:  # local mode
                self.conn = duckdb.connect(database=self.db_path, read_only=False)
                self.connection_info["primary"] = "local"
                logger.info(f"Connected to local database: {self.db_path}")

            # Set common connection settings
            self.conn.execute("SET GLOBAL pandas_analyze_sample = 10000;")

        except Exception as e:
            if self.mode in ["cloud", "hybrid"]:
                logger.error(f"Failed to connect to MotherDuck: {e}")

                # Both cloud and hybrid modes can fall back to local-only
                logger.warning(
                    f"MotherDuck connection failed in {self.mode} mode. Falling back to local-only connection..."
                )
                try:
                    self.conn = duckdb.connect(database=self.db_path, read_only=False)
                    self.conn.execute("SET GLOBAL pandas_analyze_sample = 10000;")
                    self.is_cloud_connected = False
                    self.connection_info = {
                        "primary": "local",
                        "fallback": True,
                        "requested_mode": self.mode,
                    }
                    logger.warning(
                        f"Successfully connected in local-only mode (requested: {self.mode})"
                    )
                    return
                except Exception as fallback_error:
                    logger.error(
                        f"Fallback to local connection also failed: {fallback_error}"
                    )
                    raise
            else:
                logger.error(f"Error connecting to local database: {e}")
                raise

    def _create_tables(self):
        """Creates the 'envelopes' and 'transactions' tables if they don't exist."""
        try:
            self.conn.execute(
                """
                CREATE TABLE IF NOT EXISTS envelopes (
                    id INTEGER PRIMARY KEY,
                    category VARCHAR NOT NULL UNIQUE,
                    budgeted_amount DOUBLE NOT NULL,
                    starting_balance DOUBLE NOT NULL,
                    description VARCHAR
                );
            """
            )
            self.conn.execute("CREATE SEQUENCE IF NOT EXISTS envelopes_id_seq;")
            self.conn.execute(
                """
                CREATE TABLE IF NOT EXISTS transactions (
                    id INTEGER PRIMARY KEY,
                    envelope_id INTEGER NOT NULL,
                    amount DOUBLE NOT NULL,
                    description VARCHAR,
                    date DATE NOT NULL,
                    type VARCHAR NOT NULL, -- 'income' or 'expense'
                    FOREIGN KEY (envelope_id) REFERENCES envelopes(id)
                );
            """
            )
            self.conn.execute("CREATE SEQUENCE IF NOT EXISTS transactions_id_seq;")
            self.conn.commit()
            logger.info("Database tables checked/created successfully.")
        except Exception as e:
            logger.error(f"Error creating tables: {e}")
            raise

    def close(self):
        """Closes the database connection."""
        if self.conn:
            self.conn.close()
            logger.info("Database connection closed.")

    # --- Envelope CRUD Operations ---
    def insert_envelope(self, category, budgeted_amount, starting_balance, description):
        """Inserts a new envelope into the database."""
        try:
            result = self.conn.execute(
                "INSERT INTO envelopes (id, category, budgeted_amount, starting_balance, description) VALUES (nextval('envelopes_id_seq'), ?, ?, ?, ?) RETURNING id;",
                (category, budgeted_amount, starting_balance, description),
            ).fetchone()
            self.conn.commit()
            return result[0] if result else None
        except duckdb.ConstraintException as e:
            error_str = str(e)
            if (
                "violates unique constraint" in error_str.lower()
                and f"category: {category}" in error_str
            ):  # More robust check
                raise ValueError(f"Envelope with category '{category}' already exists.")
            # Re-raise other constraint exceptions that are not unique violations on category
            raise
        except Exception as e:
            logger.error(f"Error inserting envelope: {e}")
            raise

    def get_envelope_by_id(self, envelope_id):
        """Retrieves an envelope by its ID."""
        try:
            result = self.conn.execute(
                "SELECT id, category, budgeted_amount, starting_balance, description FROM envelopes WHERE id = ?;",
                (envelope_id,),
            ).fetchone()
            if result:
                return {
                    "id": result[0],
                    "category": result[1],
                    "budgeted_amount": result[2],
                    "starting_balance": result[3],
                    "description": result[4],
                }
            return None
        except Exception as e:
            logger.error(f"Error getting envelope by ID: {e}")
            raise

    def get_envelope_by_category(self, category):
        """Retrieves an envelope by its category name."""
        try:
            result = self.conn.execute(
                "SELECT id, category, budgeted_amount, starting_balance, description FROM envelopes WHERE category = ?;",
                (category,),
            ).fetchone()
            if result:
                return {
                    "id": result[0],
                    "category": result[1],
                    "budgeted_amount": result[2],
                    "starting_balance": result[3],
                    "description": result[4],
                }
            return None
        except Exception as e:
            logger.error(f"Error getting envelope by category: {e}")
            raise

    def get_all_envelopes(self):
        """Retrieves all envelopes."""
        try:
            results = self.conn.execute(
                "SELECT id, category, budgeted_amount, starting_balance, description FROM envelopes;"
            ).fetchall()
            return [
                {
                    "id": r[0],
                    "category": r[1],
                    "budgeted_amount": r[2],
                    "starting_balance": r[3],
                    "description": r[4],
                }
                for r in results
            ]
        except Exception as e:
            logger.error(f"Error getting all envelopes: {e}")
            raise

    def update_envelope(
        self,
        envelope_id,
        category=None,
        budgeted_amount=None,
        starting_balance=None,
        description=None,
    ):
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
            return False  # No fields to update

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
            logger.error(f"Error updating envelope: {e}")
            raise

    def delete_envelope(self, envelope_id):
        """Deletes an envelope by its ID."""
        try:
            self.conn.execute("DELETE FROM envelopes WHERE id = ?;", (envelope_id,))
            self.conn.commit()
            return True
        except Exception as e:
            logger.error(f"Error deleting envelope: {e}")
            raise

    # --- Transaction CRUD Operations ---
    def insert_transaction(self, envelope_id, amount, description, date, type):
        """Inserts a new transaction into the database."""
        try:
            result = self.conn.execute(
                "INSERT INTO transactions (id, envelope_id, amount, description, date, type) VALUES (nextval('transactions_id_seq'), ?, ?, ?, ?, ?) RETURNING id;",
                (envelope_id, amount, description, date, type),
            ).fetchone()
            self.conn.commit()
            return result[0] if result else None
        except duckdb.ConstraintException as e:
            if "violates foreign key constraint" in str(e).lower():  # More robust check
                raise ValueError(f"Envelope with ID {envelope_id} does not exist.")
            # Re-raise other constraint exceptions that are not FK violations
            raise
        except Exception as e:
            logger.error(f"Error inserting transaction: {e}")
            raise

    def get_transaction_by_id(self, transaction_id):
        """Retrieves a transaction by its ID."""
        try:
            result = self.conn.execute(
                "SELECT id, envelope_id, amount, description, date, type FROM transactions WHERE id = ?;",
                (transaction_id,),
            ).fetchone()
            if result:
                return {
                    "id": result[0],
                    "envelope_id": result[1],
                    "amount": result[2],
                    "description": result[3],
                    "date": (
                        result[4].isoformat()
                        if isinstance(result[4], date)
                        else result[4]
                    ),
                    "type": result[5],
                }
            return None
        except Exception as e:
            logger.error(f"Error getting transaction by ID: {e}")
            raise

    def get_transactions_for_envelope(self, envelope_id):
        """Retrieves all transactions for a given envelope ID."""
        try:
            results = self.conn.execute(
                "SELECT id, envelope_id, amount, description, date, type FROM transactions WHERE envelope_id = ? ORDER BY date DESC;",
                (envelope_id,),
            ).fetchall()
            return [
                {
                    "id": r[0],
                    "envelope_id": r[1],
                    "amount": r[2],
                    "description": r[3],
                    "date": r[4].isoformat() if isinstance(r[4], date) else r[4],
                    "type": r[5],
                }
                for r in results
            ]
        except Exception as e:
            logger.error(f"Error getting transactions for envelope: {e}")
            raise

    def get_all_transactions(self):
        """Retrieves all transactions."""
        try:
            results = self.conn.execute(
                "SELECT id, envelope_id, amount, description, date, type FROM transactions ORDER BY date DESC;"
            ).fetchall()
            return [
                {
                    "id": r[0],
                    "envelope_id": r[1],
                    "amount": r[2],
                    "description": r[3],
                    "date": r[4].isoformat() if isinstance(r[4], date) else r[4],
                    "type": r[5],
                }
                for r in results
            ]
        except Exception as e:
            logger.error(f"Error getting all transactions: {e}")
            raise

    def update_transaction(
        self,
        transaction_id,
        envelope_id=None,
        amount=None,
        description=None,
        date=None,
        type=None,
    ):
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
            return False  # No fields to update

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
            logger.error(f"Error updating transaction: {e}")
            raise

    def delete_transaction(self, transaction_id):
        """Deletes a transaction by its ID."""
        try:
            self.conn.execute(
                "DELETE FROM transactions WHERE id = ?;", (transaction_id,)
            )
            self.conn.commit()
            return True
        except Exception as e:
            logger.error(f"Error deleting transaction: {e}")
            raise

    def get_envelope_current_balance(self, envelope_id):
        """Calculates the current balance for an envelope."""
        try:
            envelope = self.get_envelope_by_id(envelope_id)
            if not envelope:
                return None

            starting_balance = envelope["starting_balance"]
            transactions = self.get_transactions_for_envelope(envelope_id)

            current_balance = starting_balance
            for t in transactions:
                if t["type"] == "expense":
                    current_balance -= t["amount"]
                elif t["type"] == "income":
                    current_balance += t["amount"]
            return current_balance
        except Exception as e:
            logger.error(
                f"Error calculating current balance for envelope {envelope_id}: {e}"
            )
            raise

    # --- MotherDuck Cloud Operations ---

    def get_connection_status(self) -> dict[str, Any]:
        """
        Get current connection status and information.

        Returns:
            dict: Connection status information
        """
        status = {
            "mode": self.mode,
            "is_cloud_connected": self.is_cloud_connected,
            "connection_info": self.connection_info.copy(),
            "motherduck_database": (
                self.motherduck_config.get("database", "budget_app")
                if self.motherduck_config
                else None
            ),
        }

        # Add warning if we fell back from cloud mode
        if (
            self.connection_info.get("fallback")
            and self.connection_info.get("requested_mode") == "cloud"
        ):
            status["warning"] = (
                "Requested cloud mode but fell back to local-only connection"
            )

        return status

    def sync_to_cloud(self) -> dict[str, Any]:
        """
        Synchronize local data to MotherDuck cloud database.
        Only available in hybrid mode or when cloud connection is available.

        Returns:
            dict: Sync operation results
        """
        if not self.is_cloud_connected:
            raise ValueError("Cloud connection not available for synchronization")

        if self.mode == "cloud":
            raise ValueError(
                "sync_to_cloud not applicable in cloud mode (data is already in cloud)"
            )

        if self.conn is None:
            raise ValueError("Database connection not available")

        try:
            logger.info("Starting sync to MotherDuck cloud...")

            results: dict[str, int | list[str]] = {
                "envelopes_synced": 0,
                "transactions_synced": 0,
                "errors": [],
            }

            # Get database name for cloud operations

            # Sync envelopes
            try:
                envelopes = self.get_all_envelopes()
                if envelopes:
                    # Create envelopes table in cloud if not exists
                    self.conn.execute(
                        """
                        CREATE TABLE IF NOT EXISTS motherduck.main.envelopes (
                            id INTEGER PRIMARY KEY,
                            category VARCHAR NOT NULL UNIQUE,
                            budgeted_amount DOUBLE NOT NULL,
                            starting_balance DOUBLE NOT NULL,
                            description VARCHAR
                        )
                    """
                    )

                    # Insert or replace envelopes in cloud
                    for envelope in envelopes:
                        self.conn.execute(
                            """
                            INSERT OR REPLACE INTO motherduck.main.envelopes 
                            (id, category, budgeted_amount, starting_balance, description)
                            VALUES (?, ?, ?, ?, ?)
                        """,
                            (
                                envelope["id"],
                                envelope["category"],
                                envelope["budgeted_amount"],
                                envelope["starting_balance"],
                                envelope["description"],
                            ),
                        )
                        results["envelopes_synced"] = (
                            cast(int, results["envelopes_synced"]) + 1
                        )

                logger.info(f"Synced {results['envelopes_synced']} envelopes to cloud")

            except Exception as e:
                error_msg = f"Error syncing envelopes: {e}"
                logger.error(error_msg)
                cast(list[str], results["errors"]).append(error_msg)

            # Sync transactions
            try:
                transactions = self.get_all_transactions()
                if transactions:
                    # Create transactions table in cloud if not exists
                    self.conn.execute(
                        """
                        CREATE TABLE IF NOT EXISTS motherduck.main.transactions (
                            id INTEGER PRIMARY KEY,
                            envelope_id INTEGER NOT NULL,
                            amount DOUBLE NOT NULL,
                            description VARCHAR,
                            date DATE NOT NULL,
                            type VARCHAR NOT NULL
                        )
                    """
                    )

                    # Insert or replace transactions in cloud
                    for transaction in transactions:
                        self.conn.execute(
                            """
                            INSERT OR REPLACE INTO motherduck.main.transactions 
                            (id, envelope_id, amount, description, date, type)
                            VALUES (?, ?, ?, ?, ?, ?)
                        """,
                            (
                                transaction["id"],
                                transaction["envelope_id"],
                                transaction["amount"],
                                transaction["description"],
                                transaction["date"],
                                transaction["type"],
                            ),
                        )
                        results["transactions_synced"] = (
                            cast(int, results["transactions_synced"]) + 1
                        )

                logger.info(
                    f"Synced {results['transactions_synced']} transactions to cloud"
                )

            except Exception as e:
                error_msg = f"Error syncing transactions: {e}"
                logger.error(error_msg)
                cast(list[str], results["errors"]).append(error_msg)

            self.conn.commit()
            logger.info("Successfully completed sync to MotherDuck cloud")

            return results

        except Exception as e:
            logger.error(f"Failed to sync to cloud: {e}")
            raise

    def sync_from_cloud(self) -> dict[str, Any]:
        """
        Synchronize data from MotherDuck cloud to local database.
        Only available in hybrid mode or when cloud connection is available.

        Returns:
            dict: Sync operation results
        """
        if not self.is_cloud_connected:
            raise ValueError("Cloud connection not available for synchronization")

        if self.mode == "cloud":
            raise ValueError(
                "sync_from_cloud not applicable in cloud mode (data is already in cloud)"
            )

        if self.conn is None:
            raise ValueError("Database connection not available")

        try:
            logger.info("Starting sync from MotherDuck cloud...")

            results: dict[str, int | list[str]] = {
                "envelopes_synced": 0,
                "transactions_synced": 0,
                "errors": [],
            }

            # Sync envelopes from cloud
            try:
                cloud_envelopes = self.conn.execute(
                    """
                    SELECT id, category, budgeted_amount, starting_balance, description 
                    FROM motherduck.main.envelopes
                """
                ).fetchall()

                for envelope_row in cloud_envelopes:
                    # Insert or replace in local database
                    self.conn.execute(
                        """
                        INSERT OR REPLACE INTO main.envelopes 
                        (id, category, budgeted_amount, starting_balance, description)
                        VALUES (?, ?, ?, ?, ?)
                    """,
                        envelope_row,
                    )
                    results["envelopes_synced"] = (
                        cast(int, results["envelopes_synced"]) + 1
                    )

                logger.info(
                    f"Synced {results['envelopes_synced']} envelopes from cloud"
                )

            except Exception as e:
                error_msg = f"Error syncing envelopes from cloud: {e}"
                logger.error(error_msg)
                cast(list[str], results["errors"]).append(error_msg)

            # Sync transactions from cloud
            try:
                cloud_transactions = self.conn.execute(
                    """
                    SELECT id, envelope_id, amount, description, date, type 
                    FROM motherduck.main.transactions
                """
                ).fetchall()

                for transaction_row in cloud_transactions:
                    # Insert or replace in local database
                    self.conn.execute(
                        """
                        INSERT OR REPLACE INTO main.transactions 
                        (id, envelope_id, amount, description, date, type)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """,
                        transaction_row,
                    )
                    results["transactions_synced"] = (
                        cast(int, results["transactions_synced"]) + 1
                    )

                logger.info(
                    f"Synced {results['transactions_synced']} transactions from cloud"
                )

            except Exception as e:
                error_msg = f"Error syncing transactions from cloud: {e}"
                logger.error(error_msg)
                cast(list[str], results["errors"]).append(error_msg)

            self.conn.commit()
            logger.info("Successfully completed sync from MotherDuck cloud")

            return results

        except Exception as e:
            logger.error(f"Failed to sync from cloud: {e}")
            raise

    def get_sync_status(self) -> dict[str, Any]:
        """
        Get synchronization status between local and cloud databases.

        Returns:
            dict: Sync status information
        """
        if not self.is_cloud_connected:
            return {
                "cloud_available": False,
                "message": "Cloud connection not available",
            }

        if self.mode == "cloud":
            return {
                "cloud_available": True,
                "mode": "cloud",
                "message": "Operating in cloud mode - no sync needed",
            }

        if self.conn is None:
            return {
                "cloud_available": False,
                "message": "Database connection not available",
            }

        try:
            # Count local records
            local_envelopes = len(self.get_all_envelopes())
            local_transactions = len(self.get_all_transactions())

            # Count cloud records
            try:
                result = self.conn.execute(
                    "SELECT COUNT(*) FROM motherduck.main.envelopes"
                ).fetchone()
                cloud_envelopes = result[0] if result else 0
            except duckdb.Error:
                cloud_envelopes = 0

            try:
                result = self.conn.execute(
                    "SELECT COUNT(*) FROM motherduck.main.transactions"
                ).fetchone()
                cloud_transactions = result[0] if result else 0
            except duckdb.Error:
                cloud_transactions = 0

            return {
                "cloud_available": True,
                "mode": self.mode,
                "local_counts": {
                    "envelopes": local_envelopes,
                    "transactions": local_transactions,
                },
                "cloud_counts": {
                    "envelopes": cloud_envelopes,
                    "transactions": cloud_transactions,
                },
                "sync_needed": (
                    local_envelopes != cloud_envelopes
                    or local_transactions != cloud_transactions
                ),
            }

        except Exception as e:
            logger.error(f"Error getting sync status: {e}")
            return {"cloud_available": True, "error": str(e)}
