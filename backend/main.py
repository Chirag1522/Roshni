"""
ROSHNI Backend - Main FastAPI Application Entry Point
AI-powered DISCOM-compliant solar energy pool with blockchain allocation proof.
"""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging

from config import settings
from logging_config import setup_logging
from app import models
from app.database import init_db
from app.routes import demand, dashboard, billing, admin, blockchain, wallet, voice, iot


# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan context manager."""
    # Startup
    logger.info("🌞 ROSHNI Backend Starting...")
    try:
        init_db()
        logger.info(f"Environment: {settings.environment}")
        logger.info(f"Debug mode: {settings.debug}")
        logger.info("✅ Database initialized successfully")
    except Exception as e:
        logger.warning(f"⚠️ Database initialization warning: {e}")
        logger.info("Continuing without database init (will retry on first query)")
    yield
    # Shutdown
    logger.info("🌞 ROSHNI Backend Shutting Down...")

app = FastAPI(
    title="ROSHNI - Solar Energy Pool",
    description="AI-powered DISCOM-compliant feeder-level energy allocation with blockchain transparency",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS Configuration  
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow IoT devices and frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all incoming requests."""
    logger.debug(f"{request.method} {request.url.path}")
    response = await call_next(request)
    logger.debug(f"Response status: {response.status_code}")
    return response

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle unexpected exceptions globally."""
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "type": type(exc).__name__},
    )

# API Routers
app.include_router(demand.router, prefix="/api/demand", tags=["Demand"])
app.include_router(dashboard.router, prefix="/api/dashboard", tags=["Dashboard"])
app.include_router(wallet.router, prefix="/api/wallet", tags=["Wallet"])
app.include_router(billing.router, prefix="/api/billing", tags=["Billing"])
app.include_router(admin.router, prefix="/api/admin", tags=["Admin"])
app.include_router(blockchain.router, prefix="/api/blockchain", tags=["Blockchain"])
app.include_router(voice.router, prefix="/api/voice", tags=["Voice"])
app.include_router(iot.router, prefix="/api/iot", tags=["IoT"])

# Health check
@app.get("/health", tags=["System"])
async def health_check():
    """System health check endpoint."""
    return {
        "status": "healthy",
        "service": "ROSHNI Backend",
        "environment": settings.environment,
    }


@app.get("/", tags=["System"])
async def root():
    """Root endpoint with API information."""
    return {
        "name": "ROSHNI",
        "version": "1.0.0",
        "description": "AI-powered solar energy pool with blockchain allocation proof",
        "feeder_based": True,
        "discom_compliant": True,
        "blockchain_enabled": True,
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        log_level=settings.log_level.lower(),
    )
