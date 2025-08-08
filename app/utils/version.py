#!/usr/bin/env python3
"""
Version utilities for Budget Cash Envelope MCP Server.
Provides runtime access to package version information.
"""

import importlib.metadata
from typing import Any


def get_version() -> str:
    """
    Get the current version of the budget-mcp-server package.

    Returns:
        str: Version string from pyproject.toml

    Raises:
        ImportError: If package metadata cannot be found
    """
    try:
        return importlib.metadata.version("budget-mcp-server")
    except importlib.metadata.PackageNotFoundError:
        # Fallback for development/testing when package not installed
        return "0.2.0-dev"


def get_version_info() -> dict[str, Any]:
    """
    Get comprehensive version information.

    Returns:
        Dict with version, name, and metadata
    """
    try:
        version = importlib.metadata.version("budget-mcp-server")
        metadata = importlib.metadata.metadata("budget-mcp-server")

        return {
            "version": version,
            "name": metadata["Name"] if "Name" in metadata else "budget-mcp-server",
            "description": metadata["Summary"] if "Summary" in metadata else "",
            "python_requires": metadata["Requires-Python"]
            if "Requires-Python" in metadata
            else "",
        }
    except importlib.metadata.PackageNotFoundError:
        # Fallback for development/testing
        return {
            "version": "0.2.0-dev",
            "name": "budget-mcp-server",
            "description": "Budget Cash Envelope MCP Server - Development Build",
            "python_requires": ">=3.12",
        }


def format_version_string() -> str:
    """
    Get a formatted version string for display.

    Returns:
        str: Formatted version string
    """
    info = get_version_info()
    return f"{info['name']} v{info['version']}"
