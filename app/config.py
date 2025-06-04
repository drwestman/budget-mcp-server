import os


class Config:
    """Base configuration class."""
    API_KEY = os.getenv('API_KEY', 'your_super_secret_api_key_12345')
    DATABASE_FILE = os.getenv('DATABASE_FILE', 'budget_app.duckdb')
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    
    @staticmethod
    def ensure_data_directory():
        """Ensure the data directory exists for database file."""
        db_file = os.getenv('DATABASE_FILE', 'budget_app.duckdb')
        if db_file != ':memory:':
            db_dir = os.path.dirname(db_file)
            if db_dir and not os.path.exists(db_dir):
                os.makedirs(db_dir, exist_ok=True)


class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True
    TESTING = False
    # Reset database on each run during development
    RESET_DB_ON_START = True


class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False
    TESTING = False
    RESET_DB_ON_START = False


class TestingConfig(Config):
    """Testing configuration."""
    DEBUG = True
    TESTING = True
    DATABASE_FILE = ':memory:'  # Use in-memory database for tests
    RESET_DB_ON_START = True


# Configuration mapping
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}