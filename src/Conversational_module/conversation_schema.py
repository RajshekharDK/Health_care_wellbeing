"""
HWELBEING — CONVERSATION SCHEMA (FINAL PRODUCTION)

Purpose:
Defines request/response models for chat + voice + streaming.

Rules:
- ONLY "confidence"
- audio = base64
- streaming-safe contracts
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict


# ======================================================
# START CONVERSATION
# ======================================================
class StartConversationResponse(BaseModel):
    session_id: str
    message: str


# ======================================================
# LOCATION
# ======================================================
class Location(BaseModel):
    lat: float = Field(..., ge=-90, le=90)
    lon: float = Field(..., ge=-180, le=180)


# ======================================================
# USER MESSAGE
# ======================================================
class ConversationMessage(BaseModel):
    session_id: str
    message: str
    location: Optional[Location] = None


# ======================================================
# DOCTOR
# ======================================================
class Doctor(BaseModel):
    name: str
    distance: str
    type: str
    lat: float
    lon: float


# ======================================================
# TRIAGE RESULT (FIXED 🔥)
# ======================================================
class TriageResult(BaseModel):
    disease: str
    confidence: float = Field(..., ge=0.0, le=1.0)
    explanation: str


# ======================================================
# BASE RESPONSE
# ======================================================
class BaseConversationResponse(BaseModel):
    reply: str
    confidence: float = Field(..., ge=0.0, le=1.0)
    complete: bool
    audio_b64: Optional[str] = None
    doctors: List[Doctor] = Field(default_factory=list)
    triage: Optional[List[TriageResult]] = None  # 🔥 FIX


# ======================================================
# CHAT RESPONSE
# ======================================================
class ConversationResponse(BaseConversationResponse):
    pass


# ======================================================
# VOICE (HTTP FALLBACK)
# ======================================================
class VoiceResponse(BaseModel):
    session_id: str
    transcript: str
    response_text: str
    audio_b64: Optional[str] = None
    language: str
    confidence: float = Field(..., ge=0.0, le=1.0)
    complete: bool  # 🔥 ADDED


# ======================================================
# WEBSOCKET MESSAGE TYPES (STREAMING)
# ======================================================
class WSMessage(BaseModel):
    type: str


class WSTranscript(WSMessage):
    type: str = "transcript"
    text: str


class WSResponseText(WSMessage):
    type: str = "response_text"
    text: str


class WSAudio(WSMessage):
    type: str = "audio"
    audio_b64: str


# 🔥 NEW — error handling
class WSError(WSMessage):
    type: str = "error"
    message: str


# 🔥 NEW — stream end signal
class WSEnd(WSMessage):
    type: str = "end"


# ======================================================
# PREDICTION REQUEST
# ======================================================
class ConversationPredict(BaseModel):
    session_id: str


# ======================================================
# PREDICTION RESPONSE
# ======================================================
class ConversationPredictionResponse(BaseModel):
    possible_conditions: List[dict]
    confidence: float = Field(..., ge=0.0, le=1.0)
    treatment_guidance: List[dict]
    health_report: Optional[str] = None
    note: str