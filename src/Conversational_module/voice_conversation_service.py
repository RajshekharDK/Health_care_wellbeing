"""
HWELBEING — VOICE CONVERSATION SERVICE (CHATGPT-LIKE REALTIME)
"""

from typing import Optional, Dict, Any
import asyncio

from src.Conversational_module.ai_engine import ai_conversation
from src.Conversational_module.tts_service import generate_tts
from src.core.logger import get_logger

logger = get_logger(__name__)


# ==========================================================
# SAFE RESPONSE
# ==========================================================
def _safe_response(session_id, message, language):
    return {
        "session_id": session_id,
        "transcript": message,
        "response_text": "I couldn't understand clearly. Please say that again.",
        "audio_b64": None,
        "language": language,
        "confidence": 0.3,
        "complete": False
    }


# ==========================================================
# MEMORY (SESSION CHAT)
# ==========================================================
SESSION_MEMORY = {}


# ==========================================================
# MAIN ENTRY
# ==========================================================
async def run_voice_conversation(
    message: str,
    session_id: Optional[str] = None,
    language: Optional[str] = "en",
    location: Optional[Dict[str, float]] = None,
    request_id: Optional[str] = None
) -> Dict[str, Any]:

    if not message or not message.strip():
        return _safe_response(session_id, "", language)

    message = message.strip()

    # =========================
    # SESSION INIT
    # =========================
    if not session_id:
        session_id = str(hash(message))  # simple fallback

    if session_id not in SESSION_MEMORY:
        SESSION_MEMORY[session_id] = []

    history = SESSION_MEMORY[session_id]

    try:
        # =========================
        # 🔥 AI (CORE BRAIN)
        # =========================
        ai_data = await asyncio.wait_for(
            ai_conversation(
                user_message=message,
                history=history,
                language=language
            ),
            timeout=15
        )

    except Exception as e:
        logger.error("AI_FAIL", extra={"error": str(e)})
        return _safe_response(session_id, message, language)

    # =========================
    # EXTRACT
    # =========================
    reply = ai_data.get("reply", "").strip()
    confidence = float(ai_data.get("confidence", 0.5))

    if not reply:
        reply = "I didn't fully understand. Could you repeat that?"

    # =========================
    # STORE MEMORY
    # =========================
    history.append({"role": "user", "content": message})
    history.append({"role": "assistant", "content": reply})

    # limit memory
    if len(history) > 10:
        history[:] = history[-10:]

    # =========================
    # TTS
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
    # RESPONSE
    # =========================
    return {
        "session_id": session_id,
        "transcript": message,
        "response_text": reply,
        "audio_b64": audio_b64,
        "language": language,
        "confidence": confidence,
        "complete": False
    }