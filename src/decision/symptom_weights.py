"""
HWELBEING — SYMPTOM WEIGHTS ENGINE (CLINICAL UPGRADE)

Purpose:
- Calculate severity score
- Detect critical symptoms
- Provide normalized severity (0–1)

Exports To:
- decision_engine
- risk_engine
"""

from typing import List, Dict


# =========================================================
# WEIGHT CONFIG (CLINICAL)
# =========================================================

SYMPTOM_WEIGHTS: Dict[str, int] = {
    # 🔴 CRITICAL (life-threatening indicators)
    "chest pain": 5,
    "shortness of breath": 5,
    "difficulty breathing": 5,
    "fainting": 5,
    "loss of consciousness": 5,
    "severe headache": 5,

    # 🟠 HIGH
    "high fever": 4,
    "persistent fever": 4,
    "vomiting": 4,
    "severe vomiting": 4,
    "diarrhea": 4,

    # 🟡 MEDIUM
    "fever": 3,
    "cough": 3,
    "headache": 3,
    "body pain": 3,

    # 🟢 LOW
    "fatigue": 1,
    "weakness": 1,
    "cold": 1,
    "runny nose": 1
}


# Max score (top 5 symptoms)
MAX_SCORE = sum(sorted(SYMPTOM_WEIGHTS.values(), reverse=True)[:5])


# =========================================================
# HELPERS
# =========================================================

def _normalize(text: str) -> str:
    return text.strip().lower()


def _match_weight(symptom: str) -> int:
    """
    More precise matching:
    - Exact match OR contained phrase
    """

    symptom = _normalize(symptom)

    for key, weight in SYMPTOM_WEIGHTS.items():
        if key == symptom or key in symptom:
            return weight

    return 0


def _is_critical(symptom: str) -> bool:
    CRITICAL_KEYS = [
        "chest pain",
        "shortness of breath",
        "difficulty breathing",
        "fainting",
        "loss of consciousness"
    ]

    symptom = _normalize(symptom)

    return any(key in symptom for key in CRITICAL_KEYS)


# =========================================================
# MAIN FUNCTION
# =========================================================

def calculate_symptom_score(symptoms: List[str]) -> Dict[str, float]:
    """
    Returns:
    {
        "raw_score": int,
        "normalized_score": float,
        "critical": bool
    }
    """

    if not symptoms:
        return {
            "raw_score": 0,
            "normalized_score": 0.0,
            "critical": False
        }

    unique_symptoms = set(_normalize(s) for s in symptoms if s)

    score = 0
    critical_flag = False

    for s in unique_symptoms:
        score += _match_weight(s)

        if _is_critical(s):
            critical_flag = True

    normalized = min(score / MAX_SCORE, 1.0) if MAX_SCORE else 0.0

    return {
        "raw_score": score,
        "normalized_score": normalized,
        "critical": critical_flag
    }