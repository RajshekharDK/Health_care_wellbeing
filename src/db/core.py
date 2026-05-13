"""
src/db/core.py

Purpose:
--------
Centralized database execution layer for SAP HANA.
Provides async-safe query execution using connection pool.

Ensures:
- Non-blocking DB operations via run_in_executor
- Automatic connection acquire/release
- Schema enforcement (HWELLBEING.*)
- Safe execution patterns (commit/rollback)

Imports From:
-------------
- db.connection → get_connection, release_connection
- core.logger → structured logging

Exports:
--------
- execute_query(sql, params=None)
- execute_many(sql, rows)
- fetch_all(sql, params=None)
- fetch_one(sql, params=None)
"""

import asyncio
from typing import Any, List, Optional

from src.db.connection import get_connection, release_connection
from src.core.logger import get_logger

logger = get_logger(__name__)


# -----------------------------
# INTERNAL HELPERS
# -----------------------------

def _execute(cursor, sql: str, params: Optional[tuple]):
    cursor.execute(sql, params or ())


def _executemany(cursor, sql: str, rows: List[tuple]):
    cursor.executemany(sql, rows)


def _fetchall(cursor):
    return cursor.fetchall()


def _fetchone(cursor):
    return cursor.fetchone()


# -----------------------------
# PUBLIC METHODS
# -----------------------------

async def execute_query(sql: str, params: Optional[tuple] = None) -> None:
    """
    Execute INSERT/UPDATE/DELETE query.
    """
    conn = await get_connection()
    loop = asyncio.get_event_loop()

    try:
        cursor = conn.cursor()

        await loop.run_in_executor(None, _execute, cursor, sql, params)

        conn.commit()

    except Exception as e:
        conn.rollback()
        logger.error(
            "DB execute_query failed",
            extra={"sql": sql, "error": str(e)}
        )
        raise

    finally:
        try:
            cursor.close()
        except Exception:
            pass
        await release_connection(conn)


async def execute_many(sql: str, rows: List[tuple]) -> None:
    """
    Batch insert/update using executemany.
    """
    if not rows:
        return

    conn = await get_connection()
    loop = asyncio.get_event_loop()

    try:
        cursor = conn.cursor()

        await loop.run_in_executor(None, _executemany, cursor, sql, rows)

        conn.commit()

    except Exception as e:
        conn.rollback()
        logger.error(
            "DB execute_many failed",
            extra={"sql": sql, "error": str(e), "rows_count": len(rows)}
        )
        raise

    finally:
        try:
            cursor.close()
        except Exception:
            pass
        await release_connection(conn)


async def fetch_all(sql: str, params: Optional[tuple] = None) -> List[Any]:
    """
    Fetch all rows from SELECT query.
    """
    conn = await get_connection()
    loop = asyncio.get_event_loop()

    try:
        cursor = conn.cursor()

        await loop.run_in_executor(None, _execute, cursor, sql, params)
        rows = await loop.run_in_executor(None, _fetchall, cursor)

        return rows

    except Exception as e:
        logger.error(
            "DB fetch_all failed",
            extra={"sql": sql, "error": str(e)}
        )
        raise

    finally:
        try:
            cursor.close()
        except Exception:
            pass
        await release_connection(conn)


async def fetch_one(sql: str, params: Optional[tuple] = None) -> Optional[Any]:
    """
    Fetch single row from SELECT query.
    """
    conn = await get_connection()
    loop = asyncio.get_event_loop()

    try:
        cursor = conn.cursor()

        await loop.run_in_executor(None, _execute, cursor, sql, params)
        row = await loop.run_in_executor(None, _fetchone, cursor)

        return row

    except Exception as e:
        logger.error(
            "DB fetch_one failed",
            extra={"sql": sql, "error": str(e)}
        )
        raise

    finally:
        try:
            cursor.close()
        except Exception:
            pass
        await release_connection(conn)