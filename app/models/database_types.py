"""Database type definitions and enumerations.

This module provides type-safe database mode definitions following the
Single Responsibility Principle (SRP) by focusing solely on database
type definitions and validation.
"""
from enum import Enum


class DatabaseMode(str, Enum):
    """
    Database connection mode enumeration.

    Inherits from str to maintain backward compatibility with string-based
    operations while providing type safety and validation.

    Values:
        LOCAL: Local-only DuckDB database mode
        CLOUD: Cloud-only MotherDuck database mode
        HYBRID: Hybrid mode with local database and cloud sync capabilities
    """

    LOCAL = "local"
    CLOUD = "cloud"
    HYBRID = "hybrid"

    @classmethod
    def from_string(cls, value: str | None) -> "DatabaseMode":
        """
        Convert string value to DatabaseMode enum.

        Args:
            value: String representation of database mode

        Returns:
            DatabaseMode: Corresponding enum member

        Raises:
            ValueError: If value is not a valid database mode
            TypeError: If value is None
        """
        if value is None:
            raise TypeError("Database mode cannot be None")

        if not isinstance(value, str):
            raise TypeError(
                f"Database mode must be a string, got {type(value).__name__}"
            )

        # Case-insensitive comparison
        normalized_value = value.lower().strip()

        if not normalized_value:
            raise ValueError("Invalid database mode ''")

        for mode in cls:
            if mode.value == normalized_value:
                return mode

        raise ValueError(
            f"Invalid database mode '{value}'. Must be one of: {cls.all_modes()}"
        )

    @classmethod
    def is_valid(cls, value: str | None) -> bool:
        """
        Check if a string value is a valid database mode.

        Args:
            value: String value to validate

        Returns:
            bool: True if value is valid, False otherwise
        """
        try:
            cls.from_string(value)
            return True
        except (ValueError, TypeError):
            return False

    @classmethod
    def all_modes(cls) -> list[str]:
        """
        Get list of all valid database mode strings.

        Returns:
            List[str]: List of all database mode string values
        """
        return [mode.value for mode in cls]

    def requires_token(self) -> bool:
        """
        Check if this database mode requires a MotherDuck token.

        Returns:
            bool: True if mode requires MotherDuck token, False otherwise
        """
        return self in (self.CLOUD, self.HYBRID)

    def __str__(self) -> str:
        """Return string representation for backward compatibility."""
        return self.value
