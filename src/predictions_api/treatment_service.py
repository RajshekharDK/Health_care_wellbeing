"""
HWELBEING — TREATMENT SERVICE (PRODUCTION HARDENED)

Purpose:
- Fetch prescription using DISEASE_ID
- Handles real-world name mismatches (Typhoid vs Typhoid Fever)
- Executor-safe DB operations
- Always returns stable structure

Exports To:
- triage_service
"""

import asyncio
from typing import Dict, List, Any, Optional

from src.db.connection import get_connection, release_connection
from src.core.logger import get_logger

logger = get_logger(__name__)


# ============================
# EXECUTOR HELPERS
# ============================

def _execute(cursor, query, params):
    cursor.execute(query, params)


def _fetchall(cursor):
    return cursor.fetchall()


def _fetchone(cursor):
    return cursor.fetchone()


# ============================
# NORMALIZER
# ============================

def normalize_disease_name(name: str) -> str:
    return name.strip().lower()


# ============================
# GET DISEASE ID (ROBUST)
# ============================

async def get_disease_id(cursor, loop, disease: str) -> Optional[int]:
    clean = normalize_disease_name(disease)

    # ---------------------------
    # 1. EXACT MATCH
    # ---------------------------
    exact_query = """
    SELECT ID
    FROM HWELLBEING.DISEASES
    WHERE LOWER(TRIM(NAME)) = ?
    """

    await loop.run_in_executor(None, _execute, cursor, exact_query, (clean,))
    result = await loop.run_in_executor(None, _fetchone, cursor)

    if result:
        return result[0]

    # ---------------------------
    # 2. LIKE MATCH (CRITICAL FIX)
    # ---------------------------
    like_query = """
    SELECT ID
    FROM HWELLBEING.DISEASES
    WHERE LOWER(NAME) LIKE ?
    ORDER BY LENGTH(NAME) ASC
    """

    like_param = f"%{clean}%"

    await loop.run_in_executor(None, _execute, cursor, like_query, (like_param,))
    result = await loop.run_in_executor(None, _fetchone, cursor)

    if result:
        logger.info("DISEASE_MATCHED_LIKE", extra={"input": disease, "matched_id": result[0]})
        return result[0]

    return None


# ============================
# MAIN SERVICE
# ============================

async def get_treatment(disease: str) -> Dict[str, Any]:
    conn = None

    try:
        conn = await get_connection()
        cursor = conn.cursor()

        loop = asyncio.get_running_loop()

        logger.info("TREATMENT_LOOKUP", extra={"disease": disease})

        # ---------------------------
        # STEP 1: RESOLVE DISEASE ID
        # ---------------------------
        disease_id = await get_disease_id(cursor, loop, disease)

        if not disease_id:
            logger.warning("DISEASE_NOT_FOUND", extra={"disease": disease})

            cursor.close()
            return {
                "has_treatment": False,
                "medications": []
            }

        # ---------------------------
        # STEP 2: FETCH REGIMEN
        # ---------------------------
        treatment_query = """
        SELECT 
            M.NAME,
            RL.SPECIAL_INSTRUCTION
        FROM HWELLBEING.TREATMENT_REGIMENS TR
        JOIN HWELLBEING.REGIMEN_LINES RL ON TR.ID = RL.REGIMEN_ID
        JOIN HWELLBEING.MEDICATIONS M ON RL.MEDICATION_ID = M.ID
        WHERE TR.DISEASE_ID = ?
        ORDER BY RL.LINE_ORDER
        """

        await loop.run_in_executor(None, _execute, cursor, treatment_query, (disease_id,))
        rows = await loop.run_in_executor(None, _fetchall, cursor)

        cursor.close()

        # ---------------------------
        # NO DATA
        # ---------------------------
        if not rows:
            logger.warning("NO_TREATMENT_FOUND", extra={"disease_id": disease_id})

            return {
                "has_treatment": False,
                "medications": []
            }

        # ---------------------------
        # FORMAT RESPONSE
        # ---------------------------
        medications: List[Dict[str, Any]] = []

        for row in rows:
            name = row[0]
            instruction = row[1]

            medications.append({
                "name": name,
                "dosage": None,
                "duration": None,
                "instructions": instruction or "Take as prescribed"
            })

        return {
            "has_treatment": True,
            "medications": medications
        }

    except Exception as e:
        logger.error("TREATMENT_FETCH_ERROR", extra={"error": str(e)})

        return {
            "has_treatment": False,
            "medications": []
        }

    finally:
        if conn:
            await release_connection(conn)