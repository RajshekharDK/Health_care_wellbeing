"""
HWELBEING — RISK ENGINE (CLINICAL FINAL)

Purpose:
- Adjust confidence per disease
- Compute risk level
- Use symptom severity + ML confidence

Exports:
- decision_engine
"""

from typing import List, Dict, Any
from src.decision.symptom_weights import calculate_symptom_score


# =========================================================
# RISK LEVEL LOGIC
# =========================================================

def _get_risk_level(confidence: float, critical: bool) -> str:
    if critical:
        return "high"

    if confidence >= 0.7:
        return "high"
    elif confidence >= 0.4:
        return "medium"
    else:
        return "low"


# =========================================================
# MAIN FUNCTION
# =========================================================

def adjust_with_risk(
    symptoms: List[str],
    duration: str,
    conditions: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    Returns:
    [
        {
            "disease": str,
            "confidence": float,
            "risk": str
        }
    ]
    """

    if not conditions:
        return []

    severity_data = calculate_symptom_score(symptoms)
    severity_score = severity_data["normalized_score"]
    critical_flag = severity_data["critical"]

    updated = []

    for c in conditions:
        try:
            base_conf = float(c.get("confidence", 0.0))

            # -----------------------------------
            # Fusion formula (SAFE)
            # -----------------------------------
            final_conf = (
                (base_conf * 0.7) +   # ML remains dominant
                (severity_score * 0.3)
            )

            final_conf = max(0.0, min(1.0, final_conf))

            # -----------------------------------
            # Risk Level
            # -----------------------------------
            risk = _get_risk_level(final_conf, critical_flag)

            updated.append({
                **c,
                "confidence": final_conf,
                "risk": risk
            })

        except Exception:
            continue

    # Sort by confidence
    updated.sort(key=lambda x: x["confidence"], reverse=True)

    return updated