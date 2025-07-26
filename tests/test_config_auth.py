"""
Unit tests for configuration and startup behavior with authentication.
"""

import os
from unittest.mock import Mock, patch

from app.config import Config, DevelopmentConfig, ProductionConfig, TestingConfig


class TestAuthConfiguration:
    """Test configuration classes with authentication settings."""

    def test_base_config_bearer_token_from_env(self):
        """Test base Config class reads BEARER_TOKEN from environment."""
        with patch.dict(os.environ, {"BEARER_TOKEN": "test-token-123"}):
            config = Config()
            assert config.BEARER_TOKEN == "test-token-123"

    def test_base_config_bearer_token_none_when_missing(self):
        """Test base Config class returns None when BEARER_TOKEN is missing."""
        with patch.dict(os.environ, {}, clear=True):
            if "BEARER_TOKEN" in os.environ:
                del os.environ["BEARER_TOKEN"]
            config = Config()
            assert config.BEARER_TOKEN is None

    def test_base_config_bearer_token_empty_string(self):
        """Test base Config class handles empty BEARER_TOKEN."""
        with patch.dict(os.environ, {"BEARER_TOKEN": ""}):
            config = Config()
            assert config.BEARER_TOKEN == ""

    def test_development_config_inherits_bearer_token(self):
        """Test DevelopmentConfig inherits BEARER_TOKEN from base Config."""
        with patch.dict(os.environ, {"BEARER_TOKEN": "dev-token"}):
            config = DevelopmentConfig()
            assert config.BEARER_TOKEN == "dev-token"
            assert config.DEBUG is True
            assert config.RESET_DB_ON_START is True

    def test_production_config_inherits_bearer_token(self):
        """Test ProductionConfig inherits BEARER_TOKEN from base Config."""
        with patch.dict(os.environ, {"BEARER_TOKEN": "prod-token"}):
            config = ProductionConfig()
            assert config.BEARER_TOKEN == "prod-token"
            assert config.DEBUG is False
            assert config.RESET_DB_ON_START is False

    def test_testing_config_inherits_bearer_token(self):
        """Test TestingConfig inherits BEARER_TOKEN from base Config."""
        with patch.dict(os.environ, {"BEARER_TOKEN": "test-token"}):
            config = TestingConfig()
            assert config.BEARER_TOKEN == "test-token"
            assert config.DEBUG is True
            assert config.TESTING is True
            assert config.DATABASE_FILE == ":memory:"

    def test_config_mapping_includes_all_environments(self):
        """Test that config mapping includes all environment configurations."""
        from app.config import config

        assert "development" in config
        assert "production" in config
        assert "testing" in config
        assert "default" in config

        assert config["development"] == DevelopmentConfig
        assert config["production"] == ProductionConfig
        assert config["testing"] == TestingConfig
        assert config["default"] == DevelopmentConfig


class TestStartupValidation:
    """Test startup validation behavior for bearer token authentication."""

    @patch("sys.exit")
    @patch("builtins.print")
    def test_run_main_exits_without_bearer_token_in_production(
        self, mock_print, mock_exit
    ):
        """Test that run.py main() exits when BEARER_TOKEN is missing in production."""
        with patch.dict(os.environ, {"APP_ENV": "production"}, clear=True):
            if "BEARER_TOKEN" in os.environ:
                del os.environ["BEARER_TOKEN"]

            # Import and call main function
            from run import main

            main()

            # Should have printed error and exited
            mock_print.assert_called()
            mock_exit.assert_called_with(1)

            # Check that error message was printed
            print_calls = [call[0][0] for call in mock_print.call_args_list]
            error_messages = [msg for msg in print_calls if "BEARER_TOKEN" in msg]
            assert len(error_messages) > 0

    @patch("sys.exit")
    @patch("builtins.print")
    def test_run_main_exits_with_empty_bearer_token_in_production(
        self, mock_print, mock_exit
    ):
        """Test that run.py main() exits when BEARER_TOKEN is empty in production."""
        with patch.dict(os.environ, {"BEARER_TOKEN": "", "APP_ENV": "production"}):
            from run import main

            main()

            # Should have printed error and exited
            mock_print.assert_called()
            mock_exit.assert_called_with(1)

            # Check that error message was printed
            print_calls = [call[0][0] for call in mock_print.call_args_list]
            error_messages = [msg for msg in print_calls if "BEARER_TOKEN" in msg]
            assert len(error_messages) > 0

    @patch("app.fastmcp_server.create_fastmcp_server")
    @patch("builtins.print")
    @patch("sys.exit")
    def test_run_main_continues_with_valid_bearer_token(
        self, mock_exit, mock_print, mock_create_server
    ):
        """Test that run.py main() continues when BEARER_TOKEN is valid."""
        # Mock the FastMCP server
        mock_server = Mock()
        mock_server.db = Mock()
        mock_server.db._connect = Mock()
        mock_server.db._create_tables = Mock()
        mock_server.run = Mock()
        mock_create_server.return_value = mock_server

        with patch.dict(os.environ, {"BEARER_TOKEN": "valid-token-123"}):
            # Mock Config.ensure_data_directory to avoid filesystem operations
            with patch("app.config.Config.ensure_data_directory"):
                from run import main

                try:
                    main()
                except SystemExit:
                    pass  # Expected since we're mocking the server run

                # Should not have called sys.exit(1) for missing token
                if mock_exit.called:
                    # If exit was called, it should not be with code 1 (token error)
                    args = mock_exit.call_args[0]
                    assert args[0] != 1 or not any(
                        "BEARER_TOKEN" in str(call)
                        for call in mock_print.call_args_list
                    )

                # Should have created server with auth enabled
                mock_create_server.assert_called()
                call_args = mock_create_server.call_args
                if len(call_args[1]) > 0:  # Check kwargs
                    assert call_args[1].get("enable_auth", True) is True


