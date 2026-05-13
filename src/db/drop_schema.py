"""
src/db/drop_schema.py

Purpose:
--------
Safely drops all database objects under HWELLBEING schema.
Handles dependencies using CASCADE and executes in async-safe manner.

Imports From:
-------------
- db.core → execute_query
- core.logger → structured logging

Exports:
--------
- drop_schema()
"""

import asyncio
from src.db.core import execute_query
from src.core.logger import get_logger

logger = get_logger(__name__)


# -----------------------------
# DROP ORDER (DEPENDENCY SAFE)
# -----------------------------

DROP_STATEMENTS = [

    # Views first
    "DROP VIEW HWELLBEING.PRESCRIPTION_VIEW",

    # Child tables (CASCADE handles FK but we still order safely)
    "DROP TABLE HWELLBEING.REGIMEN_LINES CASCADE",
    "DROP TABLE HWELLBEING.TREATMENT_REGIMENS CASCADE",

    # Independent tables
    "DROP TABLE HWELLBEING.SYMPTOM_INDEX CASCADE",
    "DROP TABLE HWELLBEING.AUDIT_LOGS CASCADE",
    "DROP TABLE HWELLBEING.MEDICATIONS CASCADE",
    "DROP TABLE HWELLBEING.DISEASES CASCADE"
]


# -----------------------------
# INTERNAL EXECUTION
# -----------------------------

async def _run_drop():
    """
    Execute DROP statements safely and idempotently.
    """

    for stmt in DROP_STATEMENTS:
        try:
            await execute_query(stmt)

            logger.info(
                "DROP executed",
                extra={"extra_data": {"statement": stmt}}
            )

        except Exception as e:
            err = str(e).lower()

            # ✅ Handle ALL HANA "not exists" cases
            if any(x in err for x in [
                "does not exist",
                "invalid table name",
                "invalid view name",
                "unknown"
            ]):
                logger.info(
                    "DROP skipped (not exists)",
                    extra={"extra_data": {"statement": stmt}}
                )
                continue

            # ❌ real error
            logger.error(
                "DROP failed",
                extra={"extra_data": {
                    "statement": stmt,
                    "error": str(e)
                }}
            )
            raise
        
# -----------------------------
# PUBLIC FUNCTION
# -----------------------------

async def drop_schema():
    """
    Drop entire HWELLBEING schema objects safely.
    """
    logger.info("Starting schema drop")

    await _run_drop()

    logger.info("Schema drop completed successfully")


# -----------------------------
# CLI ENTRY
# -----------------------------

from src.db.connection import init_pool, close_pool

if __name__ == "__main__":
    async def run():
        await init_pool()
        try:
            await drop_schema()
        finally:
            await close_pool()

    import asyncio
    asyncio.run(run())