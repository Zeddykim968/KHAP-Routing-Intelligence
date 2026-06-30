"""
Database service — uses local Replit PostgreSQL via psycopg2.
Connection pool (SimpleConnectionPool) for thread safety.
All query helpers return plain dicts for JSON serialisation.
"""

import os
import logging
from typing import Any, Dict, List, Optional
from contextlib import contextmanager

import psycopg2
from psycopg2 import pool
from psycopg2.extras import RealDictCursor

logger = logging.getLogger(__name__)

DATABASE_URL = os.getenv("DATABASE_URL", "")

if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL environment variable is not set.")

_pool: Optional[pool.SimpleConnectionPool] = None


def get_pool() -> pool.SimpleConnectionPool:
    global _pool
    if _pool is None:
        _pool = pool.SimpleConnectionPool(
            minconn=1,
            maxconn=10,
            dsn=DATABASE_URL,
        )
        logger.info("DB connection pool initialised")
    return _pool


@contextmanager
def get_conn():
    """Context manager — borrows a connection from the pool."""
    p = get_pool()
    conn = p.getconn()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        p.putconn(conn)


def query(sql: str, params=None) -> List[Dict[str, Any]]:
    """Execute a SELECT and return list of dicts."""
    with get_conn() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(sql, params)
            return [dict(r) for r in cur.fetchall()]


def query_one(sql: str, params=None) -> Optional[Dict[str, Any]]:
    """Execute a SELECT and return a single dict or None."""
    rows = query(sql, params)
    return rows[0] if rows else None


def execute(sql: str, params=None) -> int:
    """Execute INSERT/UPDATE/DELETE. Returns rowcount."""
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            return cur.rowcount


def execute_returning(sql: str, params=None) -> Optional[Dict[str, Any]]:
    """Execute INSERT ... RETURNING and return the new row."""
    with get_conn() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(sql, params)
            row = cur.fetchone()
            return dict(row) if row else None
