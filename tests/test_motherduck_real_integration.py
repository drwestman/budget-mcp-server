"""
Real integration tests for MotherDuck connectivity.
Tests actual connection to MotherDuck cloud service using environment configuration.
"""

import os
from datetime import date

import pytest

from app.config import Config
from app.models.database import Database


class TestMotherDuckRealIntegration:
    """Integration tests with real MotherDuck connection."""

    @pytest.fixture(autouse=True)
    def setup_method(self) -> None:
        """Setup for each test method."""
        # Verify MOTHERDUCK_TOKEN is available
        self.motherduck_token = os.getenv("MOTHERDUCK_TOKEN")
        if not self.motherduck_token:
            pytest.skip("MOTHERDUCK_TOKEN environment variable not set")

        # Verify token is valid format
        if not Config.validate_motherduck_token(self.motherduck_token):
            pytest.skip("MOTHERDUCK_TOKEN is not in valid format")

        self.motherduck_database = os.getenv("MOTHERDUCK_DATABASE", "budget_app")
        self.motherduck_config = {
            "token": self.motherduck_token,
            "database": self.motherduck_database,
        }

    def test_motherduck_token_validation(self) -> None:
        """Test that the actual token from .env is valid."""
        assert Config.validate_motherduck_token(self.motherduck_token)

    def test_motherduck_config_validation(self) -> None:
        """Test config validation with actual environment variables."""
        # Create config with environment variables
        config = Config()
        is_valid, error_msg = config.validate_motherduck_config()

        assert is_valid, f"Config validation failed: {error_msg}"
        assert error_msg is None

    def test_motherduck_cloud_mode_connection(self) -> None:
        """Test actual connection to MotherDuck in cloud mode."""
        try:
            db = Database(
                db_path=self.motherduck_database,
                mode="cloud",
                motherduck_config=self.motherduck_config,
            )

            # Verify connection was successful
            assert db.is_cloud_connected
            assert db.mode == "cloud"
            assert db.connection_info["primary"] == "cloud"

            # Test basic database functionality
            status = db.get_connection_status()
            assert status["is_cloud_connected"]
            assert status["motherduck_database"] == self.motherduck_database

            db.close()

        except Exception as e:
            pytest.fail(f"Failed to connect to MotherDuck in cloud mode: {e}")

    def test_motherduck_hybrid_mode_connection(self) -> None:
        """Test actual connection to MotherDuck in hybrid mode."""
        try:
            db = Database(
                db_path=":memory:",
                mode="hybrid",
                motherduck_config=self.motherduck_config,
            )

            # Verify connection setup
            assert db.mode == "hybrid"
            assert db.connection_info["primary"] == "local"

            # Check if cloud is available
            if db.is_cloud_connected:
                assert db.connection_info.get("cloud_available") is True
                # Test sync status if cloud is available
                sync_status = db.get_sync_status()
                assert sync_status["cloud_available"]
                assert sync_status["mode"] == "hybrid"
            else:
                # Log but don't fail if cloud isn't available
                print("Warning: MotherDuck cloud not available in hybrid mode")

            db.close()

        except Exception as e:
            pytest.fail(f"Failed to connect to MotherDuck in hybrid mode: {e}")

    def test_motherduck_database_tables_creation(self) -> None:
        """Test that tables are created properly in MotherDuck database."""
        try:
            db = Database(
                db_path=self.motherduck_database,
                mode="cloud",
                motherduck_config=self.motherduck_config,
            )

            # Tables should be created during initialization
            # Test that we can query the tables (they should exist even if empty)
            envelopes = db.get_all_envelopes()
            transactions = db.get_all_transactions()

            # These should return empty lists if tables exist but have no data
            assert isinstance(envelopes, list)
            assert isinstance(transactions, list)

            db.close()

        except Exception as e:
            pytest.fail(f"Failed to verify table creation in MotherDuck: {e}")

    def test_motherduck_basic_crud_operations(self) -> None:
        """Test basic CRUD operations on actual MotherDuck database."""
        try:
            db = Database(
                db_path=self.motherduck_database,
                mode="cloud",
                motherduck_config=self.motherduck_config,
            )

            # Test envelope creation
            test_envelope_id = db.insert_envelope(
                category="TEST_INTEGRATION_ENVELOPE",
                budgeted_amount=100.0,
                starting_balance=50.0,
                description="Integration test envelope - should be cleaned up",
            )

            assert test_envelope_id is not None

            # Test envelope retrieval
            envelope = db.get_envelope_by_id(test_envelope_id)
            assert envelope is not None
            assert envelope["category"] == "TEST_INTEGRATION_ENVELOPE"
            assert envelope["budgeted_amount"] == 100.0

            # Test transaction creation
            test_transaction_id = db.insert_transaction(
                envelope_id=test_envelope_id,
                amount=25.0,
                description="Integration test transaction",
                date=date.today(),
                type="expense",
            )

            assert test_transaction_id is not None

            # Test transaction retrieval
            transaction = db.get_transaction_by_id(test_transaction_id)
            assert transaction is not None
            assert transaction["envelope_id"] == test_envelope_id
            assert transaction["amount"] == 25.0

            # Test balance calculation
            balance = db.get_envelope_current_balance(test_envelope_id)
            assert balance == 25.0  # 50.0 starting - 25.0 expense

            # Cleanup: Delete test data
            db.delete_transaction(test_transaction_id)
            db.delete_envelope(test_envelope_id)

            db.close()

        except Exception as e:
            pytest.fail(f"CRUD operations failed on MotherDuck: {e}")

    def test_motherduck_attach_to_budget_app_db(self) -> None:
        """Specific test to verify connection to the budget_app database."""
        try:
            # Test direct connection to budget_app database
            db = Database(
                db_path="budget_app",  # Use specific database name
                mode="cloud",
                motherduck_config={
                    "token": self.motherduck_token,
                    "database": "budget_app",  # Explicitly test budget_app
                },
            )

            # Verify we're connected to the right database
            status = db.get_connection_status()
            assert status["is_cloud_connected"]
            assert status["motherduck_database"] == "budget_app"

            # Test that we can perform basic operations
            envelopes_count_before = len(db.get_all_envelopes())
            transactions_count_before = len(db.get_all_transactions())

            # These should not throw exceptions
            print(f"Current envelopes in budget_app: {envelopes_count_before}")
            print(f"Current transactions in budget_app: {transactions_count_before}")

            db.close()

        except Exception as e:
            pytest.fail(f"Failed to attach to budget_app database: {e}")


