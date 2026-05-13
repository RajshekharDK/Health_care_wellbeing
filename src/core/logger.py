"""
HWELBEING — STRUCTURED LOGGER (PRODUCTION)

Purpose:
Structured JSON logging with request tracing and safe serialization.

Exports:
- get_logger(name)
- request_id_ctx
"""

import logging
import json
import sys
from datetime import datetime
from contextvars import ContextVar


# =========================================================
# REQUEST CONTEXT
# =========================================================
request_id_ctx: ContextVar[str] = ContextVar("request_id", default="unknown")


# =========================================================
# JSON FORMATTER
# =========================================================
class JSONFormatter(logging.Formatter):
    """
    Custom JSON log formatter with safe serialization.
    """

    def format(self, record: logging.LogRecord) -> str:
        log_record = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "request_id": request_id_ctx.get(),
            "module": record.name,
            "message": record.getMessage(),
        }

        # 🔹 Handle extra fields safely
        if hasattr(record, "__dict__"):
            for key, value in record.__dict__.items():
                if key not in (
                    "name", "msg", "args", "levelname", "levelno",
                    "pathname", "filename", "module", "exc_info",
                    "exc_text", "stack_info", "lineno", "funcName",
                    "created", "msecs", "relativeCreated",
                    "thread", "threadName", "processName", "process"
                ):
                    try:
                        json.dumps(value)  # test serializable
                        log_record[key] = value
                    except Exception:
                        log_record[key] = str(value)

        # 🔹 Exception handling
        if record.exc_info:
            log_record["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_record)


# =========================================================
# LOGGER FACTORY
# =========================================================
def get_logger(name: str) -> logging.Logger:
    """
    Returns configured JSON logger.
    """

    logger = logging.getLogger(name)

    # Prevent duplicate handlers
    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JSONFormatter())

    logger.addHandler(handler)
    logger.propagate = False

    return logger