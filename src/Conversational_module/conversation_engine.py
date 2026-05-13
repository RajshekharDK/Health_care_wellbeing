"""
HWELBEING — CONVERSATION ENGINE (SESSION ONLY)
"""

import uuid
from typing import Dict, Any


class ConversationEngine:

    def __init__(self):
        self.sessions: Dict[str, Dict[str, Any]] = {}

    def start_session(self) -> Dict[str, str]:
        session_id = str(uuid.uuid4())

        self.sessions[session_id] = {
            "history": [],
            "language": "en"
        }

        return {
            "session_id": session_id,
            "message": "Hello 👋 I'm your AI health assistant. Please describe your symptoms."
        }

    def get_history(self, session_id):
        return self.sessions.get(session_id, {}).get("history", [])

    def update_history(self, session_id, role, content):
        if session_id in self.sessions:
            self.sessions[session_id]["history"].append({
                "role": role,
                "content": content
            })