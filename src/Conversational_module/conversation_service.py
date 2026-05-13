"""
HWELBEING — CONVERSATION SERVICE (AI-FIRST + NATURAL FLOW)
"""

import asyncio
from typing import Dict, Any, Optional, List

from src.Conversational_module.ai_engine import ai_conversation
from src.decision.decision_engine import run_decision_engine
from src.ml_engine.nlp_triage.inference import predict_nlp_triage
from src.Conversational_module.tts_service import generate_tts
from src.core.logger import get_logger

logger = get_logger(__name__)


# ======================================================
# MEMORY (SESSION CONTEXT)
# ======================================================
SESSION_MEMORY: Dict[str, List[Dict]] = {}


# ======================================================
# HELPERS
# ======================================================
def _normalize_confidence(value) -> float:
    try:
        return max(0.0, min(1.0, float(value)))
    except Exception:
        return 0.0


async def _run(fn, *args):
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, fn, *args)


# ======================================================
# START SESSION
# ======================================================
async def start_conversation() -> Dict[str, Any]:
    session_id = str(asyncio.get_event_loop().time())

    SESSION_MEMORY[session_id] = []

    return {
        "session_id": session_id,
        "message": "Hello 👋 I'm your AI health assistant. How can I help you today?"
    }


# ======================================================
# PROCESS MESSAGE
# ======================================================
async def process_message(
    session_id: str,
    message: str,
    language: str = "en",
    location: Optional[Dict[str, float]] = None,
    request_id: Optional[str] = None
) -> Dict[str, Any]:

    if not message or not message.strip():
        return {
            "reply": "I couldn't understand clearly. Please say that again.",
            "confidence": 0.3,
            "complete": False,
            "triage": None,
            "audio_b64": None,
            "clinical": {"symptoms": []}
        }

    message = message.strip()

    # =========================
    # SESSION MEMORY
    # =========================
    if session_id not in SESSION_MEMORY:
        SESSION_MEMORY[session_id] = []

    history = SESSION_MEMORY[session_id]

    # =========================
    # 🧠 AI UNDERSTANDING
    # =========================
    try:
        ai_data = await asyncio.wait_for(
            ai_conversation(
                user_message=message,
                history=history,
                language=language
            ),
            timeout=12
        )
    except Exception as e:
        logger.error("AI_ERROR", extra={"error": str(e)})
        return {
            "reply": "Something went wrong. Please try again.",
            "confidence": 0.0,
            "complete": False,
            "triage": None,
            "audio_b64": None,
            "clinical": {"symptoms": []}
        }

    reply = ai_data.get("reply", "")
    symptoms: List[str] = ai_data.get("symptoms", [])
    confidence = _normalize_confidence(ai_data.get("confidence", 0.6))

    # =========================
    # SAVE MEMORY
    # =========================
    history.append({"role": "user", "content": message})
    history.append({"role": "assistant", "content": reply})

    if len(history) > 10:
        history[:] = history[-10:]

    # =========================
    # 🩺 OPTIONAL DIAGNOSIS
    # =========================
    triage = None

    if len(symptoms) >= 3:
        try:
            ml_output = await _run(
                predict_nlp_triage,
                " ".join(symptoms)
            )

            decision_results = await run_decision_engine(
                symptoms=symptoms,
                ml_output=ml_output
            )

            if decision_results:
                triage = [
                    d for d in decision_results
                    if float(d.get("confidence", 0)) >= 0.4
                ]

                if triage:
                    top = triage[0]
                    disease = top.get("disease", "a condition")
                    conf = round(top.get("confidence", 0) * 100, 1)

                    reply += f" Based on your symptoms, this may indicate {disease} ({conf}%)."

        except Exception as e:
            logger.error("TRIAGE_ERROR", extra={"error": str(e)})

    # =========================
    # 🔊 TTS
    # =========================
    audio_b64 = None

    try:
        audio_b64 = await generate_tts(
            text=reply[:300],
            language=language
        )
    except Exception:
        pass

    # =========================
    # FINAL RESPONSE
    # =========================
    return {
        "reply": reply,
        "confidence": confidence,
        "complete": False,
        "triage": triage,
        "audio_b64": audio_b64,
        "clinical": {"symptoms": symptoms}
    }