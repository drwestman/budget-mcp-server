#!/usr/bin/env python3
"""
Stdio entry point for the Budget Cash Envelope MCP Server application.
Run this file to start the MCP server with stdio transport.
"""
import asyncio
import os

from mcp.server.stdio import stdio_server

from app import create_mcp_server


async def main() -> None:
    """Main function to run the MCP server with stdio transport."""
    # Get configuration environment from environment variable
    config_name = os.getenv("APP_ENV", "development")

    # Ensure data directory exists for database file
    from app.config import Config

    Config.ensure_data_directory()

    # Create MCP server using the factory pattern
    server = create_mcp_server(config_name)

    # Get configuration for database cleanup
    from app.config import config

    app_config = config[config_name]()

    # Clean up database file on start for development
    if app_config.RESET_DB_ON_START:
        db_file = app_config.DATABASE_FILE
        if db_file != ":memory:" and os.path.exists(db_file):
            os.remove(db_file)
            print(f"Removed existing database file: {db_file}")
            # Recreate database with fresh tables
            server.db._connect()
            server.db._create_tables()

    # Print configuration info
    print(f"Environment: {config_name}")
    print(f"Database File: {app_config.DATABASE_FILE}")
    print(f"Debug Mode: {app_config.DEBUG}")
    print("Starting Budget Envelope MCP Server with stdio transport...")

    # Run the MCP server
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream, write_stream, server.create_initialization_options()
        )


if __name__ == "__main__":
    asyncio.run(main())
