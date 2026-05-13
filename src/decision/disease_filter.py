"""
HWELBEING — DISEASE FILTER

Purpose:
Filters candidate diseases based on symptom relevance and confidence.

Imports From:
- config.settings

Exports To:
- decision_engine

NOTES:
- PURE FUNCTION (no side effects)
- No hardcoded disease rules (handled in clinical_rules.py)
- Uses symptom overlap scoring
"""

from typing import List, Dict, Any
from src.config import settings


# -----------------------------------
# HELPERS
# -----------------------------------

def _normalize(text: str) -> str:
    return text.strip().lower()


def _calculate_overlap_score(
    disease_name: str,
    symptoms: List[str]
) -> int:
    """
    Simple keyword-based overlap scoring.
    """

    if not disease_name or not symptoms:
        return 0

    name_tokens = set(_normalize(disease_name).split())
    symptom_tokens = set(_normalize(s) for s in symptoms)

    return len(name_tokens.intersection(symptom_tokens))


# -----------------------------------
# MAIN FILTER
# -----------------------------------

def filter_conditions(
    conditions: List[Dict[str, Any]],
    symptoms: List[str]
) -> List[Dict[str, Any]]:
    """
    Filters and ranks conditions using:
    - Confidence
    - Symptom overlap

    Returns:
    [
        {
            "condition": str,
            "confidence": float
        }
    ]
    """

    if not conditions:
        return []

    max_results = settings.MAX_CONDITIONS  # e.g. 3–5

    scored = []

    for c in conditions:
        name = c.get("condition", "")
        confidence = c.get("confidence", 0.0)

        overlap = _calculate_overlap_score(name, symptoms)

        # Combined score (weighted)
        score = (confidence * 0.8) + (overlap * 0.2)

        scored.append({
            **c,
            "_score": score
        })

    # Sort by combined score
    scored.sort(key=lambda x: x["_score"], reverse=True)

    # Remove internal score before returning
    results = [
        {k: v for k, v in item.items() if k != "_score"}
        for item in scored[:max_results]
    ]

    return results