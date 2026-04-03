"""
IoT endpoints for solar generation updates.
NodeMCU devices push generation data here every 5 seconds.
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from datetime import datetime
import logging

from app.database import get_db
from app.models import House, GenerationRecord
from app.services.iot_service import iot_service

router = APIRouter()
logger = logging.getLogger(__name__)


class IoTData(BaseModel):
    auth_token: str
    device_id: str
    generation_kwh: float
    house_id: str
    signal_strength: int


@router.post("/test-generate")
async def test_generate(data: IoTData, db: Session = Depends(get_db)):
    """
    Test endpoint to simulate IoT generation.
    """
    # Auth check
    if data.auth_token != "iot_secret_token_12345":
        raise HTTPException(status_code=401, detail="Invalid auth token")

    # Find house
    house = db.query(House).filter(House.house_id == data.house_id).first()
    if not house:
        raise HTTPException(status_code=404, detail="House not found")

    # Store generation record
    record = GenerationRecord(
        house_id=house.id,
        generation_kwh=data.generation_kwh,
        device_id=data.device_id,
        signal_strength=data.signal_strength,
    )
    db.add(record)
    db.commit()

    # Update in-memory service
    iot_service.update_device_status(
        house_id=data.house_id,
        device_id=data.device_id,
        generation_kwh=data.generation_kwh,
        signal_strength=data.signal_strength,
    )

    return {
        "status": "success",
        "message": f"Simulated generation: {data.generation_kwh} kWh for {data.house_id}",
    }