"""
Database configuration and connection management
"""
from contextlib import contextmanager
from typing import Generator, Optional
import psycopg2
import psycopg2.pool
from psycopg2.extras import RealDictCursor
from src.configs.settings import db_settings
from src.configs.logging import get_logger

logger = get_logger("database")

# Database connection pool
_connection_pool: Optional[psycopg2.pool.ThreadedConnectionPool] = None
_sqlmodel_engine = None


class DatabaseConfig:
    """Database configuration and connection management"""
    
    def __init__(self):
        self.settings = db_settings
        self.database_url = self.settings.database_url
        self.pool_size = 5
        self.max_overflow = 10
        
    def get_connection_params(self) -> dict:
        """Get database connection parameters"""
        return {
            "host": self.settings.DB_HOST,
            "port": self.settings.DB_PORT,
            "database": self.settings.DB_NAME,
            "user": self.settings.DB_USER,
            "password": self.settings.DB_PASSWORD,
            "cursor_factory": RealDictCursor,
            "application_name": f"{self.settings.APP_NAME}_{self.settings.ENVIRONMENT}"
        }
    
    def create_connection_pool(self) -> psycopg2.pool.ThreadedConnectionPool:
        """Create a connection pool for psycopg2"""
        try:
            pool = psycopg2.pool.ThreadedConnectionPool(
                minconn=1,
                maxconn=self.pool_size,
                **self.get_connection_params()
            )
            logger.info(f"Database connection pool created with {self.pool_size} connections")
            return pool
        except Exception as e:
            logger.error(f"Failed to create database connection pool: {str(e)}")
            raise
    
    def test_connection(self) -> bool:
        """Test database connection"""
        try:
            with psycopg2.connect(**self.get_connection_params()) as conn:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT 1")
                    result = cursor.fetchone()
                    if result:
                        logger.info("Database connection test successful")
                        return True
        except Exception as e:
            logger.error(f"Database connection test failed: {str(e)}")
            return False
        return False


# Global database configuration
db_config = DatabaseConfig()


def initialize_database():
    """Initialize database connections and pool"""
    global _connection_pool
    
    try:
        # Test connection first
        if not db_config.test_connection():
            raise Exception("Database connection test failed")
        
        # Create connection pool
        _connection_pool = db_config.create_connection_pool()
        
        logger.info("Database initialization completed successfully")
        
    except Exception as e:
        logger.error(f"Database initialization failed: {str(e)}")
        raise


def get_connection_pool() -> psycopg2.pool.ThreadedConnectionPool:
    """Get the database connection pool"""
    global _connection_pool
    if _connection_pool is None:
        raise Exception("Database not initialized. Call initialize_database() first.")
    return _connection_pool


def get_sqlmodel_engine():
    """Get the SQLModel engine"""
    global _sqlmodel_engine
    if _sqlmodel_engine is None:
        raise Exception("Database not initialized. Call initialize_database() first.")
    return _sqlmodel_engine


@contextmanager
def get_db_connection():
    """Get a database connection from the pool (context manager)"""
    pool = get_connection_pool()
    conn = None
    try:
        conn = pool.getconn()
        logger.debug("Database connection acquired from pool")
        yield conn
    except Exception as e:
        logger.error(f"Database connection error: {str(e)}")
        if conn:
            conn.rollback()
        raise
    finally:
        if conn:
            pool.putconn(conn)
            logger.debug("Database connection returned to pool")


@contextmanager
def get_db_cursor():
    """Get a database cursor (context manager)"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        try:
            yield cursor
            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error(f"Database cursor error: {str(e)}")
            raise
        finally:
            cursor.close()


class DatabaseManager:
    """Database manager for common operations"""
    
    @staticmethod
    def execute_query(query: str, params: tuple = None) -> list:
        """Execute a SELECT query and return results"""
        with get_db_cursor() as cursor:
            cursor.execute(query, params)
            return cursor.fetchall()
    
    @staticmethod
    def execute_update(query: str, params: tuple = None) -> int:
        """Execute an INSERT/UPDATE/DELETE query and return affected rows"""
        with get_db_cursor() as cursor:
            cursor.execute(query, params)
            return cursor.rowcount
    
    @staticmethod
    def execute_scalar(query: str, params: tuple = None):
        """Execute a query and return a single value"""
        with get_db_cursor() as cursor:
            cursor.execute(query, params)
            result = cursor.fetchone()
            if result:
                # Handle RealDictRow (dictionary-like) result
                if hasattr(result, 'get'):
                    # For RealDictRow, get the first value
                    return list(result.values())[0] if result else None
                else:
                    # Handle tuple result
                    return result[0] if len(result) > 0 else None
            return None
    
    @staticmethod
    def health_check() -> dict:
        """Perform database health check"""
        try:
            with get_db_cursor() as cursor:
                cursor.execute("SELECT version(), current_database(), current_user")
                result = cursor.fetchone()
                
                if result:
                    # Handle RealDictRow (dictionary-like) result
                    if hasattr(result, 'get'):
                        return {
                            "status": "healthy",
                            "database": result.get('current_database', 'unknown'),
                            "user": result.get('current_user', 'unknown'),
                            "version": result.get('version', 'unknown')
                        }
                    else:
                        # Handle tuple result
                        return {
                            "status": "healthy",
                            "database": result[1] if len(result) > 1 else "unknown",
                            "user": result[2] if len(result) > 2 else "unknown",
                            "version": result[0] if len(result) > 0 else "unknown"
                        }
                else:
                    return {
                        "status": "unhealthy",
                        "error": "No result from database query"
                    }
        except Exception as e:
            logger.error(f"Database health check failed: {str(e)}")
            return {
                "status": "unhealthy",
                "error": str(e)
            }


# Database initialization on module import
try:
    initialize_database()
except Exception as e:
    logger.error(f"Failed to initialize database on startup: {str(e)}")
    # Don't raise here to allow the app to start even if DB is unavailable
