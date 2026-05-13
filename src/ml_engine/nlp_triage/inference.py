"""
HWELBEING — NLP TRIAGE INFERENCE (PRODUCTION HARDENED)

Purpose:
- Symptom text → disease prediction
- Clean, filter, normalize ML outputs

Exports To:
- triage_service
"""

import os
import re
import joblib
import numpy as np
from typing import List, Dict

from sentence_transformers import SentenceTransformer


# =========================================================
# PATHS
# =========================================================
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PIPELINE_PATH = os.path.join(CURRENT_DIR, "pipeline.pkl")
ENCODER_PATH = os.path.join(CURRENT_DIR, "label_encoder.pkl")


# =========================================================
# LOAD MODELS
# =========================================================
_pipeline = joblib.load(PIPELINE_PATH)
classifier = _pipeline["classifier"]

label_encoder = joblib.load(ENCODER_PATH)
embedder = SentenceTransformer("all-MiniLM-L6-v2")


# =========================================================
# CONFIG (IMPORTANT)
# =========================================================
MIN_CONFIDENCE = 0.05     # 🔥 filter weak predictions
TOP_K = 5
TEMPERATURE = 0.7        # 🔥 sharpening


# =========================================================
# NORMALIZATION
# =========================================================
SYMPTOM_NORMALIZATION = {
    "feverish": "fever",
    "stomach ache": "stomach pain",
    "belly pain": "stomach pain",
    "head hurts": "headache",
    "throwing up": "vomiting",
    "loose motion": "diarrhea",
    "blocked nose": "cold"
}


# =========================================================
# TEXT PROCESSING
# =========================================================
def _clean_text(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^\w\s]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()[:300]


def _normalize_text(text: str) -> str:
    for k, v in SYMPTOM_NORMALIZATION.items():
        text = text.replace(k, v)
    return text


def _enhance_symptoms(text: str) -> str:
    """
    🔥 Key improvement: emphasize symptoms
    """
    words = text.split()
    return " ".join(words + words)  # duplicate signal


# =========================================================
# FEATURES
# =========================================================
def _extract_features(text: str) -> np.ndarray:
    words = text.split()

    symptom_count = len(words)

    severity_score = 0
    if "severe" in text or "high" in text:
        severity_score = 3
    elif "moderate" in text:
        severity_score = 2
    elif "mild" in text:
        severity_score = 1

    critical_keywords = [
        "chest pain",
        "shortness of breath",
        "fainting",
        "breathing problem"
    ]

    has_critical = int(any(k in text for k in critical_keywords))

    return np.array([[symptom_count, severity_score, has_critical]])


# =========================================================
# SOFTMAX SHARPENING
# =========================================================
def _apply_temperature(probs: np.ndarray) -> np.ndarray:
    probs = np.power(probs, 1 / TEMPERATURE)
    probs = probs / np.sum(probs)
    return probs


# =========================================================
# MAIN FUNCTION
# =========================================================
def predict_nlp_triage(symptom_text: str) -> Dict:

    if not symptom_text or not symptom_text.strip():
        return {"possible_conditions": []}

    # CLEAN
    text = _clean_text(symptom_text)
    text = _normalize_text(text)
    text = _enhance_symptoms(text)

    if not text:
        return {"possible_conditions": []}

    # EMBEDDING
    embedding = embedder.encode([text], normalize_embeddings=True)

    # FEATURES
    features = _extract_features(text)
    X = np.hstack([embedding, features])

    # PREDICT
    probs = classifier.predict_proba(X)[0]

    # 🔥 APPLY SHARPENING
    probs = _apply_temperature(probs)

    results: List[Dict] = []

    for idx, prob in enumerate(probs):
        if prob < MIN_CONFIDENCE:
            continue

        disease = label_encoder.inverse_transform([idx])[0]

        results.append({
            "disease": disease,
            "confidence": float(prob)
        })

    # SORT
    results.sort(key=lambda x: x["confidence"], reverse=True)

    # LIMIT
    results = results[:TOP_K]

    return {
        "possible_conditions": results
    }