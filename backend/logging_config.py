"""
Logging configuration for ROSHNI.
Only shows what matters: ROSHNI app logs + errors.
SQLAlchemy, uvicorn access logs, and debug noise are suppressed.
"""
import logging
import logging.config
import os
import sys
from config import settings
from datetime import datetime

# Force UTF-8 on Windows console so unicode chars don't crash the logger
if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "format": "[%(asctime)s] %(levelname)s - %(message)s",
            "datefmt": "%H:%M:%S",
        },
        "detailed": {
            "format": "[%(asctime)s] %(name)s:%(lineno)d - %(levelname)s - %(message)s",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "level": "INFO",
            "formatter": "default",
            "stream": "ext://sys.stdout",
        },
        "file": {
            "class": "logging.FileHandler",
            "level": "INFO",
            "formatter": "detailed",
            "filename": f"logs/roshni_{datetime.now().strftime('%Y%m%d')}.log",
        },
    },
    "loggers": {
        # ── ROSHNI app: show INFO and above ───────────────────────────────
        "main":                         {"level": "INFO",    "handlers": ["console", "file"], "propagate": False},
        "app":                          {"level": "INFO",    "handlers": ["console", "file"], "propagate": False},
        "app.services.pool_engine":     {"level": "WARNING", "handlers": ["console", "file"], "propagate": False},

        # ── SQLAlchemy: silence completely (show only critical errors) ────
        "sqlalchemy":                   {"level": "ERROR",   "handlers": ["file"], "propagate": False},
        "sqlalchemy.engine":            {"level": "ERROR",   "handlers": ["file"], "propagate": False},
        "sqlalchemy.engine.Engine":     {"level": "ERROR",   "handlers": ["file"], "propagate": False},
        "sqlalchemy.pool":              {"level": "ERROR",   "handlers": ["file"], "propagate": False},
        "sqlalchemy.dialects":          {"level": "ERROR",   "handlers": ["file"], "propagate": False},
        "sqlalchemy.orm":               {"level": "ERROR",   "handlers": ["file"], "propagate": False},

        # ── Uvicorn: only errors, no per-request access logs ─────────────
        "uvicorn":                      {"level": "WARNING", "handlers": ["console"], "propagate": False},
        "uvicorn.error":                {"level": "WARNING", "handlers": ["console"], "propagate": False},
        "uvicorn.access":               {"level": "ERROR",   "handlers": ["file"],    "propagate": False},

        # ── Other noisy libraries ─────────────────────────────────────────
        "asyncio":                      {"level": "WARNING", "handlers": ["console"], "propagate": False},
        "multipart":                    {"level": "WARNING", "handlers": ["console"], "propagate": False},
    },
    "root": {
        "level": "WARNING",
        "handlers": ["console", "file"],
    },
}


def setup_logging():
    """Initialize logging configuration."""
    os.makedirs("logs", exist_ok=True)
    logging.config.dictConfig(LOGGING_CONFIG)