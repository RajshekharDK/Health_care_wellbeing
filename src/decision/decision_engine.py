"""
HWELBEING — DECISION ENGINE (AI-COMPATIBLE + SAFE)
"""

from typing import List, Dict, Any
import asyncio

from src.decision.clinical_rules import apply_clinical_rules
from src.decision.risk_engine import adjust_with_risk
from src.core.logger import get_logger

logger = get_logger(__name__)


# ======================================================
# CLEAN SYMPTOMS
# ======================================================
def _clean_symptoms(symptoms: List[str]) -> List[str]:
    return list({
        s.lower().strip()
        for s in symptoms
        if isinstance(s, str) and len(s.strip()) > 2
    })


# ======================================================
# INTERNAL PIPELINE
# ======================================================
def _run_decision_pipeline(
    symptoms: List[str],
    ml_output: Dict[str, Any]
) -> List[Dict[str, Any]]:

    try:
        symptoms = _clean_symptoms(symptoms)

        # 🔥 REQUIRE MINIMUM CONTEXT
        if len(symptoms) < 2:
            return []

        conditions = ml_output.get("possible_conditions", [])

        if not isinstance(conditions, list) or not conditions:
            return []

        # =========================
        # STEP 1: SORT
        # =========================
        conditions = sorted(
            conditions,
            key=lambda x: float(x.get("confidence", 0)),
            reverse=True
        )

        # =========================
        # STEP 2: CLINICAL RULES
        # =========================
        conditions = apply_clinical_rules(symptoms, conditions)
        if not conditions:
            return []

        # =========================
        # STEP 3: RISK ENGINE
        # =========================
        conditions = adjust_with_risk(
            symptoms=symptoms,
            duration=None,
            conditions=conditions
        )
        if not conditions:
            return []

        # =========================
        # STEP 4: FILTER LOW CONF
        # =========================
        conditions = [
            c for c in conditions
            if float(c.get("confidence", 0)) >= 0.35  # 🔥 slightly relaxed
        ]

        if not conditions:
            return []

        # =========================
        # STEP 5: NORMALIZE (SAFE)
        # =========================
        max_conf = max(float(c.get("confidence", 0)) for c in conditions)

        for c in conditions:
            try:
                raw = float(c.get("confidence", 0))

                # 🔥 SOFT NORMALIZATION (avoid 1.0 certainty)
                c["confidence"] = round(
                    min((raw / max_conf) * 0.85, 0.85),
                    3
                )
            except Exception:
                c["confidence"] = 0.3

        # =========================
        # STEP 6: LIMIT TOP 3
        # =========================
        conditions = conditions[:3]

        # =========================
        # STEP 7: FORMAT OUTPUT
        # =========================
        results = []

        for c in conditions:
            try:
                results.append({
                    "disease": c.get("disease", "Unknown"),
                    "confidence": float(c.get("confidence", 0)),
                    "risk": c.get("risk", "low"),
                    "explanation": c.get(
                        "explanation",
                        "Based on symptom patterns"
                    )
                })
            except Exception:
                continue

        return results

    except Exception as e:
        logger.error("DECISION_PIPELINE_ERROR", extra={"error": str(e)})
        return []


# ======================================================
# PUBLIC ENTRY
# ======================================================
async def run_decision_engine(
    symptoms: List[str],
    ml_output: Dict[str, Any]
) -> List[Dict[str, Any]]:

    if not symptoms or not ml_output:
        return []

    try:
        loop = asyncio.get_running_loop()

        return await loop.run_in_executor(
            None,
            _run_decision_pipeline,
            symptoms,
            ml_output
        )

    except Exception as e:
        logger.error("DECISION_ENGINE_ERROR", extra={"error": str(e)})
        return []