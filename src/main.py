"""
HWELBEING — FASTAPI ENTRY POINT (FINAL STABLE)

Purpose:
- Secure REST APIs with JWT
- Stable WebSocket registration (NO 403)
- Proper lifespan handling
"""

import uuid
import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Depends
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from slowapi.errors import RateLimitExceeded

from src.config import settings
from src.limit import limiter
from src.core.logger import get_logger, request_id_ctx
from src.core.security import (
    verify_token,
    create_access_token,
    verify_password,
    get_password_hash
)

from src.db.connection import init_pool, close_pool
from src.db.core import execute_query, fetch_one

# Routers (HTTP ONLY)
from src.predictions_api.triage_service import router as triage_router
from src.predictions_api.skin_service import router as skin_router

# WebSocket (DIRECT REGISTRATION)
from src.Conversational_module.realtime_voice import attach_ws

# Services
from src.Conversational_module.doctor_service import find_doctors
from src.ml_engine.lung_risk.inference import predict_lung_risk

logger = get_logger(__name__)


# =========================================================
# LIFESPAN (DB + MODEL LOAD)
# =========================================================
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("APP_STARTUP_INIT")

    await init_pool()

    loop = asyncio.get_running_loop()

    # preload models safely
    from src.ml_engine.nlp_triage import inference as _
    from src.ml_engine.lung_risk import inference as _
    from src.ml_engine.skin_cnn import inference as _

    await loop.run_in_executor(None, lambda: None)

    logger.info("MODELS_PRELOADED")

    yield

    await close_pool()
    logger.info("APP_SHUTDOWN_COMPLETE")


app = FastAPI(
    title="HWellbeing AI Healthcare System",
    version="1.0.0",
    lifespan=lifespan
)


# =========================================================
# 🔥 REGISTER WEBSOCKET (CRITICAL FIX)
# =========================================================
attach_ws(app)


# =========================================================
# REQUEST ID MIDDLEWARE
# =========================================================
@app.middleware("http")
async def request_id_middleware(request: Request, call_next):
    request_id = str(uuid.uuid4())
    request_id_ctx.set(request_id)

    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response


# =========================================================
# CORS (STRICT — NO "*")
# =========================================================
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Authorization", "Content-Type"],
)


# =========================================================
# RATE LIMIT
# =========================================================
app.state.limiter = limiter

@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(
        status_code=429,
        content={"error": "Too many requests"}
    )


# =========================================================
# STATIC FILES
# =========================================================
app.mount("/static", StaticFiles(directory="static"), name="static")


# =========================================================
# ROUTERS (JWT PROTECTED)
# =========================================================
app.include_router(
    triage_router,
    prefix="/api/v1",
    dependencies=[Depends(verify_token)]
)

app.include_router(
    skin_router,
    prefix="/api/v1",
    dependencies=[Depends(verify_token)]
)


# =========================================================
# HEALTH
# =========================================================
@app.get("/api/v1/health")
async def health():
    return {
        "status": "ok",
        "db_connected": True,
        "models_loaded": True,
        "version": "1.0.0"
    }


# =========================================================
# AUTH — REGISTER
# =========================================================
@app.post("/api/v1/auth/register")
async def register(body: dict):
    username = body.get("username")
    password = body.get("password")

    if not username or not password:
        return JSONResponse(
            status_code=400,
            content={"error": "Username and password required"}
        )

    existing = await fetch_one(
        "SELECT ID FROM HWELLBEING.USERS WHERE USERNAME = ?",
        (username,)
    )

    if existing:
        return JSONResponse(
            status_code=400,
            content={"error": "User already exists"}
        )

    password_hash = get_password_hash(password)

    await execute_query(
        "INSERT INTO HWELLBEING.USERS (USERNAME, PASSWORD_HASH, ROLE) VALUES (?, ?, ?)",
        (username, password_hash, "user")
    )

    return {"message": "User registered successfully"}


# =========================================================
# AUTH — LOGIN
# =========================================================
@app.post("/api/v1/auth/login")
async def login(body: dict):
    username = body.get("username")
    password = body.get("password")

    user = await fetch_one(
        "SELECT USERNAME, PASSWORD_HASH FROM HWELLBEING.USERS WHERE USERNAME = ?",
        (username,)
    )

    if not user:
        return JSONResponse(
            status_code=401,
            content={"error": "Invalid credentials"}
        )

    db_username, password_hash = user

    if not verify_password(password, password_hash):
        return JSONResponse(
            status_code=401,
            content={"error": "Invalid credentials"}
        )

    token = create_access_token(db_username)

    return {
        "access_token": token,
        "token_type": "bearer"
    }


# =========================================================
# LUNG RISK
# =========================================================
@app.post("/api/v1/predict/lung")
async def lung_risk(body: dict, user=Depends(verify_token)):

    if "features" not in body:
        return JSONResponse(
            status_code=400,
            content={"error": "Missing features"}
        )

    loop = asyncio.get_running_loop()

    result = await loop.run_in_executor(
        None,
        predict_lung_risk,
        body["features"]
    )

    return {
        "risk_level": result.get("risk_level", "unknown"),
        "confidence": float(result.get("confidence", 0)),
        "factors": result.get("factors", [])
    }


# ==============
# DOCTORS 
# ==============
@app.post("/api/v1/doctors")
async def doctors(body: dict, user=Depends(verify_token)):

    try:
        lat = body.get("lat")
        lon = body.get("lon")

        # ✅ validation
        if not isinstance(lat, (int, float)) or not isinstance(lon, (int, float)):
            return JSONResponse(
                status_code=400,
                content={"error": "Invalid lat/lon"}
            )

        # ✅ CORRECT CALL (async → await)
        result = await find_doctors(lat, lon)

        # ✅ safe fallback
        if not result:
            return {
                "available": False,
                "confidence": 0.0,
                "doctors": [],
                "message": "No doctors found"
            }

        return result

    except Exception as e:
        logger.error("DOCTOR_API_ERROR", extra={"error": str(e)})

        return {
            "available": False,
            "confidence": 0.0,
            "doctors": [],
            "message": "Doctor service failed"
        }