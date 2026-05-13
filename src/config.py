"""
src/config.py

Purpose:
--------
Centralized application configuration loader.
"""

import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    # -----------------------------
    # SAP HANA CONFIG
    # -----------------------------
    HANA_HOST: str = os.getenv("HANA_HOST")
    HANA_PORT: int = int(os.getenv("HANA_PORT", 443))
    HANA_USER: str = os.getenv("HANA_USER")
    HANA_PASSWORD: str = os.getenv("HANA_PASSWORD")
    HANA_SCHEMA: str = os.getenv("HANA_SCHEMA", "HWELLBEING")

    # -----------------------------
    # DB POOL
    # -----------------------------
    DB_POOL_SIZE: int = int(os.getenv("DB_POOL_SIZE", 5))

    # -----------------------------
    # CORS (FIXED)
    # -----------------------------
    ALLOWED_ORIGINS: list = os.getenv(
        "ALLOWED_ORIGINS",
        "http://localhost:5173"
    ).split(",")

    # -----------------------------
    # API KEYS
    # -----------------------------
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY")
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY")

    # -----------------------------
    # JWT CONFIG (FIXED)
    # -----------------------------
    SECRET_KEY: str = os.getenv("JWT_SECRET_KEY")  # 🔥 FIX
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(
        os.getenv("JWT_EXPIRE_MINUTES", 60)
    )

    # -----------------------------
    # OPTIONAL REDIS
    # -----------------------------
    REDIS_URL: str | None = os.getenv("REDIS_URL", None)

    # -----------------------------
    # MODEL / LOGIC CONFIG
    # -----------------------------
    CONFIDENCE_THRESHOLD: float = float(
        os.getenv("CONFIDENCE_THRESHOLD", 0.05)
    )

    SKIN_CONFIDENCE_THRESHOLD: float = 0.4
    SKIN_TREATMENT_THRESHOLD: float = 0.5

    MAX_CONDITIONS: int = 3

    # -----------------------------
    # VALIDATION
    # -----------------------------
    def validate(self):
        missing = []

        # DB required
        if not self.HANA_HOST:
            missing.append("HANA_HOST")
        if not self.HANA_USER:
            missing.append("HANA_USER")
        if not self.HANA_PASSWORD:
            missing.append("HANA_PASSWORD")

        # JWT required
        if not self.SECRET_KEY:
            missing.append("JWT_SECRET_KEY")

        if missing:
            raise ValueError(f"Missing required config: {', '.join(missing)}")


# Singleton
settings = Settings()
settings.validate()
print("LOADED SECRET KEY:", settings.SECRET_KEY)