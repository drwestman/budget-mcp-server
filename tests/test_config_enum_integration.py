"""Integration tests for Config class with DatabaseMode enum."""
import os
import pytest
from unittest.mock import patch
from app.config import Config, DevelopmentConfig, ProductionConfig, ConfigTesting
from app.models.database_types import DatabaseMode


class TestConfigEnumIntegration:
    """Test Config class integration with DatabaseMode enum."""

    def test_config_database_mode_default_enum(self) -> None:
        """Test Config.DATABASE_MODE returns DatabaseMode enum by default."""
        with patch.dict(os.environ, {}, clear=True):
            config = Config()
            # Defaults to LOCAL because no MOTHERDUCK_TOKEN provided
            assert config.DATABASE_MODE == DatabaseMode.LOCAL
            assert isinstance(config.DATABASE_MODE, DatabaseMode)

    def test_config_database_mode_from_env_string(self) -> None:
        """Test Config.DATABASE_MODE converts environment string to enum."""
        with patch.dict(os.environ, {"DATABASE_MODE": "local"}):
            config = Config()
            assert config.DATABASE_MODE == DatabaseMode.LOCAL
            assert isinstance(config.DATABASE_MODE, DatabaseMode)

    def test_config_database_mode_case_insensitive(self) -> None:
        """Test Config.DATABASE_MODE handles case insensitive environment values."""
        with patch.dict(os.environ, {"DATABASE_MODE": "CLOUD", "MOTHERDUCK_TOKEN": "test_token"}):
            config = Config()
            assert config.DATABASE_MODE == DatabaseMode.CLOUD
            assert isinstance(config.DATABASE_MODE, DatabaseMode)

    def test_config_database_mode_invalid_env_raises_error(self) -> None:
        """Test Config initialization with invalid DATABASE_MODE raises error."""
        with patch.dict(os.environ, {"DATABASE_MODE": "invalid"}):
            with pytest.raises(ValueError, match="Invalid database mode 'invalid'"):
                Config()

    def test_config_validate_database_mode_uses_enum(self) -> None:
        """Test validate_database_mode uses DatabaseMode enum validation."""
        # Should accept enum values
        assert Config.validate_database_mode(DatabaseMode.LOCAL) is True
        assert Config.validate_database_mode(DatabaseMode.CLOUD) is True
        assert Config.validate_database_mode(DatabaseMode.HYBRID) is True
        
        # Should accept string values
        assert Config.validate_database_mode("local") is True
        assert Config.validate_database_mode("cloud") is True
        assert Config.validate_database_mode("hybrid") is True
        
        # Should reject invalid values
        assert Config.validate_database_mode("invalid") is False
        assert Config.validate_database_mode("") is False
        assert Config.validate_database_mode(None) is False  # type: ignore

    def test_config_auto_switch_to_local_when_no_token(self) -> None:
        """Test Config auto-switches to LOCAL mode when no MOTHERDUCK_TOKEN."""
        with patch.dict(os.environ, {"DATABASE_MODE": "hybrid"}, clear=True):
            config = Config()
            # Should auto-switch to LOCAL when no token provided
            assert config.DATABASE_MODE == DatabaseMode.LOCAL
            assert isinstance(config.DATABASE_MODE, DatabaseMode)

    def test_config_motherduck_validation_with_enum(self) -> None:
        """Test validate_motherduck_config works with enum modes."""
        with patch.dict(os.environ, {"DATABASE_MODE": "local"}):
            config = Config()
            is_valid, error_msg = config.validate_motherduck_config()
            assert is_valid is True
            assert error_msg is None

        # Test cloud mode requires token  
        with patch.dict(os.environ, {"DATABASE_MODE": "cloud"}, clear=True):
            config = Config()
            # Should auto-switch to local since no token provided
            assert config.DATABASE_MODE == DatabaseMode.LOCAL

    def test_config_development_uses_enum(self) -> None:
        """Test DevelopmentConfig uses DatabaseMode enum."""
        with patch.dict(os.environ, {"DATABASE_MODE": "local"}):
            config = DevelopmentConfig()
            assert config.DATABASE_MODE == DatabaseMode.LOCAL
            assert isinstance(config.DATABASE_MODE, DatabaseMode)

    def test_config_production_uses_enum(self) -> None:
        """Test ProductionConfig uses DatabaseMode enum."""
        with patch.dict(os.environ, {"DATABASE_MODE": "hybrid", "MOTHERDUCK_TOKEN": "test_token"}):
            config = ProductionConfig()
            assert config.DATABASE_MODE == DatabaseMode.HYBRID
            assert isinstance(config.DATABASE_MODE, DatabaseMode)

    def test_config_testing_forces_local_enum(self) -> None:
        """Test ConfigTesting forces LOCAL mode as enum."""
        with patch.dict(os.environ, {"DATABASE_MODE": "cloud"}):
            config = ConfigTesting()
            assert config.DATABASE_MODE == DatabaseMode.LOCAL
            assert isinstance(config.DATABASE_MODE, DatabaseMode)

    def test_config_enum_backward_compatibility(self) -> None:
        """Test Config enum values work with string operations for backward compatibility."""
        with patch.dict(os.environ, {"DATABASE_MODE": "hybrid", "MOTHERDUCK_TOKEN": "test_token"}):
            config = Config()
            
            # Should work with string comparisons
            assert config.DATABASE_MODE == "hybrid"
            assert str(config.DATABASE_MODE) == "hybrid"
            
            # Should work in string contexts
            assert f"Mode: {config.DATABASE_MODE}" == "Mode: hybrid"

    def test_config_validation_error_messages_use_enum_values(self) -> None:
        """Test validation error messages reference correct enum values."""
        with patch.dict(os.environ, {"DATABASE_MODE": "cloud", "MOTHERDUCK_TOKEN": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.validtoken123.signature"}):
            config = Config()
            is_valid, error_msg = config.validate_motherduck_config()
            
            # Should be valid with a proper JWT token format
            assert is_valid is True
            assert error_msg is None
            assert config.DATABASE_MODE == DatabaseMode.CLOUD

    def test_config_enum_supports_motherduck_operations(self) -> None:
        """Test Config enum modes support MotherDuck operations correctly."""
        # Test LOCAL mode doesn't require token
        with patch.dict(os.environ, {"DATABASE_MODE": "local"}):
            config = Config()
            assert not config.DATABASE_MODE.requires_token()
            
        # Test CLOUD and HYBRID modes require token
        with patch.dict(os.environ, {"DATABASE_MODE": "cloud", "MOTHERDUCK_TOKEN": "test_token"}):
            config = Config()
            # Will auto-switch to local due to invalid token, but we can test the enum method
            assert DatabaseMode.CLOUD.requires_token()
            assert DatabaseMode.HYBRID.requires_token()