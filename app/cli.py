#!/usr/bin/env python3
"""
CLI entry point for the Budget Cash Envelope MCP Server.
This module provides the command-line interface for uvx installation using FastMCP.
"""
import os
import sys

from app.fastmcp_server import create_fastmcp_server


def main() -> int:
    """Main entry point for the CLI."""
    try:
        # Get configuration environment from environment variable
        # Default to production for uvx installation
        config_name = os.getenv("APP_ENV", "production")

        # Ensure data directory exists for database file
        from app.config import Config

        Config.ensure_data_directory()

        # Get configuration for database cleanup
        from app.config import config

        app_config = config[config_name]()

        # Clean up database file on start for development
        if hasattr(app_config, "RESET_DB_ON_START") and app_config.RESET_DB_ON_START:
            db_file = app_config.DATABASE_FILE
            if db_file != ":memory:" and os.path.exists(db_file):
                os.remove(db_file)
                print(f"Removed existing database file: {db_file}", file=sys.stderr)

        # Create FastMCP server using the factory pattern
        # No authentication needed for stdio transport
        mcp = create_fastmcp_server(config_name, enable_auth=False)

        # Database is already initialized by create_fastmcp_server

        # Print configuration info to stderr (not to interfere with MCP stdio)
        print(f"Environment: {config_name}", file=sys.stderr)
        print(f"Database File: {app_config.DATABASE_FILE}", file=sys.stderr)
        print(f"Debug Mode: {getattr(app_config, 'DEBUG', False)}", file=sys.stderr)
        print(
            "Starting Budget Envelope FastMCP Server with stdio transport...",
            file=sys.stderr,
        )

        # Run MCP server with stdio transport using hybrid approach
        # Create a native MCP server and copy tools from FastMCP for compatibility
        import asyncio

        from mcp.server import Server
        from mcp.server.stdio import stdio_server
        from mcp.types import TextContent, Tool

        async def run_hybrid_mcp_stdio() -> None:
            # Create a native MCP server
            mcp_server: Server = Server("budget-envelope-server")

            # Get tools from FastMCP and register them with native MCP server
            fastmcp_tools = await mcp.get_tools()

            # Register tools with native MCP server
            @mcp_server.list_tools()
            async def list_tools() -> list[Tool]:
                tools = []
                for name, fastmcp_tool in fastmcp_tools.items():
                    # Convert FastMCP tool to MCP Tool
                    tool = Tool(
                        name=name,
                        description=getattr(fastmcp_tool, "description", ""),
                        inputSchema=getattr(fastmcp_tool, "input_schema", {}),
                    )
                    tools.append(tool)
                return tools

            @mcp_server.call_tool()
            async def call_tool(name: str, arguments: dict) -> list[TextContent]:
                # Call the FastMCP tool and return result
                if name in fastmcp_tools:
                    tool_func = getattr(fastmcp_tools[name], "func", None)
                    if tool_func:
                        result = await tool_func(**arguments)
                    else:
                        result = f"Tool {name} has no callable function"
                    return [TextContent(type="text", text=result)]
                else:
                    return [TextContent(type="text", text=f"Tool {name} not found")]

            # Run the native MCP server with stdio transport
            async with stdio_server() as (read_stream, write_stream):
                await mcp_server.run(
                    read_stream,
                    write_stream,
                    mcp_server.create_initialization_options(),
                )

        asyncio.run(run_hybrid_mcp_stdio())
        return 0

    except KeyboardInterrupt:
        print("\nShutting down Budget MCP Server...", file=sys.stderr)
        return 0
    except Exception as e:
        print(f"Error starting Budget MCP Server: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
