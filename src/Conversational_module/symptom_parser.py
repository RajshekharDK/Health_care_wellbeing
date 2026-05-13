"""
HWELBEING — SYMPTOM PARSER (PRODUCTION HARDENED)

Purpose:
Extract and normalize symptoms from user text and AI suggestions.

Enhancements:
- Stronger negation detection
- Phrase normalization
- Multilingual basic support
- Streaming-safe filtering
"""

import re
from typing import List


# ======================================================
# KNOWN SYMPTOMS
# ======================================================
KNOWN_SYMPTOMS = [
    "fever", "chills", "fatigue", "weakness",
    "headache", "body pain", "muscle pain", "joint pain",
    "chest pain", "abdominal pain", "stomach pain",
    "cough", "shortness of breath", "runny nose",
    "nasal congestion", "sore throat",
    "nausea", "vomiting", "diarrhea",
    "dizziness", "fainting",
    "rash", "itching",
    "palpitations", "high blood pressure"
]


# ======================================================
# SYNONYMS + PHRASES
# ======================================================
SYMPTOM_SYNONYMS = {
    "feverish": "fever",
    "high temperature": "fever",
    "tired": "fatigue",
    "breathing problem": "shortness of breath",
    "throwing up": "vomiting",
    "loose motion": "diarrhea",
    "stomach ache": "stomach pain",
    "head pain": "headache",

    # phrase normalization
    "pain in chest": "chest pain",
    "pain in stomach": "stomach pain",
    "pain in abdomen": "abdominal pain"
}


# ======================================================
# MULTILINGUAL BASIC MAP (LIGHTWEIGHT)
# ======================================================
MULTILINGUAL_MAP = {
    "bukhar": "fever",
    "khansi": "cough",
    "sar dard": "headache",
    "pet dard": "stomach pain"
}


# ======================================================
# NEGATION WORDS
# ======================================================
NEGATION_WORDS = ["no", "not", "without", "don't", "do not", "didn't"]


# ======================================================
# NORMALIZE TEXT
# ======================================================
def _normalize_text(text: str) -> str:
    text = text.lower()

    # multilingual mapping
    for k, v in MULTILINGUAL_MAP.items():
        text = re.sub(rf"\b{re.escape(k)}\b", v, text)

    # synonym mapping
    for k, v in SYMPTOM_SYNONYMS.items():
        text = re.sub(rf"\b{re.escape(k)}\b", v, text)

    return text


# ======================================================
# STRONG NEGATION CHECK
# ======================================================
def _is_negated(text: str, symptom: str) -> bool:
    window_pattern = rf"(no|not|without|don't|do not)\s+\w*\s*{re.escape(symptom)}"
    return re.search(window_pattern, text) is not None


# ======================================================
# VALIDATE AI SYMPTOMS
# ======================================================
def _validate_ai_symptoms(ai_symptoms) -> List[str]:
    if not isinstance(ai_symptoms, list):
        return []

    valid = []

    for s in ai_symptoms:
        if not isinstance(s, str):
            continue

        s = s.lower().strip()

        if s in KNOWN_SYMPTOMS:
            valid.append(s)

    return valid


# ======================================================
# MAIN FUNCTION
# ======================================================
def extract_symptoms(text: str, ai_symptoms: List[str] = None) -> List[str]:

    if not text or len(text.strip()) < 3:
        return []

    text = _normalize_text(text)

    detected = set()

    # ==================================================
    # REGEX DETECTION
    # ==================================================
    for symptom in KNOWN_SYMPTOMS:
        if re.search(rf"\b{re.escape(symptom)}\b", text):

            if not _is_negated(text, symptom):
                detected.add(symptom)

    # ==================================================
    # AI SYMPTOMS (SAFE MERGE)
    # ==================================================
    ai_valid = _validate_ai_symptoms(ai_symptoms)

    for s in ai_valid:
        if not _is_negated(text, s):
            detected.add(s)

    return sorted(detected)