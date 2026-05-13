"""
HWELBEING — SECURITY MODULE (FINAL PRODUCTION SAFE)

Purpose:
- JWT authentication
- Secure password hashing (bcrypt + SHA256)
- Request authorization (FastAPI dependency)

Features:
- Fix bcrypt 72-byte limit
- Strong input validation
- Clean 401 handling
- Token payload validation
- Structured logging
"""

from datetime import datetime, timedelta
from typing import Optional, Dict
import hashlib

from jose import JWTError, jwt
from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from passlib.context import CryptContext

from src.config import settings
from src.core.logger import get_logger, request_id_ctx

logger = get_logger(__name__)


# =========================================================
# PASSWORD HASHING (SAFE)
# =========================================================
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def _normalize_password(password: str) -> str:
    """
    Normalize password before hashing.

    - Prevent bcrypt 72-byte limit issue
    - Enforce valid input
    """
    if not isinstance(password, str):
        raise ValueError("Password must be a string")

    password = password.strip()

    if not password:
        raise ValueError("Password cannot be empty")

    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def get_password_hash(password: str) -> str:
    """
    Hash password safely (SHA256 -> bcrypt)
    """
    normalized = _normalize_password(password)
    return pwd_context.hash(normalized)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify password safely
    """
    try:
        normalized = _normalize_password(plain_password)
        return pwd_context.verify(normalized, hashed_password)
    except Exception:
        return False


# =========================================================
# JWT CONFIG
# =========================================================
ALGORITHM = "HS256"


# =========================================================
# TOKEN CREATION
# =========================================================
def create_access_token(user_id: str, role: str = "user") -> str:
    """
    Create JWT access token
    """
    now = datetime.utcnow()
    expire = now + timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )

    payload = {
        "sub": user_id,
        "role": role,
        "type": "access",
        "iat": now,   # issued at
        "exp": expire
    }

    return jwt.encode(payload, settings.SECRET_KEY, algorithm=ALGORITHM)


# =========================================================
# TOKEN VERIFICATION
# =========================================================
security = HTTPBearer(auto_error=False)


def verify_token(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Dict[str, str]:
    """
    FastAPI dependency to verify JWT token.

    Returns:
    {
        "user_id": str,
        "role": str
    }
    """

    if credentials is None:
        raise HTTPException(
            status_code=401,
            detail="Authorization header missing"
        )

    token = credentials.credentials

    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[ALGORITHM]
        )

        user_id: Optional[str] = payload.get("sub")
        role: Optional[str] = payload.get("role", "user")
        token_type: Optional[str] = payload.get("type")

        # 🔐 Validate payload
        if not user_id or token_type != "access":
            raise HTTPException(
                status_code=401,
                detail="Invalid token payload"
            )

        return {
            "user_id": user_id,
            "role": role
        }

    except JWTError as e:
        logger.warning(
            "JWT_VALIDATION_FAILED",
            extra={
                "request_id": request_id_ctx.get(),
                "error": str(e)
            }
        )

        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token"
        )