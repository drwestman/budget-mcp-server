#!/usr/bin/env python3
"""
Entry point for the Budget Cash Envelope MCP Server application.
Run this file to start the FastMCP server with Streamable HTTP transport.
"""
import os
import ssl
import sys
import uvicorn
from app.fastmcp_server import create_fastmcp_server


def run_https_server(mcp, host, port, ssl_cert_file, ssl_key_file, log_level):
    """
    Run the FastMCP server with HTTPS using custom Uvicorn configuration.
    
    Args:
        mcp: FastMCP server instance
        host: Server host address
        port: Server port number
        ssl_cert_file: Path to SSL certificate file
        ssl_key_file: Path to SSL private key file
        log_level: Logging level
    """
    # Get the ASGI app from FastMCP
    asgi_app = mcp.http_app()
    
    # Run with Uvicorn and SSL using certificate files
    uvicorn.run(
        asgi_app,
        host=host,
        port=port,
        ssl_certfile=ssl_cert_file,
        ssl_keyfile=ssl_key_file,
        log_level=log_level
    )


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
    
    # HTTPS configuration
    https_enabled = app_config.HTTPS_ENABLED
    ssl_cert_file = app_config.SSL_CERT_FILE
    ssl_key_file = app_config.SSL_KEY_FILE
    
    # Determine protocol and validate SSL files if HTTPS is enabled
    if https_enabled:
        if not os.path.exists(ssl_cert_file) or not os.path.exists(ssl_key_file):
            print(f"Error: SSL certificate files not found!")
            print(f"Expected cert file: {ssl_cert_file}")
            print(f"Expected key file: {ssl_key_file}")
            print(f"Run 'python scripts/generate_cert.py' to generate self-signed certificates")
            sys.exit(1)
        protocol = "https"
        print(f"HTTPS Mode: Enabled")
        print(f"SSL Certificate: {ssl_cert_file}")
        print(f"SSL Private Key: {ssl_key_file}")
    else:
        protocol = "http"
        print(f"HTTPS Mode: Disabled (set HTTPS_ENABLED=true to enable)")
    
    print(f"Server will be accessible at {protocol}://{host}:{port}{path}")
    
    # Prepare run arguments
    run_args = {
        "transport": "streamable-http",
        "host": host,
        "port": port,
        "path": path,
        "log_level": "info" if app_config.DEBUG else "warning"
    }
    
    # Note: SSL configuration handled separately for HTTPS mode
    
    # Run the FastMCP server with streamable HTTP transport
    if https_enabled:
        # Use custom HTTPS implementation
        run_https_server(
            mcp=mcp,
            host=host,
            port=port,
            ssl_cert_file=ssl_cert_file,
            ssl_key_file=ssl_key_file,
            log_level=run_args["log_level"]
        )
    else:
        # Standard HTTP mode
        mcp.run(**run_args)


if __name__ == '__main__':
    main()
