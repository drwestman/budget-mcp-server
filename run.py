#!/usr/bin/env python3
"""
Entry point for the Budget Cash Envelope REST API application.
Run this file to start the Flask development server.
"""
import os
from app import create_app


def main():
    """Main function to run the Flask application."""
    # Get configuration environment from environment variable
    config_name = os.getenv('FLASK_ENV', 'development')
    
    # Ensure data directory exists for database file
    from app.config import Config
    Config.ensure_data_directory()
    
    # Create Flask app using the factory pattern
    app = create_app(config_name)
    
    # Clean up database file on start for development
    if app.config.get('RESET_DB_ON_START', False):
        db_file = app.config['DATABASE_FILE']
        if db_file != ':memory:' and os.path.exists(db_file):
            os.remove(db_file)
            print(f"Removed existing database file: {db_file}")
            # Recreate database with fresh tables
            app.db._connect()
            app.db._create_tables()
    
    # Print configuration info
    print(f"Environment: {config_name}")
    print(f"API Key: {app.config['API_KEY']}")
    print(f"Database File: {app.config['DATABASE_FILE']}")
    print(f"Debug Mode: {app.config['DEBUG']}")
    
    # Run the application
    app.run(
        debug=app.config['DEBUG'],
        port=int(os.getenv('PORT', 5000)),
        host=os.getenv('HOST', '127.0.0.1')
    )


if __name__ == '__main__':
    main()