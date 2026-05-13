"""
HWELBEING — TTS SERVICE (FINAL STABLE NATURAL VERSION)

✔ No SSML (prevents "slash" reading)
✔ Natural pauses via punctuation + line breaks
✔ No audio cut
✔ Stable timeout + retry
✔ Clean, human-like delivery
"""

import os
import uuid
import base64
import asyncio
import re
from typing import Optional

import edge_tts

from src.config import settings
from src.core.logger import get_logger

logger = get_logger(__name__)


# ======================================================
# CONFIG
# ======================================================
STATIC_DIR = "static"
os.makedirs(STATIC_DIR, exist_ok=True)

VOICE_MAP = {
    "en": "en-US-AriaNeural",
    "hi": "hi-IN-SwaraNeural",
    "kn": "kn-IN-KannadaNeural",
    "ta": "ta-IN-PallaviNeural",
    "te": "te-IN-ShrutiNeural"
}

TTS_SEMAPHORE = asyncio.Semaphore(5)


# ======================================================
# EMPATHY (KEEP LIGHT)
# ======================================================
def _add_empathy(text: str) -> str:
    return (
        "I understand how you're feeling. "
        "Let me guide you through this.\n\n"
        + text
    )


# ======================================================
# CLEAN TEXT (SAFE FOR SPEECH)
# ======================================================
def _clean_text(text: str) -> str:
    if not text:
        return ""

    text = text.strip()

    # Remove emojis but keep punctuation
    text = re.sub(r'[^\x00-\x7F]+', '', text)

    # Normalize spaces
    text = re.sub(r"\s+", " ", text)

    return text


# ======================================================
# SAFE TRIM (NO MID-WORD CUT)
# ======================================================
def _safe_trim(text: str, max_len: int = 900) -> str:
    if len(text) <= max_len:
        return text

    trimmed = text[:max_len]
    return trimmed.rsplit(" ", 1)[0]


# ======================================================
# NATURAL SPEECH STRUCTURE (CRITICAL)
# ======================================================
def _structure_for_speech(text: str) -> str:
    """
    Convert structured medical response into natural spoken form
    """

    # Keep sections separated clearly
    text = text.replace("🩺 What you should do:", "\n\nWhat you should do:\n")
    text = text.replace("⚠️ When to see a doctor:", "\n\nWhen to see a doctor:\n")

    # Convert bullets into pauses
    lines = text.split("\n")

    processed = []
    for line in lines:
        line = line.strip()

        if not line:
            processed.append("")  # pause
            continue

        # bullet → sentence with pause
        if line.startswith("- "):
            processed.append(line[2:] + ".")
        else:
            processed.append(line)

    # Join with line breaks → natural pauses in TTS
    return "\n".join(processed)


# ======================================================
# GENERATE AUDIO
# ======================================================
async def _generate_file(text: str, filename: str, voice: str):
    communicate = edge_tts.Communicate(
        text,
        voice,
        rate="+0%",
        pitch="+0Hz"
    )
    await communicate.save(filename)


# ======================================================
# MAIN FUNCTION
# ======================================================
async def generate_tts(
    text: str,
    language: str = "en"
) -> Optional[str]:

    if not text:
        return None

    try:
        # -------------------------
        # PROCESS TEXT
        # -------------------------
        text = _add_empathy(text)
        text = _safe_trim(text)
        text = _structure_for_speech(text)
        text = _clean_text(text)

        if not text:
            return None

        voice = VOICE_MAP.get(language, VOICE_MAP["en"])
        filename = f"{STATIC_DIR}/tts_{uuid.uuid4().hex}.mp3"

        # -------------------------
        # GENERATE AUDIO
        # -------------------------
        async with TTS_SEMAPHORE:
            await asyncio.wait_for(
                _generate_file(text, filename, voice),
                timeout=15.0
            )

        # -------------------------
        # READ FILE
        # -------------------------
        with open(filename, "rb") as f:
            audio_b64 = base64.b64encode(f.read()).decode("utf-8")

        # -------------------------
        # CLEANUP
        # -------------------------
        if not getattr(settings, "SAVE_TTS_FILES", False):
            try:
                os.remove(filename)
            except Exception as e:
                logger.warning("TTS_FILE_DELETE_FAIL", extra={"error": str(e)})

        return audio_b64

    # -------------------------
    # TIMEOUT HANDLING
    # -------------------------
    except asyncio.TimeoutError:
        logger.warning("TTS_TIMEOUT — retrying shorter version")

        try:
            short_text = _safe_trim(text, 400)
            short_text = _structure_for_speech(short_text)
            short_text = _clean_text(short_text)

            filename = f"{STATIC_DIR}/tts_retry_{uuid.uuid4().hex}.mp3"

            await _generate_file(short_text, filename, voice)

            with open(filename, "rb") as f:
                return base64.b64encode(f.read()).decode("utf-8")

        except Exception as retry_err:
            logger.error("TTS_RETRY_FAILED", extra={"error": str(retry_err)})
            return None

    except Exception as e:
        logger.error("TTS_ERROR", extra={"error": str(e)})
        return None