#!/usr/bin/env python3
"""
CLI entry point for the Budget Cash Envelope MCP Server.
This module provides the command-line interface for uvx installation.
"""
import os
import sys
import asyncio
from mcp.server.stdio import stdio_server
from app import create_mcp_server


async def run_stdio():
    """Run the MCP server with stdio transport."""
    # Get configuration environment from environment variable
    # Default to production for uvx installation
    config_name = os.getenv("APP_ENV", "production")

    # Ensure data directory exists for database file
    from app.config import Config

    Config.ensure_data_directory()

    # Create MCP server using the factory pattern
    server = create_mcp_server(config_name)

    # Get configuration for database cleanup
    from app.config import config

    app_config = config[config_name]()

    # Print configuration info to stderr (not to interfere with MCP stdio)
    print(f"Environment: {config_name}", file=sys.stderr)
    print(f"Database File: {app_config.DATABASE_FILE}", file=sys.stderr)
    print(f"Debug Mode: {app_config.DEBUG}", file=sys.stderr)
    print(
        "Starting Budget Envelope MCP Server with stdio transport...", file=sys.stderr
    )

    # Run the MCP server
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream, write_stream, server.create_initialization_options()
        )


def main():
    """Main entry point for the CLI."""
    try:
        asyncio.run(run_stdio())
        return 0
    except KeyboardInterrupt:
        print("\nShutting down Budget MCP Server...", file=sys.stderr)
        return 0
    except Exception as e:
        print(f"Error starting Budget MCP Server: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    main()
