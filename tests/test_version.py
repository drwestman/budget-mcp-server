#!/usr/bin/env python3
"""
Unit tests for version functionality in Budget Cash Envelope MCP Server.
"""

from unittest.mock import patch

import pytest

from app import __version__
from app.utils.version import format_version_string, get_version, get_version_info


class TestVersionUtilities:
    """Test version utility functions."""

    def test_get_version_returns_string(self):
        """Test that get_version returns a version string."""
        version = get_version()
        assert isinstance(version, str)
        assert len(version) > 0

    def test_get_version_format(self):
        """Test that version follows semantic versioning format."""
        version = get_version()
        # Should be in format X.Y.Z or X.Y.Z-suffix
        parts = version.split("-")[0].split(".")
        assert len(parts) >= 3 or version.endswith("-dev")

    def test_get_version_info_structure(self):
        """Test that get_version_info returns expected structure."""
        info = get_version_info()

        assert isinstance(info, dict)
        assert "version" in info
        assert "name" in info
        assert "description" in info
        assert "python_requires" in info

        assert info["name"] == "budget-mcp-server"
        assert isinstance(info["version"], str)

    def test_format_version_string(self):
        """Test formatted version string output."""
        formatted = format_version_string()

        assert isinstance(formatted, str)
        assert "budget-mcp-server" in formatted
        assert " v" in formatted

    @patch("importlib.metadata.version")
    @patch("importlib.metadata.metadata")
    def test_get_version_fallback(self, mock_metadata, mock_version):
        """Test fallback behavior when package metadata unavailable."""
        from importlib.metadata import PackageNotFoundError

        mock_version.side_effect = PackageNotFoundError()
        mock_metadata.side_effect = PackageNotFoundError()

        version = get_version()
        assert version == "0.2.0-dev"

        info = get_version_info()
        assert info["version"] == "0.2.0-dev"
        assert info["name"] == "budget-mcp-server"


class TestPackageVersion:
    """Test package-level version access."""

    def test_package_version_available(self):
        """Test that __version__ is available at package level."""
        assert hasattr(__version__, "__str__")
        assert isinstance(__version__, str)
        assert len(__version__) > 0

    def test_package_version_consistency(self):
        """Test that package version matches utility function."""
        package_version = __version__
        utility_version = get_version()

        # Should be the same or utility should be dev version
        assert package_version == utility_version or utility_version.endswith("-dev")


class TestVersionToolIntegration:
    """Test version tool MCP integration."""

    @pytest.mark.asyncio
    async def test_version_tool_handler(self):
        """Test version tool handler functionality."""
        from unittest.mock import MagicMock

        from app.tools.handlers import handle_get_server_version

        mock_service = MagicMock()
        result = await handle_get_server_version(mock_service, {})

        assert isinstance(result, dict)
        assert "version" in result
        assert "name" in result

    def test_version_tool_schema_exists(self):
        """Test that version tool schema is properly defined."""
        from app.tools.schemas import get_all_tool_schemas

        schemas = get_all_tool_schemas()
        assert "get_server_version" in schemas

        version_schema = schemas["get_server_version"]
        assert version_schema["name"] == "get_server_version"
        assert "version" in version_schema["description"]
        assert version_schema["inputSchema"]["type"] == "object"
        assert len(version_schema["inputSchema"]["required"]) == 0

    @pytest.mark.asyncio
    async def test_fastmcp_version_tool_available(self):
        """Test that FastMCP server includes version tool."""
        from app.fastmcp_server import create_fastmcp_server

        server = create_fastmcp_server("testing")
        tools = await server.get_tools()

        # FastMCP returns tool objects, not strings
        tool_names = [
            tool.name if hasattr(tool, "name") else str(tool) for tool in tools
        ]
        assert "get_server_version" in tool_names
