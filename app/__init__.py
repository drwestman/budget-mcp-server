# This file can be used for package imports if needed in the future
# The legacy MCP server implementation has been removed
# All MCP functionality is now handled by FastMCP in app/fastmcp_server.py

# Import the standard MCP server factory for stdio transport
from app.mcp_server import create_mcp_server
from app.utils.version import get_version

# Package version - dynamically read from pyproject.toml
__version__ = get_version()

__all__ = ["create_mcp_server", "__version__"]
