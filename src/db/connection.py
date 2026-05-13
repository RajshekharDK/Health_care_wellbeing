"""
src/db/connection.py

Purpose:
--------
Async-safe SAP HANA connection pool with:
- Health check
- Auto-recovery
- Safe acquire/release
"""

import asyncio
from typing import Optional
from hdbcli import dbapi

from src.config import settings
from src.core.logger import get_logger

logger = get_logger(__name__)

_pool: Optional[asyncio.Queue] = None


# =========================================================
# VALIDATION
# =========================================================
def _validate_config():
    required = [
        settings.HANA_HOST,
        settings.HANA_USER,
        settings.HANA_PASSWORD,
        settings.HANA_SCHEMA
    ]

    if not all(required):
        raise EnvironmentError("Missing required SAP HANA configuration values")


# =========================================================
# CONNECTION CREATION
# =========================================================
def _create_connection():
    return dbapi.connect(
        address=settings.HANA_HOST,
        port=int(settings.HANA_PORT),
        user=settings.HANA_USER,
        password=settings.HANA_PASSWORD,
        encrypt=True,
        sslValidateCertificate=True,
        currentSchema=settings.HANA_SCHEMA
    )


def _is_connection_alive(conn) -> bool:
    """
    Lightweight health check.
    """
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM DUMMY")
        cursor.close()
        return True
    except Exception:
        return False


# =========================================================
# INIT
# =========================================================
async def init_pool():
    global _pool

    if _pool is not None:
        logger.info("DB pool already initialized")
        return

    _validate_config()

    pool_size = settings.DB_POOL_SIZE
    logger.info("Initializing SAP HANA pool", extra={"pool_size": pool_size})

    _pool = asyncio.Queue(maxsize=pool_size)
    loop = asyncio.get_running_loop()

    try:
        for _ in range(pool_size):
            conn = await loop.run_in_executor(None, _create_connection)
            await _pool.put(conn)

        logger.info("SAP HANA pool initialized successfully")

    except Exception as e:
        logger.error("DB pool init failed", extra={"error": str(e)})
        raise RuntimeError("DB pool initialization failed") from e


# =========================================================
# CLOSE
# =========================================================
async def close_pool():
    global _pool

    if _pool is None:
        return

    logger.info("Closing SAP HANA pool")

    while not _pool.empty():
        conn = await _pool.get()
        try:
            conn.close()
        except Exception as e:
            logger.error("Error closing connection", extra={"error": str(e)})

    _pool = None
    logger.info("SAP HANA pool closed")


# =========================================================
# GET CONNECTION
# =========================================================
async def get_connection():
    global _pool

    if _pool is None:
        raise RuntimeError("DB pool not initialized")

    try:
        conn = await asyncio.wait_for(_pool.get(), timeout=10)

        # 🔥 health check
        if not _is_connection_alive(conn):
            logger.warning("Dead connection detected, recreating")

            loop = asyncio.get_running_loop()
            conn = await loop.run_in_executor(None, _create_connection)

        return conn

    except asyncio.TimeoutError:
        logger.error("DB connection timeout")
        raise RuntimeError("Database connection timeout")


# =========================================================
# RELEASE CONNECTION
# =========================================================
async def release_connection(conn):
    global _pool

    if _pool is None:
        return

    try:
        if not _is_connection_alive(conn):
            logger.warning("Dropping dead connection")

            loop = asyncio.get_running_loop()
            conn = await loop.run_in_executor(None, _create_connection)

        # non-blocking put
        _pool.put_nowait(conn)

    except asyncio.QueueFull:
        logger.warning("Pool full, closing extra connection")
        try:
            conn.close()
        except Exception:
            pass

    except Exception as e:
        logger.error("Release failed", extra={"error": str(e)})
        try:
            conn.close()
        except Exception:
            pass