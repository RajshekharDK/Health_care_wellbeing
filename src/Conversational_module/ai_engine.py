"""
HWELBEING — AI CONVERSATION ENGINE (CLINICAL TRIAGE SAFE)

Purpose:
Clinical, deterministic conversational layer for symptom collection.
Removes generic chatbot behavior.
"""

import json
import asyncio
from typing import List, Dict, Any

import httpx

from src.config import settings
from src.core.logger import get_logger

logger = get_logger(__name__)

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL = "llama-3.3-70b-versatile"


# ======================================================
# LANGUAGE DETECTION
# ======================================================
def detect_language(text: str) -> str:
    t = text.lower()

    if any(w in t for w in ["hai", "kya", "mujhe"]):
        return "hi"

    if any(w in t for w in ["nanage", "ide", "jwara"]):
        return "kn"

    return "en"


# ======================================================
# CLEAN INPUT
# ======================================================
def clean_input(text: str) -> str:
    return text.replace("uh", "").replace("um", "").strip()


# ======================================================
# 🔥 CLINICAL SYSTEM PROMPT (FIXED)
# ======================================================
def build_system_prompt(language: str) -> str:
    return f"""
You are a clinical triage assistant.

STRICT RULES:
- ONLY focus on symptoms and health
- DO NOT act like a general chatbot
- DO NOT generate emotional or psychological responses
- DO NOT say things like "are you okay" or "what’s going on"
- DO NOT assume feelings

FLOW:
1. Extract symptoms clearly
2. Ask for missing important symptoms (max 1 question)
3. If user says "no", "nothing", "that's all":
   → STOP asking questions
   → Summarize symptoms
   → Proceed to possible condition hint

OUTPUT STYLE:
- Short
- Clinical
- Direct

Reply ONLY in {language}
"""


# ======================================================
# SIMPLE CONTROL LOGIC (CRITICAL FIX)
# ======================================================
def is_conversation_end(text: str) -> bool:
    t = text.lower()
    return any(x in t for x in ["no", "nothing", "that's all", "no more"])


def extract_basic_symptoms(text: str) -> List[str]:
    symptoms = []
    t = text.lower()

    keywords = [
        "fever", "cold", "cough", "headache", "pain",
        "vomiting", "fatigue", "sore throat", "body ache"
    ]

    for k in keywords:
        if k in t:
            symptoms.append(k)

    return symptoms


# ======================================================
# STREAMING MODE (FIXED LOGIC)
# ======================================================
async def ai_conversation_stream(
    user_message: str,
    history: List[Dict]
):
    user_message = clean_input(user_message)

    # 🔥 RULE: if user says "no" → STOP chatbot mode
    if is_conversation_end(user_message):

        # collect symptoms from history
        collected = []
        for h in history:
            if h["role"] == "user":
                collected += extract_basic_symptoms(h["content"])

        collected += extract_basic_symptoms(user_message)

        collected = list(set(collected))

        summary = ", ".join(collected) if collected else "your symptoms"

        final = f"""
Based on the symptoms reported ({summary}),
you may have a common infection or flu.

I recommend:
- rest
- hydration
- consult a doctor if symptoms worsen
"""

        for word in final.split():
            yield word + " "
            await asyncio.sleep(0.02)

        return

    # 🔥 NORMAL FLOW (controlled)
    language = detect_language(user_message)
    system_prompt = build_system_prompt(language)

    messages = [{"role": "system", "content": system_prompt}] + history
    messages.append({"role": "user", "content": user_message})

    headers = {
        "Authorization": f"Bearer {settings.GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": GROQ_MODEL,
        "messages": messages,
        "temperature": 0.2,
        "stream": True,
        "max_tokens": 120
    }

    async with httpx.AsyncClient(timeout=None) as client:
        async with client.stream("POST", GROQ_URL, headers=headers, json=payload) as res:
            async for line in res.aiter_lines():

                if not line or "data:" not in line:
                    continue

                chunk = line.replace("data:", "").strip()

                if chunk == "[DONE]":
                    break

                try:
                    data = json.loads(chunk)
                    delta = data["choices"][0]["delta"].get("content")

                    if delta:
                        yield delta

                except Exception:
                    continue