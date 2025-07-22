"""
Tests for MotherDuck integration functionality.
"""
import pytest
import os
from unittest.mock import Mock, patch, MagicMock
from app.models.database import Database
from app.config import Config, DevelopmentConfig, TestingConfig


class TestMotherDuckConfiguration:
    """Test MotherDuck configuration validation."""

    def test_validate_motherduck_token_valid(self):
        """Test validation of valid MotherDuck tokens."""
        # Test with a typical 32-character hex token
        valid_token = "1234567890abcdef1234567890abcdef"
        assert Config.validate_motherduck_token(valid_token) is True
        
        # Test with longer token
        long_token = "1234567890abcdef1234567890abcdef12345678"
        assert Config.validate_motherduck_token(long_token) is True
        
        # Test with token containing allowed special characters (hex + ._-)
        token_with_specials = "abc123def456-789abc_012.def345abc"
        assert Config.validate_motherduck_token(token_with_specials) is True

    def test_validate_motherduck_token_invalid(self):
        """Test validation of invalid MotherDuck tokens."""
        # Test with None/empty
        assert Config.validate_motherduck_token(None) is False
        assert Config.validate_motherduck_token("") is False
        
        # Test with too short token
        short_token = "abc123"
        assert Config.validate_motherduck_token(short_token) is False
        
        # Test with invalid characters
        invalid_chars_token = "abc123@def456#ghi789$jkl012%mno345^pqr678"
        assert Config.validate_motherduck_token(invalid_chars_token) is False

    def test_validate_database_mode(self):
        """Test validation of database modes."""
        assert Config.validate_database_mode('local') is True
        assert Config.validate_database_mode('cloud') is True
        assert Config.validate_database_mode('hybrid') is True
        assert Config.validate_database_mode('invalid') is False
        assert Config.validate_database_mode('') is False
        assert Config.validate_database_mode(None) is False

    def test_validate_motherduck_config_local_mode(self):
        """Test MotherDuck config validation in local mode."""
        with patch.object(Config, 'DATABASE_MODE', 'local'):
            with patch.object(Config, 'MOTHERDUCK_TOKEN', None):
                is_valid, error_msg = Config.validate_motherduck_config()
                assert is_valid is True
                assert error_msg is None

    def test_validate_motherduck_config_cloud_mode_valid(self):
        """Test MotherDuck config validation in cloud mode with valid token."""
        with patch.object(Config, 'DATABASE_MODE', 'cloud'):
            with patch.object(Config, 'MOTHERDUCK_TOKEN', '1234567890abcdef1234567890abcdef'):
                is_valid, error_msg = Config.validate_motherduck_config()
                assert is_valid is True
                assert error_msg is None

    def test_validate_motherduck_config_cloud_mode_missing_token(self):
        """Test MotherDuck config validation in cloud mode without token."""
        with patch.object(Config, 'DATABASE_MODE', 'cloud'):
            with patch.object(Config, 'MOTHERDUCK_TOKEN', None):
                is_valid, error_msg = Config.validate_motherduck_config()
                assert is_valid is False
                assert "MOTHERDUCK_TOKEN is required" in error_msg

    def test_validate_motherduck_config_invalid_mode(self):
        """Test MotherDuck config validation with invalid mode."""
        with patch.object(Config, 'DATABASE_MODE', 'invalid'):
            is_valid, error_msg = Config.validate_motherduck_config()
            assert is_valid is False
            assert "Invalid DATABASE_MODE" in error_msg


