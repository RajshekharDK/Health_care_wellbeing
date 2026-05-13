"""
HWELBEING — SYMPTOM GRAPH (MULTILINGUAL + SMART FOLLOWUPS)
"""

from typing import List
import random


SYMPTOM_GRAPH = {

    "fever": {
        "en": [
            "Do you have chills?",
            "Do you feel body pain?",
            "How high is your fever?",
            "Do you feel weak or fatigued?"
        ],
        "hi": [
            "क्या आपको ठंड लग रही है?",
            "क्या आपको बदन दर्द है?",
            "आपका बुखार कितना है?",
            "क्या आपको कमजोरी लग रही है?"
        ],
        "kn": [
            "ನಿಮಗೆ ಚಳಿ ಆಗುತ್ತಿದೆಯೆ?",
            "ನಿಮಗೆ ದೇಹ ನೋವು ಇದೆಯೆ?",
            "ನಿಮ್ಮ ಜ್ವರ ಎಷ್ಟು ಇದೆ?",
            "ನೀವು ದುರ್ಬಲವಾಗಿ ಅನುಭವಿಸುತ್ತೀರಾ?"
        ]
    },

    "cough": {
        "en": [
            "Is the cough dry or with mucus?",
            "Do you feel chest tightness?",
            "Do you have shortness of breath?"
        ],
        "hi": [
            "क्या खांसी सूखी है या बलगम के साथ?",
            "क्या आपको सीने में जकड़न है?",
            "क्या आपको सांस लेने में दिक्कत है?"
        ],
        "kn": [
            "ಕೆಮ್ಮು ಒಣವಾಗಿದೆಯಾ ಅಥವಾ ಕಫದೊಂದಿಗೆ ಇದೆಯಾ?",
            "ನಿಮಗೆ ಎದೆ ಬಿಗಿತವಾಗಿದೆಯೆ?",
            "ನಿಮಗೆ ಉಸಿರಾಟ ತೊಂದರೆ ಇದೆಯೆ?"
        ]
    },

    "headache": {
        "en": [
            "Is the headache severe?",
            "Do you feel nausea?",
            "Do you have sensitivity to light?"
        ],
        "hi": [
            "क्या सिरदर्द बहुत तेज है?",
            "क्या आपको मतली हो रही है?",
            "क्या आपको रोशनी से परेशानी है?"
        ],
        "kn": [
            "ತಲೆನೋವು ತುಂಬಾ ತೀವ್ರವಾಗಿದೆಯೆ?",
            "ನಿಮಗೆ ವಾಂತಿ ಭಾವನೆ ಇದೆಯೆ?",
            "ಬೆಳಕಿಗೆ ಸಂವೇದನೆ ಇದೆಯೆ?"
        ]
    },

    "fatigue": {
        "en": [
            "Do you feel weakness?",
            "Do you have difficulty concentrating?"
        ],
        "hi": [
            "क्या आपको कमजोरी महसूस हो रही है?",
            "क्या आपको ध्यान केंद्रित करने में कठिनाई है?"
        ],
        "kn": [
            "ನಿಮಗೆ ದುರ್ಬಲತೆ ಅನುಭವವಾಗುತ್ತಿದೆಯೆ?",
            "ನಿಮಗೆ ಗಮನ ಕೇಂದ್ರೀಕರಿಸಲು ಕಷ್ಟವಾಗುತ್ತಿದೆಯೆ?"
        ]
    }
}


# ======================================================
# GET FOLLOW-UP QUESTIONS (SMART + MULTI)
# ======================================================
def get_followup_questions(symptoms: List[str], language: str = "en") -> List[str]:
    """
    Returns smart, non-repetitive follow-up questions.
    """

    questions = []

    for symptom in symptoms:
        if symptom in SYMPTOM_GRAPH:
            lang_block = SYMPTOM_GRAPH[symptom].get(language, [])
            questions.extend(lang_block)

    # remove duplicates
    questions = list(dict.fromkeys(questions))

    # 🔥 randomize slightly for natural feel
    random.shuffle(questions)

    # return only top 2 for clean UX
    return questions[:2]