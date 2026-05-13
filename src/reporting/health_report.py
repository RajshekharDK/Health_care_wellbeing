"""
HWELBEING — HEALTH REPORT GENERATOR

Purpose:
Generate structured, human-readable health reports from model predictions
and treatment guidance.

Imports:
- Used by prediction services

Exports:
- generate_health_report()
"""

from typing import List, Dict


DISCLAIMER = (
    "⚠ This is an AI-assisted health analysis and NOT a medical diagnosis. "
    "Please consult a qualified healthcare professional before taking any medication."
)


# ==========================================================
# HELPERS
# ==========================================================

def _normalize_confidence(value) -> float:
    try:
        v = float(value)
    except Exception:
        return 0.0
    return max(0.0, min(1.0, v))


# ==========================================================
# FORMAT CONDITIONS
# ==========================================================

def _format_conditions(conditions: List[Dict]) -> str:

    if not conditions:
        return "No significant conditions detected."

    # Ensure sorted
    conditions = sorted(
        conditions,
        key=lambda x: _normalize_confidence(x.get("confidence")),
        reverse=True
    )

    lines = []

    for c in conditions:
        name = c.get("disease") or c.get("condition", "Unknown")
        confidence = _normalize_confidence(c.get("confidence"))

        lines.append(f"- {name} (Confidence: {confidence:.2f})")

    return "\n".join(lines)


# ==========================================================
# FORMAT TREATMENT
# ==========================================================

def _format_treatment(treatment: List[Dict]) -> str:

    if not treatment:
        return "No medication data available. Please consult a doctor."

    lines = []

    for t in treatment:
        # Align with DB output
        med = t.get("drug", "Medication")
        dose = t.get("dose", "")
        freq = t.get("frequency", "")
        food = t.get("food_instruction", "")

        line = f"- {med}"

        if dose:
            line += f" | Dose: {dose}"
        if freq:
            line += f" | Frequency: {freq}"
        if food:
            line += f" | Note: {food}"

        lines.append(line)

    return "\n".join(lines)


# ==========================================================
# SUMMARY GENERATOR
# ==========================================================

def _generate_summary(conditions: List[Dict]) -> str:

    if not conditions:
        return "No clear condition identified."

    top = max(
        conditions,
        key=lambda x: _normalize_confidence(x.get("confidence"))
    )

    name = top.get("disease") or top.get("condition", "Unknown")
    confidence = _normalize_confidence(top.get("confidence"))

    if confidence >= 0.75:
        return f"The analysis strongly indicates a possible case of {name}."
    elif confidence >= 0.5:
        return f"The symptoms suggest a possible condition related to {name}."
    else:
        return "The prediction is uncertain. Further medical evaluation is recommended."


# ==========================================================
# MAIN REPORT FUNCTION
# ==========================================================

def generate_health_report(
    possible_conditions: List[Dict],
    treatment_guidance: List[Dict]
) -> str:

    if not possible_conditions:
        return "Unable to generate report. No condition predicted."

    condition_text = _format_conditions(possible_conditions)
    treatment_text = _format_treatment(treatment_guidance)
    summary_text = _generate_summary(possible_conditions)

    report = f"""
================= HWELBEING REPORT =================

Possible Conditions:
{condition_text}

Summary:
{summary_text}

Recommended Guidance:
{treatment_text}

General Care Advice:
• Maintain good hygiene
• Stay hydrated
• Get adequate rest
• Monitor symptoms regularly
• Seek medical attention if symptoms worsen

{DISCLAIMER}
"""

    return report.strip()