"""
HWELBEING — REALTIME VOICE WEBSOCKET (FINAL POLISHED VERSION)
"""

import base64
import asyncio
import uuid
import os
import json
import subprocess
import re

from fastapi import WebSocket, WebSocketDisconnect, status
from jose import jwt, JWTError
import whisper

from src.config import settings
from src.core.logger import get_logger

from src.decision.decision_engine import run_decision_engine
from src.ml_engine.nlp_triage.inference import predict_nlp_triage
from src.Conversational_module.ai_engine import ai_conversation_stream
from src.Conversational_module.tts_service import generate_tts

logger = get_logger(__name__)

TEMP_DIR = "temp_audio"
os.makedirs(TEMP_DIR, exist_ok=True)

ALGORITHM = "HS256"
_whisper_model = None


# =========================
# EXECUTOR
# =========================
async def _run(fn, *args):
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, fn, *args)


# =========================
# WHISPER
# =========================
def get_whisper():
    global _whisper_model
    if _whisper_model is None:
        _whisper_model = whisper.load_model("small")
    return _whisper_model


# =========================
# JWT VERIFY
# =========================
def _verify_ws_token(token: str):
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        return payload.get("sub")
    except JWTError as e:
        logger.error("WS_TOKEN_ERROR", extra={"error": str(e)})
        return None


# =========================
# FILE OPS
# =========================
def _save_file(path, content):
    with open(path, "wb") as f:
        f.write(content)


def _convert(input_path, output_path):
    subprocess.run(
        ["ffmpeg", "-y", "-i", input_path, "-ar", "16000", "-ac", "1", output_path],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=True
    )


def _transcribe(path):
    return get_whisper().transcribe(path).get("text", "").strip()


# =========================
# CLEAN TRANSCRIPT
# =========================
def _clean_transcript(text: str) -> str:
    text = text.lower()

    garbage = ["dollars", "uh", "um"]
    for g in garbage:
        text = text.replace(g, "")

    corrections = {
        "torus": "throat",
        "todays": "today",
        "body pain": "body ache"
    }

    for k, v in corrections.items():
        text = text.replace(k, v)

    return text.strip()


# =========================
# CLEAN FOR TTS
# =========================
def _clean_for_tts(text: str) -> str:
    return re.sub(r'[^\x00-\x7F]+', '', text)


# =========================
# EXTRACT SYMPTOMS (FIXED)
# =========================
def extract_symptoms(text: str):
    keywords = [
        "fever",
        "cold",
        "cough",
        "headache",
        "fatigue",
        "vomiting",
        "diarrhea",
        "stomach pain",
        "body ache",
        "chest pain",
        "breathing",
        "dizziness"
    ]

    found = []
    text = text.lower()

    for k in keywords:
        if k in text:
            found.append(k)

    return list(set(found))


# =========================
# COLLECT USER TEXT
# =========================
def extract_medical_text(history):
    return " ".join([h["content"] for h in history if h["role"] == "user"])


