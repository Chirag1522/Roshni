"""
ROSHNI Backend - Main FastAPI Application Entry Point
AI-powered DISCOM-compliant solar energy pool with blockchain allocation proof.
"""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging
from pydantic import BaseModel

from config import settings
from logging_config import setup_logging
from app import models
from app.database import init_db, get_db
from app.routes import demand, dashboard, billing, admin, blockchain, wallet, voice
# NOTE: IoT router is replaced by a simple inline endpoint below


# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan context manager."""
    # Startup
    logger.info("🌞 ROSHNI Backend Starting...")
    init_db()
    logger.info(f"Environment: {settings.environment}")
    logger.info(f"Debug mode: {settings.debug}")
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
    allow_origins=settings.cors_origins,
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
# IoT endpoint is defined directly below, so we no longer include the separate router
app.include_router(demand.router, prefix="/api/demand", tags=["Demand"])
app.include_router(dashboard.router, prefix="/api/dashboard", tags=["Dashboard"])
app.include_router(wallet.router, prefix="/api/wallet", tags=["Wallet"])
app.include_router(billing.router, prefix="/api/billing", tags=["Billing"])
app.include_router(admin.router, prefix="/api/admin", tags=["Admin"])
app.include_router(blockchain.router, prefix="/api/blockchain", tags=["Blockchain"])
app.include_router(voice.router, prefix="/api/voice", tags=["Voice"])

# Health check
@app.get("/health", tags=["System"])
async def health_check():
    """System health check endpoint."""
    return {
        "status": "healthy",
        "service": "ROSHNI Backend",
        "environment": settings.environment,
    }


# IoT data model and simple update endpoint placed directly on the main app
class IoTData(BaseModel):
    auth_token: str
    device_id: str
    generation_kwh: float
    house_id: str
    signal_strength: int

# Import IoT service
from app.services.iot_service import iot_service

@app.post("/api/iot/update")
async def update_iot(data: IoTData):
    # log arrival immediately to aid debugging
    logger.debug("IoT update endpoint called")
    logger.info(f"ESP32 DATA RECEIVED: {data.json()}")

    # store the latest IoT reading using the IoT service
    iot_service.update_device_status(
        data.house_id,
        data.device_id,
        data.generation_kwh,
        data.signal_strength
    )

    # Update pool state with new generation data
    try:
        from app.database import get_db
        from app.services.pool_engine import PoolEngine
        from app.models import House
        from sqlalchemy.orm import Session

        # Get a database session
        db_generator = get_db()
        db: Session = next(db_generator)

        try:
            house = db.query(House).filter(House.house_id == data.house_id).first()

            if house:
                pool_engine = PoolEngine(db)
                pool_state = pool_engine.update_pool_state(house.feeder_id)
                logger.info(f"Updated pool state for feeder {house.feeder_code}: Supply={pool_state.current_supply_kwh:.2f}kWh, Demand={pool_state.current_demand_kwh:.2f}kWh")
            else:
                logger.warning(f"House {data.house_id} not found in database")
        finally:
            db.close()
    except Exception as e:
        logger.error(f"Failed to update pool state: {e}")

    # simulate pool status (since pool engine was removed)
    # in a real implementation, this would come from pool calculations
    import random
    allocation_status = random.choice(["sufficient", "allocating", "shortage"])
    current_pool_supply = round(random.uniform(10.0, 20.0), 1)
    current_pool_demand = round(random.uniform(8.0, 18.0), 1)

    # proper response format that ESP32 expects for LED control
    response_payload = {
        "status": "recorded",
        "allocation_status": allocation_status,  # controls LED: sufficient/green, allocating/yellow, shortage/red
        "current_pool_supply": current_pool_supply,
        "current_pool_demand": current_pool_demand,
        "message": f"Generation recorded. Pool status: {allocation_status}",
    }
    # use JSONResponse to guarantee content-length header
    from fastapi.responses import JSONResponse
    return JSONResponse(content=response_payload)

@app.get("/api/iot/status/{house_id}")
async def get_iot_status(house_id: str):
    """Get the latest IoT device status for a house."""
    logger.debug(f"IoT status requested for house: {house_id}")

    status = iot_service.get_device_status(house_id)
    if status:
        logger.info(f"Returning IoT status for {house_id}: {status}")
        return status
    else:
        logger.warning(f"No IoT data found for house: {house_id}")
        return {"status": "offline", "message": "No IoT device data available"}

@app.get("/api/iot/debug")
async def debug_iot_status():
    """Debug endpoint to see all stored IoT data."""
    return {
        "stored_data": iot_service.get_all_status(),
        "house_count": len(iot_service.get_all_status())
    }

@app.get("/api/iot/debug")
async def debug_iot_status():
    """Debug endpoint to see all stored IoT data."""
    return {
        "stored_data": iot_device_status,
        "house_count": len(iot_device_status)
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