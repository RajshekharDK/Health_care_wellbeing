"""
HWELBEING — TRIAGE SERVICE (PRODUCTION HARDENED)

Purpose:
- Accept symptoms
- Run NLP model (executor-safe)
- Apply decision engine (pure logic)
- Fetch treatment from DB (single source of truth)
- Return stable, frontend-safe response

Exports To:
- FastAPI router
"""

import asyncio
from typing import List, Dict, Any

from pydantic import BaseModel

from fastapi import APIRouter, Depends, HTTPException, Request

from src.core.security import verify_token
from src.core.logger import get_logger
from src.limit import limiter, ML_LIMIT

from src.ml_engine.nlp_triage.inference import predict_nlp_triage
from src.decision.decision_engine import run_decision_engine
from src.Conversational_module.symptom_parser import extract_symptoms
from src.predictions_api.treatment_service import get_treatment


router = APIRouter(tags=["Triage"])
logger = get_logger(__name__)

DISCLAIMER = "This is an AI-assisted assessment and not a medical diagnosis."


# =========================
# REQUEST MODEL
# =========================
class TriageRequest(BaseModel):
    symptoms: List[str]


# =========================
# SAFE PRESCRIPTION FORMAT
# =========================
def format_prescription(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Always return frontend-safe structure
    """
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


# =========================
# SAFE FALLBACK RESPONSE
# =========================
def safe_response(message: str = "Unable to determine condition") -> List[Dict[str, Any]]:
    return [
        {
            "disease": "Unknown",
            "confidence": 0.0,
            "risk": "low",
            "explanation": f"{message} ({DISCLAIMER})",
            "prescription": {
                "available": False,
                "message": "No prescription available. Please consult a doctor.",
                "medications": []
            }
        }
    ]


# =========================
# NLP EXECUTION (ASYNC SAFE)
# =========================
async def run_nlp(symptoms: str) -> Dict[str, Any]:
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, predict_nlp_triage, symptoms)


# =========================
# MAIN ENDPOINT
# =========================
@router.post("/predict/symptoms")
@limiter.limit(ML_LIMIT)
async def triage(
    request: Request,
    payload: TriageRequest,
    user: dict = Depends(verify_token)
):
    request_id = getattr(request.state, "request_id", "unknown")

    try:
        # ---------------------------
        # VALIDATION
        # ---------------------------
        if not payload.symptoms or not isinstance(payload.symptoms, list):
            raise HTTPException(status_code=400, detail="Symptoms required")

        raw_input = ", ".join(payload.symptoms).strip()

        logger.info(
            "TRIAGE_REQUEST",
            extra={"request_id": request_id, "symptoms": payload.symptoms}
        )

        # ---------------------------
        # NLP MODEL
        # ---------------------------
        ml_output = await run_nlp(raw_input)

        if not isinstance(ml_output, dict) or "possible_conditions" not in ml_output:
            logger.warning(
                "INVALID_ML_OUTPUT",
                extra={"request_id": request_id, "ml_output": str(ml_output)}
            )
            return safe_response("Model could not process input")

        # ---------------------------
        # SYMPTOM PARSER
        # ---------------------------
        parsed_symptoms = extract_symptoms(raw_input)

        if not parsed_symptoms:
            logger.warning(
                "NO_SYMPTOMS_PARSED",
                extra={"request_id": request_id}
            )
            return safe_response("No valid symptoms detected")

        # ---------------------------
        # DECISION ENGINE
        # ---------------------------
        results = await run_decision_engine(parsed_symptoms, ml_output)

        # ---------------------------
        # FALLBACK (ML ONLY)
        # ---------------------------
        if not results:
            fallback = ml_output.get("possible_conditions", [])[:1]

            if fallback:
                disease = fallback[0].get("disease", "Unknown")

                try:
                    treatment = await get_treatment(disease)
                except Exception as e:
                    logger.warning(
                        "FALLBACK_TREATMENT_FAIL",
                        extra={"request_id": request_id, "error": str(e)}
                    )
                    treatment = None

                return [{
                    "disease": disease,
                    "confidence": float(fallback[0].get("confidence", 0.0)),
                    "risk": "low",
                    "explanation": f"Based on ML prediction ({DISCLAIMER})",
                    "prescription": format_prescription(treatment)
                }]

            return safe_response("No prediction available")

        # ---------------------------
        # FETCH TREATMENT (STRICT)
        # ---------------------------
        final_results: List[Dict[str, Any]] = []

        for r in results:
            disease = r.get("disease", "Unknown")

            # normalize early
            confidence = float(r.get("confidence", 0.0))
            explanation = r.get("explanation", "")

            try:
                treatment = await get_treatment(disease)
            except Exception as e:
                logger.warning(
                    "TREATMENT_FETCH_FAILED",
                    extra={"request_id": request_id, "disease": disease, "error": str(e)}
                )
                treatment = None

            final_results.append({
                "disease": disease,
                "confidence": confidence,
                "risk": r.get("risk", "low"),
                "explanation": f"{explanation} ({DISCLAIMER})",
                "prescription": format_prescription(treatment)
            })

        logger.info(
            "TRIAGE_SUCCESS",
            extra={
                "request_id": request_id,
                "count": len(final_results),
                "top": final_results[0]["disease"] if final_results else None
            }
        )

        return final_results

    except HTTPException:
        raise

    except Exception as e:
        logger.error(
            "TRIAGE_ERROR",
            extra={"request_id": request_id, "error": str(e)}
        )
        return safe_response("Internal error occurred")