# =========================
# RESPONSE BUILDER (FINAL)
# =========================
def build_doctor_response(decision_output, symptoms_text: str):

    top = decision_output[0]
    disease = top.get("disease", "a possible condition")
    risk = top.get("risk", "low")

    symptoms = extract_symptoms(symptoms_text)

    if symptoms:
        if len(symptoms) == 1:
            symptoms_sentence = symptoms[0]
        else:
            symptoms_sentence = ", ".join(symptoms[:-1]) + f" and {symptoms[-1]}"
    else:
        symptoms_sentence = symptoms_text

    intro = f"Based on your symptoms, you may have {disease}."

    explanation = (
        f"You've been experiencing {symptoms_sentence}, which may be related to "
        f"{disease.lower()} or a similar condition."
    )

    # -------- Advice --------
    advice = []

    if "fever" in symptoms:
        advice.append("Take paracetamol if your fever is high")

    if "cough" in symptoms:
        advice.append("Drink warm fluids and try steam inhalation")

    if "diarrhea" in symptoms:
        advice.append("Use ORS and stay hydrated")

    if "pain" in symptoms_text or "ache" in symptoms_text:
        advice.append("Take adequate rest")

    if not advice:
        advice = [
            "Stay hydrated",
            "Get proper rest",
            "Eat light food"
        ]

    advice_block = "\n".join([f"- {a}" for a in advice])

    # -------- Warning --------
    warnings = [
        "Fever lasting more than 3 days",
        "Difficulty in breathing",
        "Symptoms getting worse"
    ]

    if risk == "high":
        warnings.append("Seek immediate medical attention")

    warning_block = "\n".join([f"- {w}" for w in warnings])

    full = (
        f"{intro}\n\n"
        f"{explanation}\n\n"
        f"🩺 What you should do:\n{advice_block}\n\n"
        f"⚠️ When to see a doctor:\n{warning_block}\n\n"
        f"Monitor your condition and consult a doctor if needed."
    )

    return full


# =========================
# WS ROUTE
# =========================
def attach_ws(app):

    @app.websocket("/ws/voice")
    async def voice_ws(ws: WebSocket):

        token = ws.query_params.get("token")

        if not token or not _verify_ws_token(token):
            await ws.close(code=status.WS_1008_POLICY_VIOLATION)
            return

        await ws.accept()

        history = []

        greeting = "Hello, please tell me your symptoms."
        history.append({"role": "assistant", "content": greeting})

        audio = await generate_tts(greeting, "en")

        await ws.send_json({
            "type": "greeting",
            "text": greeting,
            "audio_b64": audio,
            "history": history
        })

        try:
            while True:

                raw = await ws.receive()
                if raw.get("type") == "websocket.disconnect":
                    break

                data = json.loads(raw.get("text"))
                audio_b64 = data.get("audio_b64")

                if not audio_b64:
                    continue

                temp_id = uuid.uuid4().hex
                input_path = f"{TEMP_DIR}/{temp_id}.webm"
                output_path = f"{TEMP_DIR}/{temp_id}.wav"

                try:
                    audio_bytes = base64.b64decode(audio_b64)

                    await _run(_save_file, input_path, audio_bytes)
                    await _run(_convert, input_path, output_path)

                    transcript = await _run(_transcribe, output_path)
                    transcript = _clean_transcript(transcript)

                except Exception as e:
                    logger.error("AUDIO_ERROR", extra={"error": str(e)})
                    continue

                finally:
                    if os.path.exists(input_path):
                        os.remove(input_path)
                    if os.path.exists(output_path):
                        os.remove(output_path)

                if not transcript:
                    continue

                history.append({"role": "user", "content": transcript})

                await ws.send_json({
                    "type": "transcript",
                    "text": transcript,
                    "history": history
                })

                full_text = extract_medical_text(history)

                try:
                    ml_output = await _run(predict_nlp_triage, full_text)
                    decision_output = await run_decision_engine(full_text.split(), ml_output)

                    if decision_output:
                        full = build_doctor_response(decision_output, full_text)
                    else:
                        full = (
                            f"Based on your symptoms, this may be a general infection.\n\n"
                            "🩺 What you should do:\n"
                            "- Stay hydrated\n"
                            "- Take rest\n\n"
                            "⚠️ When to see a doctor:\n"
                            "- Symptoms worsen\n\n"
                            "Consult a doctor if needed."
                        )

                except Exception as e:
                    logger.error("DIAGNOSIS_ERROR", extra={"error": str(e)})
                    full = "Something went wrong while analyzing symptoms."

                history.append({"role": "assistant", "content": full})

                audio = await generate_tts(full, "en")

                await ws.send_json({
                    "type": "end",
                    "text": full,
                    "audio_b64": audio,
                    "history": history
                })

        except WebSocketDisconnect:
            logger.info("WS_DISCONNECTED")