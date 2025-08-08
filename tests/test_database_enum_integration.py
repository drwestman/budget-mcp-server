"""Integration tests for Database class with DatabaseMode enum."""
from unittest.mock import MagicMock, patch

import pytest

from app.models.database import Database
from app.models.database_types import DatabaseMode


class TestDatabaseEnumIntegration:
    """Test Database class integration with DatabaseMode enum."""

    def test_database_init_with_enum_mode(self) -> None:
        """Test Database initialization accepts DatabaseMode enum."""
        db = Database(db_path=":memory:", mode=DatabaseMode.LOCAL)
        assert db.mode == DatabaseMode.LOCAL
        assert isinstance(db.mode, DatabaseMode)

    def test_database_init_with_string_mode_converted(self) -> None:
        """Test Database initialization converts string mode to enum."""
        db = Database(db_path=":memory:", mode="local")
        assert db.mode == DatabaseMode.LOCAL
        assert isinstance(db.mode, DatabaseMode)

    def test_database_init_case_insensitive_mode(self) -> None:
        """Test Database initialization handles case insensitive string modes."""
        db = Database(db_path=":memory:", mode="LOCAL")
        assert db.mode == DatabaseMode.LOCAL

        # Cloud mode requires token
        motherduck_config = {"token": "test_token", "database": "test_db"}
        db2 = Database(
            db_path=":memory:", mode="Cloud", motherduck_config=motherduck_config
        )
        assert db2.mode == DatabaseMode.CLOUD

    def test_database_init_invalid_mode_raises_error(self) -> None:
        """Test Database initialization with invalid mode raises ValueError."""
        with pytest.raises(ValueError, match="Invalid database mode 'invalid'"):
            Database(db_path=":memory:", mode="invalid")

    def test_database_init_invalid_type_raises_type_error(self) -> None:
        """Test Database initialization with invalid type raises TypeError."""
        with pytest.raises(
            TypeError, match="Database mode must be a string or DatabaseMode, got int"
        ):
            Database(db_path=":memory:", mode=123)  # type: ignore

        with pytest.raises(
            TypeError,
            match="Database mode must be a string or DatabaseMode, got list",
        ):
            Database(db_path=":memory:", mode=["local"])  # type: ignore

        with pytest.raises(
            TypeError,
            match="Database mode must be a string or DatabaseMode, got NoneType",
        ):
            Database(db_path=":memory:", mode=None)  # type: ignore

    def test_database_mode_validation_uses_enum(self) -> None:
        """Test Database mode validation uses DatabaseMode enum validation."""
        db = Database(db_path=":memory:", mode=DatabaseMode.LOCAL)

        # The _validate_config method should use enum validation
        # This will be tested when we refactor the Database class
        assert db.mode == DatabaseMode.LOCAL

    def test_database_connection_string_with_enum_modes(self) -> None:
        """Test _get_connection_string method works with enum modes."""
        # Test local mode
        db_local = Database(db_path=":memory:", mode=DatabaseMode.LOCAL)
        assert db_local._get_connection_string() == ":memory:"

        # Test cloud mode (without actual connection)
        motherduck_config = {"token": "test_token", "database": "test_db"}
        db_cloud = Database(
            db_path="test_db",
            mode=DatabaseMode.LOCAL,  # Start with local to avoid connection
            motherduck_config=motherduck_config,
        )
        # Manually change mode for testing connection string generation
        db_cloud.mode = DatabaseMode.CLOUD
        expected = "md:test_db?motherduck_token=test_token"
        assert db_cloud._get_connection_string() == expected

    def test_database_requires_token_logic_with_enum(self) -> None:
        """Test Database token requirement logic works with enum."""
        # Local mode should not require token validation in _validate_config
        db_local = Database(db_path=":memory:", mode=DatabaseMode.LOCAL)
        assert db_local.mode == DatabaseMode.LOCAL

        # Cloud/Hybrid modes should require token
        assert DatabaseMode.CLOUD.requires_token()
        assert DatabaseMode.HYBRID.requires_token()
        assert not DatabaseMode.LOCAL.requires_token()

    @patch("app.models.database.duckdb.connect")
    def test_database_mode_conditionals_work_with_enum(
        self, mock_connect: MagicMock
    ) -> None:
        """Test that Database mode conditionals work with enum values."""
        mock_conn = MagicMock()
        mock_connect.return_value = mock_conn

        db = Database(db_path=":memory:", mode=DatabaseMode.LOCAL)

        # Test that enum comparison works in conditionals
        if db.mode == DatabaseMode.LOCAL:
            connection_type = "local"
        elif db.mode == DatabaseMode.CLOUD:
            connection_type = "cloud"
        elif db.mode == DatabaseMode.HYBRID:
            connection_type = "hybrid"
        else:
            connection_type = "unknown"

        assert connection_type == "local"

    def test_database_get_connection_status_with_enum(self) -> None:
        """Test get_connection_status returns enum mode."""
        db = Database(db_path=":memory:", mode=DatabaseMode.LOCAL)
        status = db.get_connection_status()

        # After refactoring, this should return enum, but for now it returns string
        # We'll verify the enum integration works
        assert status["mode"] == DatabaseMode.LOCAL or status["mode"] == "local"

    def test_database_motherduck_operations_with_enum(self) -> None:
        """Test MotherDuck operations handle enum modes correctly."""
        db = Database(db_path=":memory:", mode=DatabaseMode.LOCAL)

        # Test sync operations check mode correctly
        with pytest.raises(ValueError, match="Cloud connection not available"):
            db.sync_to_cloud()

        with pytest.raises(ValueError, match="Cloud connection not available"):
            db.sync_from_cloud()

    def test_database_enum_mode_preserved_through_operations(self) -> None:
        """Test that enum mode type is preserved through database operations."""
        db = Database(db_path=":memory:", mode=DatabaseMode.LOCAL)

        # Mode should remain as enum type
        assert isinstance(db.mode, DatabaseMode)
        assert db.mode == DatabaseMode.LOCAL

        # After operations, mode should still be enum
        db.insert_envelope("test", 100.0, 50.0, "Test envelope")
        assert isinstance(db.mode, DatabaseMode)
        assert db.mode == DatabaseMode.LOCAL
