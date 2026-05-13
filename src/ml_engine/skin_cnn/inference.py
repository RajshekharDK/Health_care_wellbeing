"""
HWELBEING — SKIN CNN INFERENCE (PRODUCTION HARDENED)

Purpose:
- Predict skin condition from image
- Apply calibration + safety checks

Exports To:
- skin_service
"""

import os
import json
import numpy as np
import tensorflow as tf
from PIL import Image
from typing import Dict


# =====================================================
# PATHS
# =====================================================

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(CURRENT_DIR, "skin_model")
CLASSES_PATH = os.path.join(CURRENT_DIR, "skin_classes.json")


# =====================================================
# LOAD MODEL
# =====================================================

_model = tf.saved_model.load(MODEL_PATH)
infer = _model.signatures["serving_default"]

with open(CLASSES_PATH, "r") as f:
    class_data = json.load(f)

    if isinstance(class_data, dict):
        CLASS_NAMES = {v: k for k, v in class_data.items()}
    else:
        CLASS_NAMES = {i: v for i, v in enumerate(class_data)}


# =====================================================
# CONFIG
# =====================================================

IMG_SIZE = 224
MIN_CONFIDENCE = 0.35      # 🔥 reject weak predictions
AMBIGUITY_GAP = 0.08      # 🔥 top1 vs top2 difference
TEMPERATURE = 1.2         # 🔥 soften overconfidence


# =====================================================
# LABEL NORMALIZATION
# =====================================================

DISEASE_MAPPING = {
    "acne_vulgaris": "Acne",
    "eczema": "Eczema",
    "psoriasis": "Psoriasis",
    "melanoma": "Skin Cancer Risk",
    "basal_cell_carcinoma": "Skin Cancer Risk",
    "squamous_cell_carcinoma": "Skin Cancer Risk",
}


def _normalize_label(label: str) -> str:
    label = label.lower()
    if label in DISEASE_MAPPING:
        return DISEASE_MAPPING[label]
    return label.replace("_", " ").title()


# =====================================================
# PREPROCESS (UNCHANGED)
# =====================================================

def _preprocess_image(image_path: str):
    try:
        img = Image.open(image_path).convert("RGB")
        img = img.resize((IMG_SIZE, IMG_SIZE))
        img = np.array(img) / 255.0
        img = np.expand_dims(img, axis=0).astype(np.float32)
        return img
    except Exception:
        return None


# =====================================================
# SOFTMAX CALIBRATION
# =====================================================

def _apply_temperature(preds: np.ndarray) -> np.ndarray:
    preds = np.power(preds, 1 / TEMPERATURE)
    preds = preds / np.sum(preds)
    return preds


# =====================================================
# SEVERITY LOGIC (IMPROVED)
# =====================================================

def _calculate_severity(confidence: float) -> str:
    if confidence < 0.5:
        return "mild"
    elif confidence < 0.75:
        return "moderate"
    else:
        return "severe"


# =====================================================
# MAIN FUNCTION
# =====================================================

def predict_skin_condition(image_path: str) -> Dict:

    img = _preprocess_image(image_path)

    if img is None:
        return {
            "condition": "Unknown",
            "confidence": 0.0,
            "severity": "unknown"
        }

    tensor = tf.constant(img, dtype=tf.float32)
    outputs = infer(tensor)
    preds = list(outputs.values())[0].numpy()[0]

    # 🔥 APPLY CALIBRATION
    preds = _apply_temperature(preds)

    # ----------------------------
    # TOP 2 CHECK
    # ----------------------------
    top_indices = np.argsort(preds)[::-1]
    top1, top2 = top_indices[0], top_indices[1]

    conf1 = float(preds[top1])
    conf2 = float(preds[top2])

    # ----------------------------
    # LOW CONFIDENCE
    # ----------------------------
    if conf1 < MIN_CONFIDENCE:
        return {
            "condition": "Uncertain",
            "confidence": conf1,
            "severity": "unknown"
        }

    # ----------------------------
    # AMBIGUITY DETECTION
    # ----------------------------
    if abs(conf1 - conf2) < AMBIGUITY_GAP:
        return {
            "condition": "Uncertain",
            "confidence": conf1,
            "severity": "unknown"
        }

    # ----------------------------
    # FINAL RESULT
    # ----------------------------
    raw_label = CLASS_NAMES.get(top1, "unknown")
    condition = _normalize_label(raw_label)
    severity = _calculate_severity(conf1)

    return {
        "condition": condition,
        "confidence": round(conf1, 4),
        "severity": severity
    }