import pytest

from app.models.database_types import DatabaseMode


class TestDatabaseMode:
    """Test cases for DatabaseMode enum."""

    def test_enum_values(self) -> None:
        """Test that enum has correct string values."""
        assert DatabaseMode.LOCAL.value == "local"
        assert DatabaseMode.CLOUD.value == "cloud"
        assert DatabaseMode.HYBRID.value == "hybrid"

    def test_enum_string_behavior(self) -> None:
        """Test that enum behaves like strings for backward compatibility."""
        assert str(DatabaseMode.LOCAL) == "local"
        assert DatabaseMode.LOCAL == "local"
        assert DatabaseMode.CLOUD == "cloud"
        assert DatabaseMode.HYBRID == "hybrid"

    def test_from_string_valid_values(self) -> None:
        """Test from_string method with valid values."""
        assert DatabaseMode.from_string("local") == DatabaseMode.LOCAL
        assert DatabaseMode.from_string("cloud") == DatabaseMode.CLOUD
        assert DatabaseMode.from_string("hybrid") == DatabaseMode.HYBRID

    def test_from_string_case_insensitive(self) -> None:
        """Test from_string method is case insensitive."""
        assert DatabaseMode.from_string("LOCAL") == DatabaseMode.LOCAL
        assert DatabaseMode.from_string("Cloud") == DatabaseMode.CLOUD
        assert DatabaseMode.from_string("HYBRID") == DatabaseMode.HYBRID

    def test_from_string_invalid_value(self) -> None:
        """Test from_string method with invalid value raises ValueError."""
        with pytest.raises(ValueError, match="Invalid database mode 'invalid'"):
            DatabaseMode.from_string("invalid")

        with pytest.raises(ValueError, match="Invalid database mode ''"):
            DatabaseMode.from_string("")

    def test_from_string_none_value(self) -> None:
        """Test from_string method with None raises TypeError."""
        with pytest.raises(TypeError):
            DatabaseMode.from_string(None)  # type: ignore

    def test_is_valid_method(self) -> None:
        """Test is_valid class method."""
        assert DatabaseMode.is_valid("local") is True
        assert DatabaseMode.is_valid("cloud") is True
        assert DatabaseMode.is_valid("hybrid") is True
        assert DatabaseMode.is_valid("LOCAL") is True
        assert DatabaseMode.is_valid("Cloud") is True
        assert DatabaseMode.is_valid("invalid") is False
        assert DatabaseMode.is_valid("") is False
        assert DatabaseMode.is_valid(None) is False  # type: ignore

    def test_all_modes_property(self) -> None:
        """Test all_modes class property returns all valid mode strings."""
        expected = ["local", "cloud", "hybrid"]
        assert DatabaseMode.all_modes() == expected

    def test_requires_token_method(self) -> None:
        """Test requires_token method for determining token requirements."""
        assert DatabaseMode.LOCAL.requires_token() is False
        assert DatabaseMode.CLOUD.requires_token() is True
        assert DatabaseMode.HYBRID.requires_token() is True

    def test_enum_membership(self) -> None:
        """Test membership operations."""
        valid_modes = [DatabaseMode.LOCAL, DatabaseMode.CLOUD, DatabaseMode.HYBRID]

        assert DatabaseMode.LOCAL in valid_modes
        assert DatabaseMode.CLOUD in valid_modes
        assert DatabaseMode.HYBRID in valid_modes

    def test_enum_iteration(self) -> None:
        """Test that enum can be iterated over."""
        modes = list(DatabaseMode)
        assert len(modes) == 3
        assert DatabaseMode.LOCAL in modes
        assert DatabaseMode.CLOUD in modes
        assert DatabaseMode.HYBRID in modes

    def test_enum_comparison(self) -> None:
        """Test enum comparison operations."""
        assert DatabaseMode.LOCAL == DatabaseMode.LOCAL
        assert DatabaseMode.LOCAL != DatabaseMode.CLOUD
        assert DatabaseMode.CLOUD != DatabaseMode.HYBRID
