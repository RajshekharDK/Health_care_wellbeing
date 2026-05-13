"""
HWELBEING — CLINICAL RULES ENGINE (FINAL)

Purpose:
- Adjust ML confidence using clinical logic
- Add explanation for UI
- Keep ML as base truth (no distortion)
"""

from typing import List, Dict, Any


# =========================================================
# HELPERS
# =========================================================

def _normalize(text: str) -> str:
    return text.strip().lower()


def _has(symptoms: List[str], keyword: str) -> bool:
    return any(keyword in _normalize(s) for s in symptoms)


# =========================================================
# MAIN RULE ENGINE
# =========================================================

def apply_clinical_rules(
    symptoms: List[str],
    conditions: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:

    if not conditions:
        return []

    updated = []

    for c in conditions:
        name = _normalize(c.get("disease", ""))  # ✅ FIXED
        confidence = float(c.get("confidence", 0.0))
        explanation = "Based on symptom pattern"

        # --------------------------------------------------
        # ASTHMA / RESPIRATORY
        # --------------------------------------------------
        if "asthma" in name or "bronchial" in name:
            if _has(symptoms, "cough") and _has(symptoms, "breath"):
                confidence += 0.05
                explanation = "Respiratory symptoms match asthma"
            else:
                confidence -= 0.03

        # --------------------------------------------------
        # PNEUMONIA
        # --------------------------------------------------
        if "pneumonia" in name:
            if _has(symptoms, "fever") and _has(symptoms, "cough"):
                confidence += 0.06
                explanation = "Fever + cough aligns with pneumonia"
            else:
                confidence -= 0.03

        # --------------------------------------------------
        # DENGUE
        # --------------------------------------------------
        if "dengue" in name:
            if _has(symptoms, "fever") and _has(symptoms, "body pain"):
                confidence += 0.05
                explanation = "Fever + body pain suggests dengue"
            else:
                confidence -= 0.02

        # --------------------------------------------------
        # DIABETES
        # --------------------------------------------------
        if "diabetes" in name:
            if _has(symptoms, "fatigue"):
                confidence += 0.03
                explanation = "Fatigue may relate to diabetes"
            else:
                confidence -= 0.02

        # --------------------------------------------------
        # GENERAL SEVERITY BOOST
        # --------------------------------------------------
        if _has(symptoms, "severe"):
            confidence += 0.03

        # --------------------------------------------------
        # CLAMP (IMPORTANT)
        # --------------------------------------------------
        confidence = max(0.0, min(1.0, confidence))

        # --------------------------------------------------
        # KEEP ONLY VERY LOW REMOVAL
        # --------------------------------------------------
        if confidence < 0.02:
            continue

        updated.append({
            "disease": c.get("disease"),
            "confidence": confidence,
            "explanation": explanation
        })

    # ------------------------------------------------------
    # SORT
    # ------------------------------------------------------
    updated.sort(key=lambda x: x["confidence"], reverse=True)

    return updated