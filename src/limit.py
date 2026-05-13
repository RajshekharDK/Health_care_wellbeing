"""
HWELBEING — RATE LIMITING SYSTEM (HYBRID SAFE)

Purpose:
- Use Redis if configured
- Fallback to in-memory limiter if not
- Prevent app crash
"""

from slowapi import Limiter
from slowapi.util import get_remote_address

from src.config import settings
from src.core.logger import get_logger

logger = get_logger(__name__)


# =========================================================
# CREATE LIMITER (SAFE)
# =========================================================
def create_limiter():
    try:
        redis_url = getattr(settings, "REDIS_URL", None)

        if redis_url:
            logger.info("Rate limiter using REDIS backend")

            return Limiter(
                key_func=get_remote_address,
                storage_uri=redis_url,
                default_limits=["60/minute"]
            )

    except Exception as e:
        logger.warning(
            "Redis limiter failed, falling back to memory",
            extra={"error": str(e)}
        )

    # 🔥 FALLBACK (NO REDIS)
    logger.info("Rate limiter using MEMORY backend")

    return Limiter(
        key_func=get_remote_address,
        default_limits=["60/minute"]
    )


# =========================================================
# GLOBAL LIMITER
# =========================================================
limiter = create_limiter()


# =========================================================
# LIMIT TIERS
# =========================================================

GENERAL_LIMIT = "60/minute"
ML_LIMIT = "20/minute"
LLM_LIMIT = "10/minute"