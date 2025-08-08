import os
import re

from .models.database_types import DatabaseMode


class Config:
    """Base configuration class."""

    def __init__(self) -> None:
        """Initialize configuration instance with environment variables."""
        self.DATABASE_FILE = os.getenv(
            "DATABASE_FILE", self._get_default_database_path()
        )
        self.HTTPS_ENABLED = os.getenv("HTTPS_ENABLED", "false").lower() == "true"
        self.SSL_CERT_FILE = os.getenv("SSL_CERT_FILE", "certs/server.crt")
        self.SSL_KEY_FILE = os.getenv("SSL_KEY_FILE", "certs/server.key")
        self.BEARER_TOKEN = os.getenv("BEARER_TOKEN")
        self.MOTHERDUCK_TOKEN = os.getenv("MOTHERDUCK_TOKEN")
        self.MOTHERDUCK_DATABASE = os.getenv("MOTHERDUCK_DATABASE", "budget_app")
        # Get DATABASE_MODE from environment and convert to enum
        mode_str = os.getenv("DATABASE_MODE", "hybrid")
        self.DATABASE_MODE = DatabaseMode.from_string(mode_str)
        self.MOTHERDUCK_SYNC_ON_START = (
            os.getenv("MOTHERDUCK_SYNC_ON_START", "false").lower() == "true"
        )
        # Override to use local mode if no MOTHERDUCK_TOKEN is provided
        if not self.MOTHERDUCK_TOKEN:
            self.DATABASE_MODE = DatabaseMode.LOCAL

    @staticmethod
    def _get_default_database_path() -> str:
        """
        Get XDG-compliant default database path.

        Returns:
            str: Default database file path following XDG Base Directory spec
        """
        xdg_data_home = os.getenv("XDG_DATA_HOME")
        if not xdg_data_home:
            xdg_data_home = os.path.join(os.path.expanduser("~"), ".local", "share")

        return os.path.join(xdg_data_home, "budget-mcp-server", "budget_app.duckdb")

    @staticmethod
    def ensure_data_directory() -> None:
        """Ensure the data directory exists for database file."""
        db_file = os.getenv("DATABASE_FILE", Config._get_default_database_path())
        if db_file != ":memory:":
            db_dir = os.path.dirname(db_file)
            if db_dir and not os.path.exists(db_dir):
                os.makedirs(db_dir, exist_ok=True)

    @staticmethod
    def validate_motherduck_token(token: str | None) -> bool:
        """
        Validate MotherDuck token format.

        Args:
            token (str): MotherDuck access token (JWT or legacy hex format)

        Returns:
            bool: True if token appears valid, False otherwise
        """
        if not token:
            return False

        # Check for JWT format (starts with eyJ)
        if token.startswith("eyJ"):
            # Basic JWT validation - should have 3 parts separated by dots
            parts = token.split(".")
            if len(parts) != 3:
                return False
            # Ensure minimum length for each part
            return all(len(part) > 0 for part in parts)

        # Legacy format validation: 32+ character hex strings
        if len(token) < 32:
            return False

        # Check if token contains only valid characters
        # (hex, alphanumeric, some special chars)
        if not re.match(r"^[a-fA-F0-9._-]+$", token):
            return False

        return True

    @staticmethod
    def validate_database_mode(mode: str | DatabaseMode | None) -> bool:
        """
        Validate database mode setting.

        Args:
            mode: Database mode (DatabaseMode enum, string, or None)

        Returns:
            bool: True if mode is valid, False otherwise
        """
        if isinstance(mode, DatabaseMode):
            return True
        elif isinstance(mode, str):
            return DatabaseMode.is_valid(mode)
        else:
            return False

    def validate_motherduck_config(self) -> tuple[bool, str | None]:
        """
        Validate MotherDuck configuration settings.

        Returns:
            tuple: (is_valid, error_message)
        """
        mode = self.DATABASE_MODE
        token = self.MOTHERDUCK_TOKEN

        # Validate database mode (should already be validated in __init__)
        if not self.validate_database_mode(mode):
            return (
                False,
                (
                    f"Invalid DATABASE_MODE '{mode}'. "
                    f"Must be one of: {DatabaseMode.all_modes()}"
                ),
            )

        # If using cloud or hybrid mode, MotherDuck token is required
        if mode.requires_token():
            if not token:
                return False, f"MOTHERDUCK_TOKEN is required for DATABASE_MODE '{mode}'"

            if not self.validate_motherduck_token(token):
                return (
                    False,
                    (
                        "MOTHERDUCK_TOKEN appears to be invalid "
                        "(should be JWT token or 32+ character hex string)"
                    ),
                )

        return True, None


class DevelopmentConfig(Config):
    """Development configuration."""

    def __init__(self) -> None:
        super().__init__()
        self.DEBUG = True
        self.TESTING = False
        self.RESET_DB_ON_START = True


class ProductionConfig(Config):
    """Production configuration."""

    def __init__(self) -> None:
        super().__init__()
        self.DEBUG = False
        self.TESTING = False
        self.RESET_DB_ON_START = False


class ConfigTesting(Config):
    """Testing configuration."""

    def __init__(self) -> None:
        super().__init__()
        self.DEBUG = True
        self.TESTING = True
        self.DATABASE_FILE = ":memory:"
        self.RESET_DB_ON_START = True
        self.DATABASE_MODE = DatabaseMode.LOCAL


# Configuration mapping
config = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "testing": ConfigTesting,
    "default": DevelopmentConfig,
}
