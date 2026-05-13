"""
HWELBEING — EXPLAINER

Purpose:
Generates human-readable explanations for predicted diseases.

Imports From:
- decision_engine (input data)

Exports To:
- decision_engine

NOTES:
- PURE FUNCTION (no side effects)
- Produces consistent, clinical-style explanations
- Uses ONLY "confidence"
"""

from typing import List, Dict, Any


def _format_symptoms(symptoms: List[str]) -> str:
    """
    Formats symptom list into readable string.
    Example: ["fever", "cough"] → "Fever + cough"
    """

    if not symptoms:
        return "Unknown symptoms"

    formatted = [s.strip().capitalize() for s in symptoms if s]
    return " + ".join(formatted)


def _build_single_explanation(
    symptoms: List[str],
    disease: str,
    confidence: float
) -> str:
    """
    Builds one explanation string.
    """

    symptom_str = _format_symptoms(symptoms)
    confidence_str = f"{confidence:.2f}"

    return f"{symptom_str} → {disease} ({confidence_str})"


def build_explanations(
    symptoms: List[str],
    conditions: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    Attaches explanation to each condition.

    Input:
    [
        {
            "disease": str,
            "confidence": float
        }
    ]

    Output:
    [
        {
            "disease": str,
            "confidence": float,
            "explanation": str
        }
    ]
    """

    if not conditions:
        return []

    results = []

    for c in conditions:
        disease = c.get("disease", "Unknown condition")
        confidence = c.get("confidence", 0.0)

        explanation = _build_single_explanation(
            symptoms,
            disease,
            confidence
        )

        results.append({
            **c,
            "explanation": explanation
        })

    return results