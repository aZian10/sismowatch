"""
Database Connection Manager for FastAPI.
Uses connection context with psycopg2 RealDictCursor.
"""
from contextlib import contextmanager
from typing import Generator, Any
import psycopg2
from psycopg2.extras import RealDictCursor
import logging

from api.src.config import (
    DB_HOST, DB_PORT, DB_NAME, DB_APP_USER, DB_APP_PASSWORD,
    DB_ADMIN_USER, DB_ADMIN_PASSWORD
)

logger = logging.getLogger("sismowatch.api.database")

@contextmanager
def get_db(admin: bool = False) -> Generator[psycopg2.extensions.connection, None, None]:
    """Provides a database connection with automatic commit and rollback."""
    user = DB_ADMIN_USER if admin else DB_APP_USER
    password = DB_ADMIN_PASSWORD if admin else DB_APP_PASSWORD
    
    conn = psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
        user=user,
        password=password,
        cursor_factory=RealDictCursor,
        connect_timeout=10
    )
    try:
        yield conn
        conn.commit()
    except Exception as e:
        conn.rollback()
        logger.error(f"API database error: {e}")
        raise
    finally:
        conn.close()