class TestDatabaseConnectionModes:
    """Test Database class with different connection modes."""

    def test_init_local_mode(self):
        """Test Database initialization in local mode."""
        db = Database(
            db_path=":memory:",
            mode="local",
            motherduck_config=None
        )
        assert db.mode == "local"
        assert db.is_cloud_connected is False
        assert db.connection_info['primary'] == 'local'
        assert db.conn is not None

    def test_init_local_mode_defaults(self):
        """Test Database initialization with default parameters."""
        db = Database(db_path=":memory:")
        assert db.mode == "local"
        assert db.is_cloud_connected is False
        assert db.connection_info['primary'] == 'local'

    def test_validate_config_invalid_mode(self):
        """Test Database config validation with invalid mode."""
        with pytest.raises(ValueError, match="Invalid database mode"):
            Database(
                db_path=":memory:",
                mode="invalid_mode",
                motherduck_config=None
            )

    def test_validate_config_cloud_mode_no_token(self):
        """Test Database config validation for cloud mode without token."""
        with pytest.raises(ValueError, match="MotherDuck token is required"):
            Database(
                db_path=":memory:",
                mode="cloud",
                motherduck_config={}
            )

    @patch('app.models.database.duckdb.connect')
    def test_cloud_mode_connection(self, mock_connect):
        """Test Database initialization in cloud mode."""
        mock_conn = Mock()
        mock_connect.return_value = mock_conn
        
        motherduck_config = {
            'token': '1234567890abcdef1234567890abcdef',
            'database': 'test_budget'
        }
        
        db = Database(
            db_path="test_budget",
            mode="cloud",
            motherduck_config=motherduck_config
        )
        
        assert db.mode == "cloud"
        assert db.is_cloud_connected is True
        assert db.connection_info['primary'] == 'cloud'
        
        # Verify the connection string was built correctly
        expected_connection_string = "md:test_budget?motherduck_token=1234567890abcdef1234567890abcdef"
        mock_connect.assert_called_once_with(expected_connection_string)

    @patch('app.models.database.duckdb.connect')
    def test_hybrid_mode_connection_success(self, mock_connect):
        """Test Database initialization in hybrid mode with successful MotherDuck attachment."""
        mock_conn = Mock()
        mock_connect.return_value = mock_conn
        mock_conn.execute.return_value = None
        
        motherduck_config = {
            'token': '1234567890abcdef1234567890abcdef',
            'database': 'test_budget'
        }
        
        db = Database(
            db_path=":memory:",
            mode="hybrid",
            motherduck_config=motherduck_config
        )
        
        assert db.mode == "hybrid"
        assert db.is_cloud_connected is True
        assert db.connection_info['primary'] == 'local'
        assert db.connection_info['cloud_attached'] is True
        
        # Verify MotherDuck was attached
        expected_attach_command = "ATTACH 'md:test_budget?motherduck_token=1234567890abcdef1234567890abcdef' AS motherduck"
        mock_conn.execute.assert_any_call(expected_attach_command)

    @patch('app.models.database.duckdb.connect')
    def test_hybrid_mode_connection_fallback(self, mock_connect):
        """Test Database initialization in hybrid mode with MotherDuck attachment failure."""
        mock_conn = Mock()
        mock_connect.return_value = mock_conn
        
        # Simulate MotherDuck attachment failure
        def side_effect(query):
            if "ATTACH" in query:
                raise Exception("MotherDuck connection failed")
            return None
        
        mock_conn.execute.side_effect = side_effect
        
        motherduck_config = {
            'token': '1234567890abcdef1234567890abcdef',
            'database': 'test_budget'
        }
        
        db = Database(
            db_path=":memory:",
            mode="hybrid",
            motherduck_config=motherduck_config
        )
        
        assert db.mode == "hybrid"
        assert db.is_cloud_connected is False
        assert db.connection_info['primary'] == 'local'
        assert db.connection_info['cloud_attached'] is False

    def test_get_connection_string_modes(self):
        """Test connection string generation for different modes."""
        db = Database(db_path=":memory:", mode="local")
        assert db._get_connection_string() == ":memory:"
        
        motherduck_config = {
            'token': 'abc123',
            'database': 'test_db'
        }
        
        # Test cloud mode connection string
        db_cloud = Database(
            db_path="test_db",
            mode="local",  # Initialize with local to avoid actual connection
            motherduck_config=motherduck_config
        )
        db_cloud.mode = "cloud"  # Change mode after initialization
        expected_cloud = "md:test_db?motherduck_token=abc123"
        assert db_cloud._get_connection_string() == expected_cloud
        
        # Test hybrid mode connection string (should be local path)
        db_hybrid = Database(db_path=":memory:", mode="local")
        db_hybrid.mode = "hybrid"
        assert db_hybrid._get_connection_string() == ":memory:"


