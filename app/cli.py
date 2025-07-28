#!/usr/bin/env python3
"""
CLI entry point for the Budget Cash Envelope MCP Server.
This module provides the command-line interface for uvx installation using standard
MCP SDK.
"""
import asyncio
import os
import sys

from mcp.server.stdio import stdio_server

from app import create_mcp_server
from app.config import Config, config


def main() -> int:
    """Main entry point for the CLI."""
    try:
        # Get configuration environment from environment variable
        # Default to production for uvx installation
        config_name = os.getenv("APP_ENV", "production")

        # Ensure data directory exists for database file
        Config.ensure_data_directory()

        # Get configuration for database cleanup
        app_config = config[config_name]()

        # Clean up database file on start for development
        if hasattr(app_config, "RESET_DB_ON_START") and app_config.RESET_DB_ON_START:
            db_file = app_config.DATABASE_FILE
            if db_file != ":memory:" and os.path.exists(db_file):
                os.remove(db_file)
                print(f"Removed existing database file: {db_file}", file=sys.stderr)

        # Print configuration info to stderr (not to interfere with MCP stdio)
        print(f"Environment: {config_name}", file=sys.stderr)
        print(f"Database File: {app_config.DATABASE_FILE}", file=sys.stderr)
        print(f"Debug Mode: {getattr(app_config, 'DEBUG', False)}", file=sys.stderr)
        print(
            "Starting Budget Envelope MCP Server with stdio transport...",
            file=sys.stderr,
        )

        async def run_stdio_server() -> None:
            # Create MCP server using standard MCP SDK
            server = create_mcp_server(config_name)

            # Run the MCP server with stdio transport
            async with stdio_server() as (read_stream, write_stream):
                await server.run(
                    read_stream,
                    write_stream,
                    server.create_initialization_options(),
                )

        asyncio.run(run_stdio_server())
        return 0

    except KeyboardInterrupt:
        print("\nShutting down Budget MCP Server...", file=sys.stderr)
        return 0
    except Exception as e:
        print(f"Error starting Budget MCP Server: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
