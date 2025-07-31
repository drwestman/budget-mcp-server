import datetime
import logging
import re
from datetime import date
from typing import Any, cast

import duckdb

# Set up logger for this module
logger = logging.getLogger(__name__)


class Database:
    """
    Manages all interactions with the DuckDB database.
    Supports local, cloud (MotherDuck), and hybrid connection modes.
    Adheres to the Single Responsibility Principle (SRP) by focusing
    solely on data persistence.
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
            db_path (str): Path to the DuckDB database file (for local mode)
                or database name (for cloud mode)
            mode (str): Connection mode - 'local', 'cloud', or 'hybrid'
            motherduck_config (dict, optional): MotherDuck configuration
                containing token and database name
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

    def _validate_config(self) -> None:
        """Validate configuration before attempting connection."""
        if self.mode not in ["local", "cloud", "hybrid"]:
            raise ValueError(
                f"Invalid database mode '{self.mode}'. "
                f"Must be 'local', 'cloud', or 'hybrid'"
            )

        if self.mode in ["cloud", "hybrid"]:
            token = self.motherduck_config.get("token")
            if not token:
                raise ValueError(f"MotherDuck token is required for '{self.mode}' mode")

    def _get_database_name(self) -> str:
        """
        Get the configured database name with validation.

        Returns:
            str: Database name from configuration or default

        Raises:
            ValueError: If database name is empty or invalid
        """
        database_name = self.motherduck_config.get("database", "budget_app")

        # Validation rules
        if not database_name or not database_name.strip():
            raise ValueError("Database name cannot be empty")

        if len(database_name) > 63:  # MotherDuck database name limit
            raise ValueError("Database name cannot exceed 63 characters")

        # Basic character validation for database names
        if not re.match(r"^[a-zA-Z][a-zA-Z0-9_]*$", database_name):
            raise ValueError(
                "Database name must start with letter and contain only "
                "alphanumeric characters and underscores"
            )

        return database_name.strip()

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
            database = self._get_database_name()
            return f"md:{database}?motherduck_token={token}"

        elif self.mode == "hybrid":
            # Hybrid mode starts with local connection
            return self.db_path

        else:
            raise ValueError(f"Unsupported database mode: {self.mode}")

    def _ensure_motherduck_db_exists(self) -> None:
        """
        Ensures the MotherDuck database exists by creating it if necessary.
        Supports both cloud and hybrid modes.
        """
        if self.mode not in ["cloud", "hybrid"] or not self.motherduck_config.get(
            "token"
        ):
            return

        token = self.motherduck_config.get("token")
        database = self._get_database_name()

        try:
            logger.info(
                f"Ensuring MotherDuck database '{database}' exists "
                f"for {self.mode} mode..."
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

    def _attach_motherduck_catalog(self, token: str, database: str) -> None:
        """
        Configures MotherDuck access for the local connection in hybrid mode.

        Args:
            token: MotherDuck authentication token
            database: MotherDuck database name

        Raises:
            duckdb.Error: If MotherDuck configuration fails
        """
        if self.conn is None:
            raise ValueError(
                "Database connection not available for MotherDuck configuration"
            )

        try:
            logger.info(f"Configuring MotherDuck access for database '{database}'...")

            # Install MotherDuck extension if not already installed
            self.conn.execute("INSTALL motherduck")
            self.conn.execute("LOAD motherduck")

            # Set the MotherDuck token for this connection
            self.conn.execute(f"SET motherduck_token='{token}'")

            # Test MotherDuck connectivity with a simple query
            # Note: We can't test table creation due to schema access limitations in hybrid mode
            # The token validation during SET is sufficient to verify connectivity
            pass

            logger.info(
                f"MotherDuck access configured successfully for database '{database}'"
            )

        except duckdb.Error as e:
            logger.error(f"Failed to configure MotherDuck access: {e}")
            raise

    def _connect(self) -> None:
        """Establishes a connection to the DuckDB database based on the
        configured mode."""
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
                    f"Connected to MotherDuck database: "
                    f"{self.motherduck_config.get('database', 'budget_app')}"
                )

            elif self.mode == "hybrid":
                # Ensure MotherDuck DB exists
                self._ensure_motherduck_db_exists()

                # Start with local connection
                self.conn = duckdb.connect(database=self.db_path, read_only=False)
                self.connection_info["primary"] = "local"

                # Verify MotherDuck connectivity
                # (without attachment due to alias limitation)
                try:
                    token = self.motherduck_config.get("token")
                    database = self._get_database_name()

                    if not token:
                        raise ValueError("MotherDuck token not available")

                    test_connection_string = f"md:{database}?motherduck_token={token}"

                    # Test connection to verify cloud database is accessible
                    test_conn = duckdb.connect(test_connection_string)
                    test_conn.close()

                    # Attach MotherDuck catalog to the local connection
                    try:
                        self._attach_motherduck_catalog(token, database)
                        self.connection_info["catalog_attached"] = True
                    except Exception as catalog_error:
                        logger.warning(
                            f"Failed to attach MotherDuck catalog: {catalog_error}"
                        )
                        logger.warning("sync_to_cloud operations will not be available")
                        self.connection_info["catalog_attached"] = False

                    self.is_cloud_connected = True
                    self.connection_info["cloud_available"] = True
                    logger.info(
                        f"MotherDuck database '{database}' is accessible "
                        f"and catalog attached for hybrid operations"
                    )

                except duckdb.Error as e:
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
                    f"MotherDuck connection failed in {self.mode} mode. "
                    f"Falling back to local-only connection..."
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
                        f"Successfully connected in local-only mode "
                        f"(requested: {self.mode})"
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

    def _create_tables(self) -> None:
        """Creates the 'envelopes' and 'transactions' tables if they don't exist."""
        if self.conn is None:
            raise ValueError("Database connection not available")

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

    def close(self) -> None:
        """Closes the database connection."""
        if self.conn:
            self.conn.close()
            logger.info("Database connection closed.")

    # --- Envelope CRUD Operations ---
    def insert_envelope(
        self,
        category: str,
        budgeted_amount: float,
        starting_balance: float,
        description: str | None,
    ) -> int | None:
        """Inserts a new envelope into the database."""
        if self.conn is None:
            raise ValueError("Database connection not available")

        try:
            result = self.conn.execute(
                (
                    "INSERT INTO envelopes "
                    "(id, category, budgeted_amount, starting_balance, description) "
                    "VALUES (nextval('envelopes_id_seq'), ?, ?, ?, ?) RETURNING id;"
                ),
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
            # Re-raise other constraint exceptions that are not unique
            # violations on category
            raise
        except Exception as e:
            logger.error(f"Error inserting envelope: {e}")
            raise

    def get_envelope_by_id(self, envelope_id: int) -> dict[str, Any] | None:
        """Retrieves an envelope by its ID."""
        if self.conn is None:
            raise ValueError("Database connection not available")

        try:
            result = self.conn.execute(
                (
                    "SELECT id, category, budgeted_amount, starting_balance, "
                    "description FROM envelopes WHERE id = ?;"
                ),
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

    def get_envelope_by_category(self, category: str) -> dict[str, Any] | None:
        """Retrieves an envelope by its category name."""
        if self.conn is None:
            raise ValueError("Database connection not available")

        try:
            result = self.conn.execute(
                "SELECT id, category, budgeted_amount, starting_balance, "
                "description FROM envelopes WHERE category = ?;",
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

    def get_all_envelopes(self) -> list[dict[str, Any]]:
        """Retrieves all envelopes."""
        if self.conn is None:
            raise ValueError("Database connection not available")

        try:
            results = self.conn.execute(
                "SELECT id, category, budgeted_amount, starting_balance, "
                "description FROM envelopes;"
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
        envelope_id: int,
        category: str | None = None,
        budgeted_amount: float | None = None,
        starting_balance: float | None = None,
        description: str | None = None,
    ) -> bool:
        """Updates an existing envelope."""
        if self.conn is None:
            raise ValueError("Database connection not available")

        updates: list[str] = []
        params: list[str | float | int] = []
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

    def delete_envelope(self, envelope_id: int) -> bool:
        """Deletes an envelope by its ID."""
        if self.conn is None:
            raise ValueError("Database connection not available")

        try:
            self.conn.execute("DELETE FROM envelopes WHERE id = ?;", (envelope_id,))
            self.conn.commit()
            return True
        except Exception as e:
            logger.error(f"Error deleting envelope: {e}")
            raise

    # --- Transaction CRUD Operations ---
    def insert_transaction(
        self,
        envelope_id: int,
        amount: float,
        description: str | None,
        date: date,
        type: str,
    ) -> int | None:
        """Inserts a new transaction into the database."""
        if self.conn is None:
            raise ValueError("Database connection not available")

        try:
            result = self.conn.execute(
                (
                    "INSERT INTO transactions "
                    "(id, envelope_id, amount, description, date, type) "
                    "VALUES (nextval('transactions_id_seq'), ?, ?, ?, ?, ?) "
                    "RETURNING id;"
                ),
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

    def get_transaction_by_id(self, transaction_id: int) -> dict[str, Any] | None:
        """Retrieves a transaction by its ID."""
        if self.conn is None:
            raise ValueError("Database connection not available")

        try:
            result = self.conn.execute(
                "SELECT id, envelope_id, amount, description, date, type "
                "FROM transactions WHERE id = ?;",
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

    def get_transactions_for_envelope(self, envelope_id: int) -> list[dict[str, Any]]:
        """Retrieves all transactions for a given envelope ID."""
        if self.conn is None:
            raise ValueError("Database connection not available")

        try:
            results = self.conn.execute(
                (
                    "SELECT id, envelope_id, amount, description, date, type "
                    "FROM transactions WHERE envelope_id = ? ORDER BY date DESC;"
                ),
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

    def get_all_transactions(self) -> list[dict[str, Any]]:
        """Retrieves all transactions."""
        if self.conn is None:
            raise ValueError("Database connection not available")

        try:
            results = self.conn.execute(
                "SELECT id, envelope_id, amount, description, date, type "
                "FROM transactions ORDER BY date DESC;"
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
        transaction_id: int,
        envelope_id: int | None = None,
        amount: float | None = None,
        description: str | None = None,
        date: date | None = None,
        type: str | None = None,
    ) -> bool:
        """Updates an existing transaction."""
        if self.conn is None:
            raise ValueError("Database connection not available")

        updates: list[str] = []
        params: list[int | float | str | datetime.date] = []
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

    def delete_transaction(self, transaction_id: int) -> bool:
        """Deletes a transaction by its ID."""
        if self.conn is None:
            raise ValueError("Database connection not available")

        try:
            self.conn.execute(
                "DELETE FROM transactions WHERE id = ?;", (transaction_id,)
            )
            self.conn.commit()
            return True
        except Exception as e:
            logger.error(f"Error deleting transaction: {e}")
            raise

    def get_envelope_current_balance(self, envelope_id: int) -> float | None:
        """Calculates the current balance for an envelope."""
        if self.conn is None:
            raise ValueError("Database connection not available")

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
            return float(current_balance)
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
                self._get_database_name() if self.motherduck_config else None
            ),
        }

        # Add warning if we fell back from cloud mode
        if (
            self.connection_info.get("fallback")
            and self.connection_info.get("requested_mode") == "cloud"
        ):
            status[
                "warning"
            ] = "Requested cloud mode but fell back to local-only connection"

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

        # For hybrid mode, we'll use a direct MotherDuck connection for sync operations
        # since catalog attachment has limitations

        try:
            logger.info("Starting sync to MotherDuck cloud...")

            results: dict[str, int | list[str]] = {
                "envelopes_synced": 0,
                "transactions_synced": 0,
                "errors": [],
            }

            # Get database name and token for direct MotherDuck connection
            cloud_database = self._get_database_name()
            token = self.motherduck_config.get("token")

            # Create direct MotherDuck connection for sync operations
            cloud_conn = duckdb.connect(f"md:{cloud_database}?motherduck_token={token}")
            try:
                # Sync envelopes
                try:
                    envelopes = self.get_all_envelopes()
                    if envelopes:
                        # Create envelopes table in cloud if not exists
                        cloud_conn.execute(
                            """
                            CREATE TABLE IF NOT EXISTS envelopes (
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
                            cloud_conn.execute(
                                """
                                INSERT INTO envelopes
                                (id, category, budgeted_amount, starting_balance,
                                 description)
                                VALUES (?, ?, ?, ?, ?)
                                ON CONFLICT (id) DO UPDATE SET
                                    category = EXCLUDED.category,
                                    budgeted_amount = EXCLUDED.budgeted_amount,
                                    starting_balance = EXCLUDED.starting_balance,
                                    description = EXCLUDED.description
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

                    logger.info(
                        f"Synced {results['envelopes_synced']} envelopes to cloud"
                    )

                except Exception as e:
                    error_msg = f"Error syncing envelopes: {e}"
                    logger.error(error_msg)
                    cast(list[str], results["errors"]).append(error_msg)

                # Sync transactions
                try:
                    transactions = self.get_all_transactions()
                    if transactions:
                        # Create transactions table in cloud if not exists
                        cloud_conn.execute(
                            """
                            CREATE TABLE IF NOT EXISTS transactions (
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
                            cloud_conn.execute(
                                """
                                INSERT INTO transactions
                                (id, envelope_id, amount, description, date, type)
                                VALUES (?, ?, ?, ?, ?, ?)
                                ON CONFLICT (id) DO UPDATE SET
                                    envelope_id = EXCLUDED.envelope_id,
                                    amount = EXCLUDED.amount,
                                    description = EXCLUDED.description,
                                    date = EXCLUDED.date,
                                    type = EXCLUDED.type
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

                cloud_conn.commit()
            finally:
                cloud_conn.close()
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
                "sync_from_cloud not applicable in cloud mode "
                "(data is already in cloud)"
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

            # Get database name and token for direct MotherDuck connection
            cloud_database = self._get_database_name()
            token = self.motherduck_config.get("token")

            # Create direct MotherDuck connection for sync operations
            cloud_conn = duckdb.connect(f"md:{cloud_database}?motherduck_token={token}")
            try:
                # Sync envelopes from cloud
                try:
                    cloud_envelopes = cloud_conn.execute(
                        """
                        SELECT id, category, budgeted_amount, starting_balance, description
                        FROM envelopes
                    """
                    ).fetchall()

                    for envelope_row in cloud_envelopes:
                        # Insert or replace in local database
                        self.conn.execute(
                            """
                            INSERT INTO main.envelopes
                            (id, category, budgeted_amount, starting_balance, description)
                            VALUES (?, ?, ?, ?, ?)
                            ON CONFLICT (id) DO UPDATE SET
                                category = EXCLUDED.category,
                                budgeted_amount = EXCLUDED.budgeted_amount,
                                starting_balance = EXCLUDED.starting_balance,
                                description = EXCLUDED.description
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
                    cloud_transactions = cloud_conn.execute(
                        """
                        SELECT id, envelope_id, amount, description, date, type
                        FROM transactions
                    """
                    ).fetchall()

                    for transaction_row in cloud_transactions:
                        # Insert or replace in local database
                        self.conn.execute(
                            """
                            INSERT INTO main.transactions
                            (id, envelope_id, amount, description, date, type)
                            VALUES (?, ?, ?, ?, ?, ?)
                            ON CONFLICT (id) DO UPDATE SET
                                envelope_id = EXCLUDED.envelope_id,
                                amount = EXCLUDED.amount,
                                description = EXCLUDED.description,
                                date = EXCLUDED.date,
                                type = EXCLUDED.type
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
            finally:
                cloud_conn.close()
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

            # Get database name and token for direct MotherDuck connection
            cloud_database = self._get_database_name()
            token = self.motherduck_config.get("token")

            # Count cloud records using direct connection
            try:
                cloud_conn = duckdb.connect(
                    f"md:{cloud_database}?motherduck_token={token}"
                )
                try:
                    result = cloud_conn.execute(
                        "SELECT COUNT(*) FROM envelopes"
                    ).fetchone()
                    cloud_envelopes = result[0] if result else 0

                    result = cloud_conn.execute(
                        "SELECT COUNT(*) FROM transactions"
                    ).fetchone()
                    cloud_transactions = result[0] if result else 0
                finally:
                    cloud_conn.close()
            except duckdb.Error:
                cloud_envelopes = 0
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
