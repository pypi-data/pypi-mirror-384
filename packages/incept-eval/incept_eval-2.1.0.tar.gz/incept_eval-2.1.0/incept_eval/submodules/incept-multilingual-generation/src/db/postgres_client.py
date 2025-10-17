import psycopg2
from psycopg2 import pool
from psycopg2.extras import RealDictCursor
import os
from typing import Optional, List, Dict, Any
import logging
from datetime import datetime, date
import json
from dotenv import load_dotenv
from threading import Lock

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

class PostgresClient:
    _pool = None
    _pool_lock = Lock()
    _pool_initialized = False

    def __init__(self):
        self.POSTGRES_URI = os.getenv("POSTGRES_URI")
        if not self.POSTGRES_URI:
            raise ValueError("POSTGRES_URI environment variable not set")

    def _ensure_pool(self):
        """Lazy initialization of connection pool on first use."""
        if not PostgresClient._pool_initialized:
            with PostgresClient._pool_lock:
                if not PostgresClient._pool_initialized:
                    min_connections = int(os.getenv("DB_POOL_MIN_CONNECTIONS", "2"))
                    max_connections = int(os.getenv("DB_POOL_MAX_CONNECTIONS", "20"))

                    try:
                        PostgresClient._pool = psycopg2.pool.ThreadedConnectionPool(
                            minconn=min_connections,
                            maxconn=max_connections,
                            dsn=self.POSTGRES_URI
                        )
                        PostgresClient._pool_initialized = True
                        logger.info(f"✓ PostgreSQL connection pool initialized (min={min_connections}, max={max_connections})")
                    except Exception as e:
                        logger.error(f"✗ Failed to initialize connection pool: {e}")
                        raise
    
    def _serialize_datetime(self, obj):
        """Convert datetime objects to ISO format strings"""
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        return obj
    
    def _process_results(self, results):
        """Process query results to handle datetime serialization"""
        if not results:
            return results
        
        processed_results = []
        for row in results:
            processed_row = {}
            for key, value in dict(row).items():
                processed_row[key] = self._serialize_datetime(value)
            processed_results.append(processed_row)
        return processed_results
    
    def get_connection(self):
        """Get a connection from the pool."""
        self._ensure_pool()
        return PostgresClient._pool.getconn()
    
    def execute_query(self, sql_query: str) -> Dict[str, Any]:
        """
        Execute SQL query and return results.
        
        Args:
            sql_query: The SQL query to execute
            
        Returns:
            Dictionary containing query results or error message
        """
        conn = None
        cursor = None
        
        try:
            conn = self.get_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            logger.info(f"Executing SQL query: {sql_query}")
            cursor.execute(sql_query)
            
            # Handle SELECT queries and INSERT...RETURNING queries
            if (sql_query.strip().upper().startswith('SELECT') or 
                'RETURNING' in sql_query.upper()):
                results = cursor.fetchall()
                processed_results = self._process_results(results)
                logger.info(f"Query returned {len(results)} rows")
                # Commit for INSERT...RETURNING queries
                if not sql_query.strip().upper().startswith('SELECT'):
                    conn.commit()
                return {
                    "success": True, 
                    "data": processed_results, 
                    "row_count": len(results)
                }
            else:
                # For other non-SELECT queries, commit the transaction
                conn.commit()
                affected_rows = cursor.rowcount
                logger.info(f"Query affected {affected_rows} rows")
                return {
                    "success": True, 
                    "affected_rows": affected_rows
                }
                
        except psycopg2.Error as e:
            logger.error(f"Database error: {str(e)}")
            return {"success": False, "error": f"Database error: {str(e)}"}
            
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            return {"success": False, "error": f"Unexpected error: {str(e)}"}
            
        finally:
            if cursor:
                cursor.close()
            if conn:
                # Return connection to pool instead of closing
                PostgresClient._pool.putconn(conn)

    @classmethod
    def close_pool(cls):
        """Close all connections in the pool. Call on application shutdown."""
        if cls._pool:
            cls._pool.closeall()
            cls._pool = None
            logger.info("✓ PostgreSQL connection pool closed")

# Create singleton instance
postgres_client = PostgresClient()