"""
HWELBEING — SKIN SERVICE (PRODUCTION HARDENED + SAFE + CONSISTENT)

Purpose:
- Validate image
- Run CNN (executor-safe)
- Normalize output
- Attach prescription from DB
- Return stable response contract

Imports From:
- ml_engine.skin_cnn.inference
- predictions_api.treatment_service

Exports To:
- FastAPI router
"""

import os
import uuid
import asyncio
from typing import Dict, Any

from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, Request

from src.core.security import verify_token
from src.core.logger import get_logger
from src.limit import limiter, ML_LIMIT

from src.ml_engine.skin_cnn.inference import predict_skin_condition
from src.predictions_api.treatment_service import get_treatment


router = APIRouter(tags=["Skin"])
logger = get_logger(__name__)

TEMP_DIR = "temp_images"
os.makedirs(TEMP_DIR, exist_ok=True)

MAX_FILE_SIZE_MB = 5
CONFIDENCE_THRESHOLD = 0.35  # 🔥 critical guard


# =========================================================
# SAFE PRESCRIPTION FORMAT (MATCH TRIAGE EXACTLY)
# =========================================================
def format_prescription(data: Dict[str, Any]) -> Dict[str, Any]:
    try:
        if not data or not data.get("has_treatment"):
            return {
                "available": False,
                "message": "No prescription available. Please consult a doctor.",
                "medications": []
            }

        meds = data.get("medications", [])

        return {
            "available": True,
            "medications": [
                {
                    "name": m.get("name", ""),
                    "dosage": m.get("dosage"),
                    "duration": m.get("duration"),
                    "instructions": m.get("instructions") or "Take as prescribed"
                }
                for m in meds
            ]
        }

    except Exception:
        return {
            "available": False,
            "message": "No prescription available. Please consult a doctor.",
            "medications": []
        }


# =========================================================
# SAFE RESPONSE
# =========================================================
def safe_response(message: str = "Unable to analyze image") -> Dict[str, Any]:
    return {
        "condition": "Unknown",
        "confidence": 0.0,
        "severity": "unknown",
        "prescription": {
            "available": False,
            "message": "No prescription available. Please consult a doctor.",
            "medications": []
        },
        "message": message
    }


# =========================================================
# HELPERS
# =========================================================
def _validate_file(file: UploadFile, content: bytes):
    if not file.filename:
        raise HTTPException(status_code=400, detail="File missing")

    if not file.filename.lower().endswith((".jpg", ".jpeg", ".png")):
        raise HTTPException(status_code=400, detail="Invalid file type")

    if file.content_type not in ["image/jpeg", "image/png"]:
        raise HTTPException(status_code=400, detail="Invalid content type")

    size_mb = len(content) / (1024 * 1024)
    if size_mb > MAX_FILE_SIZE_MB:
        raise HTTPException(status_code=400, detail="File too large (max 5MB)")


def _normalize_confidence(value) -> float:
    try:
        v = float(value)
    except Exception:
        return 0.0
    return max(0.0, min(1.0, v))


def _normalize_condition(value: str) -> str:
    return value.strip()


async def run_skin_model(file_path: str):
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, predict_skin_condition, file_path)


def _write_file(path: str, content: bytes):
    with open(path, "wb") as f:
        f.write(content)


# =========================================================
# ENDPOINT
# =========================================================
@router.post("/predict/skin")
@limiter.limit(ML_LIMIT)
async def analyze_skin(
    request: Request,
    file: UploadFile = File(...),
    user: dict = Depends(verify_token)
):
    request_id = getattr(request.state, "request_id", "unknown")
    file_path = None

    try:
        # -----------------------------
        # READ FILE
        # -----------------------------
        content = await file.read()
        _validate_file(file, content)

        logger.info(
            "SKIN_REQUEST",
            extra={"request_id": request_id, "file": file.filename}
        )

        # -----------------------------
        # SAVE FILE (SAFE)
        # -----------------------------
        file_id = f"{uuid.uuid4()}.jpg"
        file_path = os.path.join(TEMP_DIR, file_id)

        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, _write_file, file_path, content)

        # -----------------------------
        # MODEL
        # -----------------------------
        prediction: Dict[str, Any] = await run_skin_model(file_path)

        if not prediction or not isinstance(prediction, dict):
            logger.warning(
                "INVALID_SKIN_MODEL_OUTPUT",
                extra={"request_id": request_id}
            )
            return safe_response("Model failed to analyze image")

        # -----------------------------
        # EXTRACT + NORMALIZE
        # -----------------------------
        condition = _normalize_condition(prediction.get("condition", "Unknown"))
        confidence = _normalize_confidence(prediction.get("confidence"))
        severity = str(prediction.get("severity", "unknown"))

        if severity.lower() not in ["mild", "moderate", "severe"]:
            severity = "unknown"

        # -----------------------------
        # LOW CONFIDENCE GUARD (CRITICAL)
        # -----------------------------
        if confidence < CONFIDENCE_THRESHOLD:
            logger.warning(
                "LOW_CONFIDENCE_SKIN",
                extra={"request_id": request_id, "confidence": confidence}
            )

            return safe_response("Low confidence result. Please consult a doctor.")

        # -----------------------------
        # PRESCRIPTION
        # -----------------------------
        try:
            treatment = await get_treatment(condition)
            prescription = format_prescription(treatment)
        except Exception as e:
            logger.warning(
                "PRESCRIPTION_FETCH_FAILED",
                extra={"request_id": request_id, "error": str(e)}
            )
            prescription = format_prescription(None)

        # -----------------------------
        # RESPONSE
        # -----------------------------
        response = {
            "condition": condition,
            "confidence": confidence,
            "severity": severity,
            "prescription": prescription,
            "message": "Analysis completed"
        }

        logger.info(
            "SKIN_SUCCESS",
            extra={
                "request_id": request_id,
                "condition": condition,
                "confidence": confidence
            }
        )

        return response

    except HTTPException:
        raise

    except Exception as e:
        logger.error(
            "SKIN_ERROR",
            extra={"request_id": request_id, "error": str(e)}
        )
        return safe_response("Internal error occurred")

    finally:
        if file_path and os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception:
                pass