@pytest.mark.integration
class TestMotherDuckIntegrationWithConfig:
    """Integration tests using actual configuration from Config class."""

    def test_config_motherduck_integration(self) -> None:
        """Test integration using Config class directly."""
        config = Config()

        if not config.MOTHERDUCK_TOKEN:
            pytest.skip("MOTHERDUCK_TOKEN not configured")

        if config.DATABASE_MODE not in ["cloud", "hybrid"]:
            pytest.skip("DATABASE_MODE not set to cloud or hybrid")

        try:
            motherduck_config = {
                "token": config.MOTHERDUCK_TOKEN,
                "database": config.MOTHERDUCK_DATABASE,
            }

            db = Database(
                db_path=config.DATABASE_FILE,
                mode=config.DATABASE_MODE,
                motherduck_config=motherduck_config,
            )

            # Test connection
            status = db.get_connection_status()
            print(f"Connection status: {status}")

            # If we're in cloud or hybrid mode with successful connection
            if config.DATABASE_MODE in ["cloud", "hybrid"] and db.is_cloud_connected:
                # Test basic operations
                envelopes = db.get_all_envelopes()
                transactions = db.get_all_transactions()

                print(f"Found {len(envelopes)} envelopes")
                print(f"Found {len(transactions)} transactions")

                assert isinstance(envelopes, list)
                assert isinstance(transactions, list)

            db.close()

        except Exception as e:
            pytest.fail(f"Config-based integration test failed: {e}")


if __name__ == "__main__":
    # Run only the integration tests
    pytest.main([__file__, "-v", "-m", "integration"])
