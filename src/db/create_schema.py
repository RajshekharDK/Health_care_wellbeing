"""
src/db/create_schema.py

Purpose:
--------
Creates full clinical + auth schema for HWELLBEING system.
Safe to run multiple times (idempotent).
"""

import asyncio
from src.db.core import execute_query
from src.core.logger import get_logger

logger = get_logger(__name__)


# -----------------------------
# DDL
# -----------------------------
DDL = [

    """
    CREATE COLUMN TABLE HWELLBEING.USERS (
        ID INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
        USERNAME NVARCHAR(100) UNIQUE NOT NULL,
        PASSWORD_HASH NVARCHAR(255) NOT NULL,
        ROLE NVARCHAR(50) DEFAULT 'user',
        CREATED_AT TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """,

    """
    CREATE COLUMN TABLE HWELLBEING.DISEASES (
        ID INT PRIMARY KEY,
        NAME NVARCHAR(200),
        DESCRIPTION NCLOB,
        ICD_CODE NVARCHAR(10)
    )
    """,

    """
    CREATE COLUMN TABLE HWELLBEING.MEDICATIONS (
        ID INT PRIMARY KEY,
        NAME NVARCHAR(200),
        DOSAGE NVARCHAR(100),
        CONTRAINDICATIONS NCLOB
    )
    """,

    """
    CREATE COLUMN TABLE HWELLBEING.TREATMENT_REGIMENS (
        ID INT PRIMARY KEY,
        DISEASE_ID INT NOT NULL,
        NAME NVARCHAR(200),
        DURATION_DAYS INT
    )
    """,

    """
    CREATE COLUMN TABLE HWELLBEING.REGIMEN_LINES (
        ID INT PRIMARY KEY,
        REGIMEN_ID INT NOT NULL,
        MEDICATION_ID INT NOT NULL,

        MORNING_DOSE FLOAT,
        AFTERNOON_DOSE FLOAT,
        EVENING_DOSE FLOAT,

        FREQUENCY NVARCHAR(50),

        DURATION_DAYS INT,
        DURATION_MONTHS INT,

        FOOD_INSTRUCTION NVARCHAR(100),
        SPECIAL_INSTRUCTION NVARCHAR(300),

        LINE_ORDER INT
    )
    """,

    """
    CREATE COLUMN TABLE HWELLBEING.SYMPTOM_INDEX (
        SYMPTOM NVARCHAR(200),
        DISEASE_ID INT,
        WEIGHT FLOAT
    )
    """,

    """
    CREATE COLUMN TABLE HWELLBEING.AUDIT_LOGS (
        ID INT PRIMARY KEY,
        USER_ID NVARCHAR(100),
        ACTION NVARCHAR(200),
        TIMESTAMP TIMESTAMP,
        IP_ADDRESS NVARCHAR(50),
        PAYLOAD NCLOB
    )
    """
]


# -----------------------------
# ALTERS + INDEXES
# -----------------------------
ALTERS = [

    # FKs
    "ALTER TABLE HWELLBEING.TREATMENT_REGIMENS ADD FOREIGN KEY (DISEASE_ID) REFERENCES HWELLBEING.DISEASES(ID)",
    "ALTER TABLE HWELLBEING.REGIMEN_LINES ADD FOREIGN KEY (REGIMEN_ID) REFERENCES HWELLBEING.TREATMENT_REGIMENS(ID)",
    "ALTER TABLE HWELLBEING.REGIMEN_LINES ADD FOREIGN KEY (MEDICATION_ID) REFERENCES HWELLBEING.MEDICATIONS(ID)",

    # INDEXES
    # ⚠ USERS.USERNAME already UNIQUE → index auto-created → skip safe
    "CREATE INDEX IDX_USERS_USERNAME ON HWELLBEING.USERS(USERNAME)",

    "CREATE INDEX IDX_DISEASE_NAME ON HWELLBEING.DISEASES(NAME)",
    "CREATE INDEX IDX_REGIMEN_DISEASE ON HWELLBEING.TREATMENT_REGIMENS(DISEASE_ID)",
    "CREATE INDEX IDX_LINE_REGIMEN ON HWELLBEING.REGIMEN_LINES(REGIMEN_ID)",
    "CREATE INDEX IDX_LINE_MED ON HWELLBEING.REGIMEN_LINES(MEDICATION_ID)"
]


# -----------------------------
# SAFE EXECUTION
# -----------------------------
async def _run_statements(statements, label: str):
    for stmt in statements:
        try:
            await execute_query(stmt)

            logger.info(
                f"{label} executed",
                extra={"extra_data": {"statement": stmt[:80]}}
            )

        except Exception as e:
            err = str(e).lower()

            # 🔥 EXPANDED SAFE HANDLING
            if any(x in err for x in [
                "already exists",
                "duplicate",
                "exists",
                "already indexed",
                "column list already indexed",
                "duplicate foreign key",
                "constraint already exists"
            ]):
                logger.info(
                    f"{label} skipped",
                    extra={"extra_data": {"statement": stmt[:80]}}
                )
            else:
                logger.error(
                    f"{label} failed",
                    extra={
                        "extra_data": {
                            "error": str(e),
                            "statement": stmt
                        }
                    }
                )
                raise


# -----------------------------
# PUBLIC
# -----------------------------
async def create_schema():
    logger.info("Starting schema creation")

    await _run_statements(DDL, "DDL")
    await _run_statements(ALTERS, "ALTER")

    logger.info("Schema creation completed")


# -----------------------------
# CLI
# -----------------------------
from src.db.connection import init_pool, close_pool

if __name__ == "__main__":
    async def run():
        await init_pool()
        try:
            await create_schema()
        finally:
            await close_pool()

    asyncio.run(run())