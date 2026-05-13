"""
HWELBEING — DISEASE MAPPER

Purpose:
Maps raw ML condition names to standardized disease names.

Imports From:
- decision_engine

Exports To:
- decision_engine

NOTES:
- PURE FUNCTION (no DB calls)
- Converts "condition" → "disease"
- Preserves confidence
- Applies fuzzy matching for normalization
"""

from typing import List, Dict, Any
from difflib import get_close_matches


# -----------------------------------
# KNOWN DISEASE VOCABULARY
# -----------------------------------

KNOWN_DISEASES = [
    "Fever",
    "Viral Infection",
    "Common Cold",
    "Diabetes",
    "Hypertension",
    "Skin Infection"
]


# -----------------------------------
# INTERNAL HELPERS
# -----------------------------------

def _normalize_text(text: str) -> str:
    """
    Normalize input text.
    """
    return text.strip().lower()


def _match_disease(name: str) -> str:
    """
    Fuzzy match disease name to known list.
    """

    if not name:
        return "Unknown condition"

    normalized = _normalize_text(name)

    matches = get_close_matches(
        normalized,
        [d.lower() for d in KNOWN_DISEASES],
        n=1,
        cutoff=0.5
    )

    if matches:
        # return original case version
        for d in KNOWN_DISEASES:
            if d.lower() == matches[0]:
                return d

    # fallback: capitalize cleanly
    return name.strip().capitalize()


# -----------------------------------
# PUBLIC FUNCTION
# -----------------------------------

def map_diseases(
    conditions: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    Maps condition list to standardized disease format.

    Input:
    [
        {
            "condition": str,
            "confidence": float
        }
    ]

    Output:
    [
        {
            "disease": str,
            "confidence": float
        }
    ]
    """

    if not conditions:
        return []

    results = []

    for c in conditions:
        raw_condition = c.get("condition", "")
        confidence = c.get("confidence", 0.0)

        disease = _match_disease(raw_condition)

        results.append({
            "disease": disease,
            "confidence": confidence
        })

    return results