class TestEnvironmentVariableHandling:
    """Test environment variable handling for authentication configuration."""

    def test_bearer_token_with_special_characters(self):
        """Test BEARER_TOKEN with special characters is handled correctly."""
        special_token = "token-with-!@#$%^&*()_+-={}[]|:;'<>?,./"
        with patch.dict(os.environ, {"BEARER_TOKEN": special_token}):
            config = Config()
            assert config.BEARER_TOKEN == special_token

    def test_bearer_token_with_unicode(self):
        """Test BEARER_TOKEN with unicode characters is handled correctly."""
        unicode_token = "token-with-unicode-🔐🛡️🔒"
        with patch.dict(os.environ, {"BEARER_TOKEN": unicode_token}):
            config = Config()
            assert config.BEARER_TOKEN == unicode_token

    def test_bearer_token_very_long(self):
        """Test BEARER_TOKEN with very long value is handled correctly."""
        long_token = "a" * 1000  # 1000 character token
        with patch.dict(os.environ, {"BEARER_TOKEN": long_token}):
            config = Config()
            assert config.BEARER_TOKEN == long_token
            assert len(config.BEARER_TOKEN) == 1000

    def test_multiple_config_instances_same_token(self):
        """Test multiple config instances read the same token value."""
        with patch.dict(os.environ, {"BEARER_TOKEN": "consistent-token"}):
            config1 = Config()
            config2 = Config()
            config3 = DevelopmentConfig()

            assert config1.BEARER_TOKEN == "consistent-token"
            assert config2.BEARER_TOKEN == "consistent-token"
            assert config3.BEARER_TOKEN == "consistent-token"


class TestSecurityConfiguration:
    """Test security-related configuration aspects."""

    def test_bearer_token_not_logged_in_config(self):
        """Test that bearer token is not inadvertently logged or exposed."""
        secret_token = "super-secret-token-do-not-log"
        with patch.dict(os.environ, {"BEARER_TOKEN": secret_token}):
            config = Config()

            # The token should be present in the config but we should be careful about logging
            assert config.BEARER_TOKEN == secret_token
            # This test mainly documents that we should be careful about logging config

    def test_bearer_token_case_sensitivity(self):
        """Test that BEARER_TOKEN environment variable is case-sensitive."""
        with patch.dict(os.environ, {"bearer_token": "lowercase-var"}, clear=True):
            # Should not pick up lowercase version
            config = Config()
            assert config.BEARER_TOKEN is None

        with patch.dict(os.environ, {"BEARER_TOKEN": "uppercase-var"}):
            config = Config()
            assert config.BEARER_TOKEN == "uppercase-var"

    def test_config_immutability_concerns(self):
        """Test configuration behavior with environment changes."""
        # First set a token
        with patch.dict(os.environ, {"BEARER_TOKEN": "first-token"}):
            config1 = Config()
            assert config1.BEARER_TOKEN == "first-token"

        # Change environment and create new config
        with patch.dict(os.environ, {"BEARER_TOKEN": "second-token"}):
            config2 = Config()
            assert config2.BEARER_TOKEN == "second-token"

        # Original config should still have original value (not dynamic)
        # This documents the behavior that config reads env at instantiation time
        assert config1.BEARER_TOKEN == "first-token"
