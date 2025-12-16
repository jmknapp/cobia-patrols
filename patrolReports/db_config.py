"""
Database configuration module.
Reads credentials from .env file to keep them out of source code.
"""
import os
from pathlib import Path

def load_env():
    """Load environment variables from .env file."""
    env_path = Path(__file__).parent / '.env'
    if env_path.exists():
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip()

# Load .env on import
load_env()

# Database configuration
DB_CONFIG = {
    'host': os.environ.get('DB_HOST', 'localhost'),
    'user': os.environ.get('DB_USER'),
    'password': os.environ.get('DB_PASSWORD'),
    'database': os.environ.get('DB_NAME', 'cobia')
}

def get_db_connection():
    """Get a MySQL database connection."""
    import mysql.connector
    return mysql.connector.connect(**DB_CONFIG)

