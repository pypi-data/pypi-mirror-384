import os
from pathlib import Path
from loguru import logger
from sqlmodel import SQLModel, create_engine, Session

# from vrouter_agent.utils.config import settings


# Use configurable path for database to support different environments
def get_db_dir():
    """Get database directory based on environment variables or defaults."""
    # Check if we're in a test environment
    if os.environ.get("PYTEST_CURRENT_TEST") or os.environ.get("VROUTER_AGENT_ENV") == "test":
        # Use current directory for tests
        db_dir = Path(os.environ.get("VROUTER_AGENT_DB_DIR", "./test-data"))
    else:
        # Use system directory for production
        db_dir = Path(os.environ.get("VROUTER_AGENT_DB_DIR", "/var/db/vrouter-agent/data"))
    
    db_dir.mkdir(parents=True, exist_ok=True)  # Create data directory if it doesn't exist
    return db_dir

# Initialize database configuration lazily
_db_dir = None
_db_file = None
_database_url = None
_engine = None

def get_database_url():
    """Get database URL, initializing if necessary."""
    global _database_url, _db_dir, _db_file
    if _database_url is None:
        _db_dir = get_db_dir()
        _db_file = _db_dir / "data.db"
        _database_url = f"sqlite:///{_db_file}"
    return _database_url

def get_engine():
    """Get database engine, creating if necessary."""
    global _engine
    if _engine is None:
        database_url = get_database_url()
        _engine = create_engine(
            database_url,
            pool_size=10,  # Increase the pool size
            max_overflow=20,  # Increase the overflow size
            pool_timeout=60,  # Increase the connection timeout
            echo=False,  # Set to True for SQL debugging
        )
    return _engine

# Backward compatibility - direct function assignments instead of properties
DB_DIR = get_db_dir

def DB_FILE():
    global _db_file
    if _db_file is None:
        get_database_url()  # This will initialize _db_file
    return _db_file

DATABASE_URL = get_database_url

# Create engine attribute that evaluates to the actual engine object
# This resolves the issue where @property was creating a property object
# Now engine will be the actual SQLAlchemy engine instance
engine = get_engine()

# SQLite database connection
def init_db():
    """
    Initialize database tables.
    This function is safe to call multiple times - it only creates tables
    that don't already exist and preserves all existing data.
    """
    try:
        # Ensure database directory exists
        db_dir = get_db_dir()
        db_dir.mkdir(parents=True, exist_ok=True)
        
        # Get engine and create tables
        engine_instance = get_engine()
        
        # Create tables only if they don't exist (preserves existing data)
        SQLModel.metadata.create_all(engine_instance)
        
        db_file = get_database_url().replace("sqlite:///", "")
        logger.info(f"Database initialized at: {db_file}")
        logger.debug(f"Database URL: {get_database_url()}")
        
        # Log database size if it exists
        db_file_path = Path(db_file)
        if db_file_path.exists():
            size_mb = db_file_path.stat().st_size / (1024 * 1024)
            logger.debug(f"Database size: {size_mb:.2f} MB")
            
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise


def get_session():
    """
    Get database session with proper error handling.
    """
    try:
        with Session(get_engine()) as session:
            yield session
    except Exception as e:
        logger.error(f"Database session error: {e}")
        raise


def get_database_info():
    """
    Get information about the current database.
    """
    try:
        db_file_path = Path(get_database_url().replace("sqlite:///", ""))
        db_dir_path = get_db_dir()
        
        info = {
            "database_url": get_database_url(),
            "database_file": str(db_file_path),
            "database_exists": db_file_path.exists(),
            "database_size_mb": 0.0,
            "database_writable": False,
        }
        
        if db_file_path.exists():
            info["database_size_mb"] = db_file_path.stat().st_size / (1024 * 1024)
            info["database_writable"] = os.access(db_file_path, os.W_OK)
        else:
            # Check if directory is writable
            info["database_writable"] = os.access(db_dir_path, os.W_OK)
        
        return info
    except Exception as e:
        logger.error(f"Error getting database info: {e}")
        return {"error": str(e)}


def backup_database(backup_suffix=None):
    """
    Create a backup of the current database.
    
    Args:
        backup_suffix: Optional suffix for backup filename
    
    Returns:
        Path to backup file if successful, None otherwise
    """
    db_file_path = Path(get_database_url().replace("sqlite:///", ""))
    db_dir_path = get_db_dir()
    
    if not db_file_path.exists():
        logger.warning("No database file to backup")
        return None
    
    try:
        if backup_suffix is None:
            from datetime import datetime
            backup_suffix = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        backup_file = db_dir_path / f"vrouter-agent.db.backup_{backup_suffix}"
        
        import shutil
        shutil.copy2(db_file_path, backup_file)
        
        logger.info(f"Database backed up to: {backup_file}")
        return backup_file
        
    except Exception as e:
        logger.error(f"Failed to backup database: {e}")
        return None
