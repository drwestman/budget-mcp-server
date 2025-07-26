from unittest.mock import Mock, call, patch

import duckdb
import pytest

from app.models.database import Database


class TestMotherDuckCloudMode:
    """Test suite for MotherDuck cloud mode with database creation and fallback."""

    @patch("app.models.database.duckdb.connect")
    def test_cloud_mode_db_creation_success(self, mock_connect: Mock) -> None:
        """Test successful cloud mode with DB pre-creation."""
        # Mock successful connections for both creation and main connection
        mock_creation_conn = Mock()
        mock_main_conn = Mock()
        mock_connect.side_effect = [mock_creation_conn, mock_main_conn]

        # Test configuration
        motherduck_config = {"token": "test_token", "database": "test_db"}

        # Initialize database in cloud mode
        db = Database(
            db_path=":memory:", mode="cloud", motherduck_config=motherduck_config
        )

        # Verify pre-creation connection was made and closed
        assert mock_connect.call_count == 2
        mock_connect.assert_has_calls(
            [
                call(
                    "md:?motherduck_token=test_token"
                ),  # Pre-creation call without DB name
                call(
                    "md:test_db?motherduck_token=test_token"
                ),  # Main connection call with DB name
            ]
        )
        mock_creation_conn.close.assert_called_once()

        # Verify cloud connection is established
        assert db.is_cloud_connected is True
        assert db.connection_info["primary"] == "cloud"
        assert db.conn == mock_main_conn

    @patch("app.models.database.duckdb.connect")
    def test_cloud_mode_db_creation_failure_main_connection_fallback(
        self, mock_connect: Mock
    ) -> None:
        """Test cloud mode falling back to local when DB creation fails and main connection also fails."""
        # Mock failed creation, failed main connection, successful local fallback
        mock_local_conn = Mock()
        mock_connect.side_effect = [
            duckdb.Error(
                "MotherDuck DB creation failed"
            ),  # Creation fails (logged only)
            duckdb.Error(
                "MotherDuck main connection failed"
            ),  # Main connection fails (triggers fallback)
            mock_local_conn,  # Local fallback succeeds
        ]

        motherduck_config = {"token": "invalid_token", "database": "test_db"}

        # Initialize database in cloud mode
        db = Database(
            db_path="test.db", mode="cloud", motherduck_config=motherduck_config
        )

        # Verify fallback occurred
        assert db.is_cloud_connected is False
        assert db.connection_info["primary"] == "local"
        assert db.connection_info["fallback"] is True
        assert db.connection_info["requested_mode"] == "cloud"
        assert db.conn == mock_local_conn

    @patch("app.models.database.duckdb.connect")
    def test_cloud_mode_main_connection_failure_fallback(
        self, mock_connect: Mock
    ) -> None:
        """Test cloud mode falling back when main connection fails after successful creation."""
        # Mock successful creation, failed main connection, successful local fallback
        mock_creation_conn = Mock()
        mock_local_conn = Mock()
        mock_connect.side_effect = [
            mock_creation_conn,  # Creation succeeds
            duckdb.Error("Main connection failed"),  # Main connection fails
            mock_local_conn,  # Local fallback succeeds
        ]

        motherduck_config = {"token": "test_token", "database": "test_db"}

        # Initialize database in cloud mode
        db = Database(
            db_path="test.db", mode="cloud", motherduck_config=motherduck_config
        )

        # Verify creation connection was closed
        mock_creation_conn.close.assert_called_once()

        # Verify fallback occurred
        assert db.is_cloud_connected is False
        assert db.connection_info["primary"] == "local"
        assert db.connection_info["fallback"] is True
        assert db.connection_info["requested_mode"] == "cloud"

    def test_cloud_mode_connection_status_fallback_warning(self) -> None:
        """Test connection status includes fallback warnings for cloud mode."""
        with patch("app.models.database.duckdb.connect") as mock_connect:
            # Mock fallback scenario - creation fails, main connection fails, local succeeds
            mock_local_conn = Mock()
            mock_connect.side_effect = [
                duckdb.Error("Creation failed"),  # Creation fails (logged only)
                duckdb.Error(
                    "Main connection failed"
                ),  # Main connection fails (triggers fallback)
                mock_local_conn,  # Local succeeds
            ]

            motherduck_config = {"token": "test_token", "database": "test_db"}

            db = Database(
                db_path="test.db", mode="cloud", motherduck_config=motherduck_config
            )

            # Get connection status
            status = db.get_connection_status()

            # Verify warning is present
            assert "warning" in status
            assert (
                status["warning"]
                == "Requested cloud mode but fell back to local-only connection"
            )
            assert status["mode"] == "cloud"
            assert status["is_cloud_connected"] is False
            assert status["connection_info"]["requested_mode"] == "cloud"

    @patch("app.models.database.duckdb.connect")
    def test_hybrid_mode_connectivity_check_success(self, mock_connect: Mock) -> None:
        """Test that hybrid mode correctly verifies cloud availability."""
        # Mock the three connections: creation, local, and the test connection for cloud
        mock_creation_conn = Mock()
        mock_local_conn = Mock()
        mock_test_conn = Mock()
        mock_connect.side_effect = [mock_creation_conn, mock_local_conn, mock_test_conn]

        motherduck_config = {"token": "test_token", "database": "test_db"}

        # Initialize database in hybrid mode
        db = Database(
            db_path="test.db", mode="hybrid", motherduck_config=motherduck_config
        )

        # Verify that the cloud is marked as available
        assert db.is_cloud_connected is True
        assert db.connection_info.get("cloud_available") is True
        assert db.connection_info["primary"] == "local"

        # Verify the correct connections were made and closed
        assert mock_connect.call_count == 3
        mock_creation_conn.close.assert_called_once()
        mock_test_conn.close.assert_called_once()

    @patch("app.models.database.duckdb.connect")
    def test_cloud_mode_both_connections_fail(self, mock_connect: Mock) -> None:
        """Test cloud mode when both MotherDuck and local fallback fail."""
        # Mock all connections failing - need 3 calls: creation, main, local fallback
        mock_connect.side_effect = [
            duckdb.Error("MotherDuck creation failed"),  # Creation fails (logged only)
            duckdb.Error(
                "MotherDuck main connection failed"
            ),  # Main connection fails (triggers fallback)
            duckdb.Error("Local fallback failed"),  # Local fails
        ]

        motherduck_config = {"token": "test_token", "database": "test_db"}

        # Should raise exception when all connections fail
        with pytest.raises(duckdb.Error, match="Local fallback failed"):
            Database(
                db_path="invalid_path.db",
                mode="cloud",
                motherduck_config=motherduck_config,
            )

    def test_local_mode_unaffected_by_changes(self) -> None:
        """Test that local mode behavior is unchanged."""
        with patch("app.models.database.duckdb.connect") as mock_connect:
            mock_conn = Mock()
            mock_connect.return_value = mock_conn

            # Initialize database in local mode
            db = Database(db_path="test.db", mode="local")

            # Verify local connection
            mock_connect.assert_called_once_with(database="test.db", read_only=False)
            assert db.is_cloud_connected is False
            assert db.connection_info["primary"] == "local"
            assert "fallback" not in db.connection_info

    @patch("app.models.database.duckdb.connect")
    def test_cloud_mode_no_token_config_validation(self, mock_connect: Mock) -> None:
        """Test that cloud mode fails appropriately when no token is provided."""
        # Should fail during config validation, not during connection
        with pytest.raises(
            ValueError, match="MotherDuck token is required for 'cloud' mode"
        ):
            Database(db_path="test.db", mode="cloud", motherduck_config={})  # No token

        # Should not attempt any connections
        mock_connect.assert_not_called()
