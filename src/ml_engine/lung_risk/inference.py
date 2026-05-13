"""
HWELBEING — LUNG RISK INFERENCE (PRODUCTION)

Purpose:
Estimate lung cancer risk using trained sklearn pipeline.

Imports From:
- pipeline.pkl
- schema.json

Exports To:
- predictions_api (service layer)

NOTES:
- No FastAPI here
- No async here
- Returns standardized response
"""

import os
import json
import joblib
import pandas as pd
from typing import Dict, List


# ======================================================
# PATHS
# ======================================================

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))

PIPELINE_PATH = os.path.join(CURRENT_DIR, "pipeline.pkl")
SCHEMA_PATH = os.path.join(CURRENT_DIR, "schema.json")


# ======================================================
# SAFE MODEL LOADING
# ======================================================

try:
    pipeline = joblib.load(PIPELINE_PATH)
except Exception as e:
    raise RuntimeError(f"Failed to load lung risk model: {str(e)}")

try:
    with open(SCHEMA_PATH, "r") as f:
        schema = json.load(f)
        EXPECTED_FEATURES = schema["features"]
except Exception as e:
    raise RuntimeError(f"Failed to load schema.json: {str(e)}")


# ======================================================
# RISK LEVEL LOGIC
# ======================================================

def _calculate_risk(confidence: float) -> str:
    if confidence < 0.35:
        return "LOW"
    elif confidence < 0.65:
        return "MODERATE"
    else:
        return "HIGH"


# ======================================================
# FACTOR EXTRACTION (SIMPLE + SAFE)
# ======================================================

def _extract_factors(features: Dict) -> List[str]:
    """
    Extract contributing factors based on positive/high-risk inputs.
    """

    risk_factors = []

    for key, value in features.items():
        if key == "GENDER":
            continue

        try:
            val = float(value)
            if val >= 2:  # dataset uses 1/2 scale often
                risk_factors.append(key)
        except:
            continue

    return risk_factors[:5]  # limit size


# ======================================================
# MAIN INFERENCE FUNCTION
# ======================================================

def predict_lung_risk(features: Dict) -> Dict:
    """
    Input:
        features: dict with patient attributes

    Output:
        {
            "risk_level": str,
            "confidence": float,
            "factors": List[str]
        }
    """

    if not isinstance(features, dict):
        raise ValueError("Input must be a dictionary")

    # --------------------------------------------------
    # NORMALIZE + FILL MISSING
    # --------------------------------------------------

    normalized = {}

    for feature in EXPECTED_FEATURES:
        if feature in features:
            value = features[feature]

            # 🔥 TYPE SAFETY
            if feature != "GENDER":
                try:
                    value = float(value)
                except:
                    value = 0

            normalized[feature] = value

        else:
            # Safe defaults
            if feature == "GENDER":
                normalized[feature] = "M"
            else:
                normalized[feature] = 0

    # --------------------------------------------------
    # NORMALIZE GENDER
    # --------------------------------------------------

    gender = str(normalized["GENDER"]).upper()

    if gender in ["MALE", "M", "1"]:
        normalized["GENDER"] = "M"
    elif gender in ["FEMALE", "F", "0"]:
        normalized["GENDER"] = "F"
    else:
        normalized["GENDER"] = "M"

    # --------------------------------------------------
    # DATAFRAME (ORDER SAFE)
    # --------------------------------------------------

    df = pd.DataFrame([normalized])[EXPECTED_FEATURES]

    # --------------------------------------------------
    # PREDICTION
    # --------------------------------------------------

    probs = pipeline.predict_proba(df)[0]

    # class 1 = cancer
    confidence = float(probs[1])

    # --------------------------------------------------
    # RISK LEVEL
    # --------------------------------------------------

    risk_level = _calculate_risk(confidence)

    # --------------------------------------------------
    # FACTORS
    # --------------------------------------------------

    factors = _extract_factors(normalized)

    # --------------------------------------------------
    # FINAL RESPONSE
    # --------------------------------------------------

    return {
        "risk_level": risk_level,
        "confidence": round(confidence, 4),
        "factors": factors
    }