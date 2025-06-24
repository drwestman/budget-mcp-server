#!/usr/bin/env python3
"""
Entry point for the Budget Cash Envelope MCP Server application.
Run this file to start the FastMCP server with Streamable HTTP transport.
"""
import os
from app.fastmcp_server import create_fastmcp_server


def main():
    """Main function to run the FastMCP server."""
    # Get configuration environment from environment variable
    config_name = os.getenv('APP_ENV', 'development')
    
    # Ensure data directory exists for database file
    from app.config import Config
    Config.ensure_data_directory()
    
    # Get configuration for database cleanup
    from app.config import config
    app_config = config[config_name]()
    
    # Clean up database file on start for development
    if app_config.RESET_DB_ON_START:
        db_file = app_config.DATABASE_FILE
        if db_file != ':memory:' and os.path.exists(db_file):
            os.remove(db_file)
            print(f"Removed existing database file: {db_file}")
    
    # Create FastMCP server using the factory pattern
    mcp = create_fastmcp_server(config_name)
    
    # Initialize database tables after potential cleanup
    mcp.db._connect()
    mcp.db._create_tables()
    
    # Print configuration info
    print(f"Environment: {config_name}")
    print(f"Database File: {app_config.DATABASE_FILE}")
    print(f"Debug Mode: {app_config.DEBUG}")
    print("Starting Budget Envelope FastMCP Server with Streamable HTTP transport...")
    
    # Get host and port from environment or use defaults
    host = os.getenv('HOST', '127.0.0.1')
    port = int(os.getenv('PORT', 8000))
    path = os.getenv('MCP_PATH', '/mcp')
    
    print(f"Server will be accessible at http://{host}:{port}{path}")
    
    # Run the FastMCP server with streamable HTTP transport
    mcp.run(
        transport="streamable-http",
        host=host,
        port=port,
        path=path,
        log_level="info" if app_config.DEBUG else "warning"
    )


if __name__ == '__main__':
    main()