class TestDatabaseCloudOperations:
    """Test Database cloud synchronization operations."""

    def setup_method(self):
        """Set up test database in local mode."""
        self.db = Database(db_path=":memory:", mode="local")
        
        # Add some test data
        self.db.insert_envelope("Test Category", 100.0, 50.0, "Test envelope")
        self.db.insert_transaction(1, 25.0, "Test transaction", "2025-01-01", "expense")

    def test_get_connection_status_local(self):
        """Test connection status in local mode."""
        status = self.db.get_connection_status()
        
        assert status['mode'] == 'local'
        assert status['is_cloud_connected'] is False
        assert status['connection_info']['primary'] == 'local'
        assert status['motherduck_database'] is None

    def test_get_connection_status_cloud(self):
        """Test connection status with cloud connection."""
        self.db.mode = "cloud"
        self.db.is_cloud_connected = True
        self.db.connection_info = {'primary': 'cloud'}
        self.db.motherduck_config = {'database': 'test_db'}
        
        status = self.db.get_connection_status()
        
        assert status['mode'] == 'cloud'
        assert status['is_cloud_connected'] is True
        assert status['connection_info']['primary'] == 'cloud'
        assert status['motherduck_database'] == 'test_db'

    def test_sync_to_cloud_not_connected(self):
        """Test sync_to_cloud when cloud is not connected."""
        with pytest.raises(ValueError, match="Cloud connection not available"):
            self.db.sync_to_cloud()

    def test_sync_to_cloud_cloud_mode(self):
        """Test sync_to_cloud in cloud mode (should raise error)."""
        self.db.mode = "cloud"
        self.db.is_cloud_connected = True
        
        with pytest.raises(ValueError, match="not applicable in cloud mode"):
            self.db.sync_to_cloud()

    def test_sync_from_cloud_not_connected(self):
        """Test sync_from_cloud when cloud is not connected."""
        with pytest.raises(ValueError, match="Cloud connection not available"):
            self.db.sync_from_cloud()

    def test_sync_from_cloud_cloud_mode(self):
        """Test sync_from_cloud in cloud mode (should raise error)."""
        self.db.mode = "cloud"
        self.db.is_cloud_connected = True
        
        with pytest.raises(ValueError, match="not applicable in cloud mode"):
            self.db.sync_from_cloud()

    @patch('app.models.database.Database.get_all_envelopes')
    @patch('app.models.database.Database.get_all_transactions')
    def test_sync_to_cloud_success(self, mock_get_transactions, mock_get_envelopes):
        """Test successful sync_to_cloud operation."""
        # Setup mocks
        mock_get_envelopes.return_value = [
            {'id': 1, 'category': 'Test', 'budgeted_amount': 100.0, 
             'starting_balance': 50.0, 'description': 'Test envelope'}
        ]
        mock_get_transactions.return_value = [
            {'id': 1, 'envelope_id': 1, 'amount': 25.0, 
             'description': 'Test transaction', 'date': '2025-01-01', 'type': 'expense'}
        ]
        
        # Mock cloud connection
        self.db.mode = "hybrid"
        self.db.is_cloud_connected = True
        self.db.motherduck_config = {'database': 'test_db'}
        
        # Mock the database connection execute method
        mock_conn = Mock()
        self.db.conn = mock_conn
        
        result = self.db.sync_to_cloud()
        
        assert result['envelopes_synced'] == 1
        assert result['transactions_synced'] == 1
        assert result['errors'] == []

    def test_get_sync_status_not_connected(self):
        """Test get_sync_status when cloud is not connected."""
        status = self.db.get_sync_status()
        
        assert status['cloud_available'] is False
        assert 'Cloud connection not available' in status['message']

    def test_get_sync_status_cloud_mode(self):
        """Test get_sync_status in cloud mode."""
        self.db.mode = "cloud"
        self.db.is_cloud_connected = True
        
        status = self.db.get_sync_status()
        
        assert status['cloud_available'] is True
        assert status['mode'] == 'cloud'
        assert 'no sync needed' in status['message']

    @patch('app.models.database.Database.get_all_envelopes')
    @patch('app.models.database.Database.get_all_transactions')
    def test_get_sync_status_hybrid_mode(self, mock_get_transactions, mock_get_envelopes):
        """Test get_sync_status in hybrid mode."""
        # Setup for hybrid mode
        self.db.mode = "hybrid"
        self.db.is_cloud_connected = True
        
        # Mock local data methods
        mock_get_envelopes.return_value = [{'id': 1, 'category': 'Test'}]  # 1 envelope
        mock_get_transactions.return_value = [{'id': 1, 'envelope_id': 1}]  # 1 transaction
        
        # Mock cloud table queries to return 0 for both envelope and transaction counts
        mock_conn = Mock()
        mock_conn.execute.return_value.fetchone.return_value = [0]  # Return 0 cloud records
        self.db.conn = mock_conn
        
        status = self.db.get_sync_status()
        
        assert status['cloud_available'] is True
        assert status['mode'] == 'hybrid'
        assert 'local_counts' in status
        assert 'cloud_counts' in status
        assert status['local_counts']['envelopes'] == 1  # Mocked to return 1
        assert status['local_counts']['transactions'] == 1  # Mocked to return 1
        assert status['cloud_counts']['envelopes'] == 0  # Mocked to return 0
        assert status['cloud_counts']['transactions'] == 0  # Mocked to return 0
        assert status['sync_needed'] is True  # Because local != cloud counts


class TestMCPToolsWithMotherDuck:
    """Test MCP tools integration with MotherDuck functionality."""

    def setup_method(self):
        """Set up test environment."""
        self.db = Database(db_path=":memory:", mode="local")
        
    def test_database_initialization_with_motherduck_config(self):
        """Test that MCP tools can work with MotherDuck-enabled database."""
        # This test verifies that the new Database constructor works
        # with the existing MCP tools infrastructure
        
        from app.services.envelope_service import EnvelopeService
        from app.services.transaction_service import TransactionService
        
        envelope_service = EnvelopeService(self.db)
        transaction_service = TransactionService(self.db)
        
        # Test that services work with the enhanced Database class
        envelope = envelope_service.create_envelope(
            category="Test Category",
            budgeted_amount=100.0,
            starting_balance=50.0,
            description="Test envelope"
        )
        
        assert envelope is not None
        assert 'id' in envelope
        
        # Test transaction creation with correct parameter name
        transaction = transaction_service.create_transaction(
            envelope_id=envelope['id'],
            amount=25.0,
            description="Test transaction",
            date="2025-01-01",
            type="expense"
        )
        
        assert transaction is not None


if __name__ == "__main__":
    pytest.main([__file__])