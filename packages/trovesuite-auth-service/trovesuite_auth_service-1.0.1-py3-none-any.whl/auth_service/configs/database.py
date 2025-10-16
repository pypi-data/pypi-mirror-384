"""
Database configuration and connection management
"""

from contextlib import contextmanager
from typing import Optional
import psycopg2
import psycopg2.pool
from .logging import get_logger

logger = get_logger("database")

# Database connection pool
_connection_pool: Optional[psycopg2.pool.ThreadedConnectionPool] = None

def get_connection_pool() -> psycopg2.pool.ThreadedConnectionPool:
    """Get the database connection pool"""
    if _connection_pool is None:
        raise Exception("Database not initialized. Call initialize_database() first.")
    return _connection_pool


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