"""
HWELBEING — CONFIDENCE FILTER

Purpose:
Filters and normalizes ML prediction outputs based on confidence threshold.

Imports From:
- config.settings

Exports To:
- decision_engine

NOTES:
- PURE FUNCTION (no side effects)
- Enforces confidence ∈ [0, 1]
- Sorts results descending
"""

from typing import List, Dict, Any
from src.config import settings


def _normalize_confidence(value: Any) -> float:
    """
    Ensures confidence is a float within [0, 1].
    """

    try:
        val = float(value)
    except (TypeError, ValueError):
        return 0.0

    if val < 0.0:
        return 0.0
    if val > 1.0:
        return 1.0

    return val


def filter_low_confidence(
    conditions: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    Filters conditions below threshold and normalizes confidence.

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

    threshold = settings.CONFIDENCE_THRESHOLD

    filtered = []

    for c in conditions:
        confidence = _normalize_confidence(c.get("confidence"))

        if confidence >= threshold:
            filtered.append({
                **c,
                "confidence": confidence
            })

    # Sort descending by confidence
    filtered.sort(key=lambda x: x["confidence"], reverse=True)

    return filtered