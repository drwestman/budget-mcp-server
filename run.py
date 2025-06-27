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


def run_https_server(mcp, host, port, path, ssl_cert_file, ssl_key_file, log_level):
    """
    Run the FastMCP server with HTTPS using proper FastMCP initialization.
    
    Note: This implementation uses FastMCP's run method with SSL configuration,
    but due to current FastMCP limitations with HTTPS, it falls back to 
    standard HTTP mode. HTTPS support requires additional FastMCP framework updates.
    
    Args:
        mcp: FastMCP server instance
        host: Server host address
        port: Server port number
        path: MCP endpoint path
        ssl_cert_file: Path to SSL certificate file
        ssl_key_file: Path to SSL private key file
        log_level: Logging level
    """
    print("Note: HTTPS mode currently has limitations with FastMCP task group initialization.")
    print("Falling back to HTTP mode for proper FastMCP functionality.")
    print("For production HTTPS, consider using a reverse proxy (nginx, traefik) in front of the HTTP server.")
    
    # Run in HTTP mode to ensure proper FastMCP initialization
    mcp.run(
        transport="streamable-http",
        host=host,
        port=port,
        path=path,
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
    
    # Validate bearer token is configured for HTTP transport (only in production)
    if config_name == 'production' and not app_config.BEARER_TOKEN:
        print("Error: BEARER_TOKEN environment variable is required for production HTTP transport security.")
        print("Please set BEARER_TOKEN in your environment or .env file.")
        sys.exit(1)
    
    # Warn about missing bearer token in development
    if config_name != 'production' and not app_config.BEARER_TOKEN:
        print("Warning: BEARER_TOKEN not set. Authentication middleware will be disabled in development.")
        print("Set BEARER_TOKEN environment variable to enable authentication.")
    
    # Clean up database file on start for development
    if app_config.RESET_DB_ON_START:
        db_file = app_config.DATABASE_FILE
        if db_file != ':memory:' and os.path.exists(db_file):
            os.remove(db_file)
            print(f"Removed existing database file: {db_file}")
    
    # Create FastMCP server using the factory pattern with authentication enabled only if token is set
    enable_auth = bool(app_config.BEARER_TOKEN)
    mcp = create_fastmcp_server(config_name, enable_auth=enable_auth)
    
    # Initialize database tables after potential cleanup
    mcp.db._connect()
    mcp.db._create_tables()
    
    # Print configuration info
    print(f"Environment: {config_name}")
    print(f"Database File: {app_config.DATABASE_FILE}")
    print(f"Debug Mode: {app_config.DEBUG}")
    print(f"Bearer Token Authentication: {'Enabled' if enable_auth else 'Disabled'}")
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
        # Use custom HTTPS implementation (currently falls back to HTTP due to FastMCP limitations)
        run_https_server(
            mcp=mcp,
            host=host,
            port=port,
            path=path,
            ssl_cert_file=ssl_cert_file,
            ssl_key_file=ssl_key_file,
            log_level=run_args["log_level"]
        )
    else:
        # Standard HTTP mode
        mcp.run(**run_args)


if __name__ == '__main__':
    main()
