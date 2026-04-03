"""
IoT endpoints for solar generation updates and buyer demand.
NodeMCU devices push generation/demand data here every 5 seconds.
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from datetime import datetime
import logging

from app.database import get_db
from app.models import House, GenerationRecord, DemandRecord, Allocation
from app.services.iot_service import iot_service
from app.services.matching_engine import MatchingEngine

router = APIRouter()
logger = logging.getLogger(__name__)


class IoTData(BaseModel):
    auth_token: str
    device_id: str
    generation_kwh: float
    house_id: str
    signal_strength: int


class IoTDemandData(BaseModel):
    auth_token: str
    device_id: str
    demand_kwh: float
    house_id: str


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


@router.post("/demand")
async def submit_iot_demand(data: IoTDemandData, db: Session = Depends(get_db)):
    """
    Receive demand from buyer IoT device (ESP32 with potentiometer).
    Automatically triggers matching and returns allocation (pool or grid).
    """
    # Auth check
    if data.auth_token != "iot_secret_token_12345":
        raise HTTPException(status_code=401, detail="Invalid auth token")

    # Find house
    house = db.query(House).filter(House.house_id == data.house_id).first()
    if not house:
        raise HTTPException(status_code=404, detail="House not found")

    # Skip if demand is too low (noise filtering)
    if data.demand_kwh < 0.1:
        return {
            "status": "skipped",
            "reason": "Demand below threshold",
            "demand_kwh": data.demand_kwh,
        }

    # Record demand as pending
    demand = DemandRecord(
        house_id=house.id,
        demand_kwh=data.demand_kwh,
        priority_level="normal",
        duration_hours=1.0,
        status="pending",
    )
    db.add(demand)
    db.commit()
    db.refresh(demand)

    # Store in IoT service for real-time tracking
    iot_service.update_buyer_demand(data.house_id, data.demand_kwh, data.device_id)

    # Run matching engine
    try:
        matching = MatchingEngine(db)
        result = matching.match_demand(house.id, data.demand_kwh)
    except Exception as e:
        logger.error(f"Matching failed for {data.house_id}: {e}")
        # Fallback: allocate all from grid
        result = {
            "pool_kwh": 0,
            "grid_kwh": data.demand_kwh,
            "ai_reasoning": "Fallback: matching failed, using grid",
            "estimated_pool_cost_inr": 0,
            "estimated_grid_cost_inr": data.demand_kwh * 12,
            "sun_tokens_minted": 0,
            "blockchain_tx": None,
        }

    # Update demand status based on result
    demand.status = "fulfilled" if result["grid_kwh"] == 0 else "partial"
    db.commit()

    # Save allocation to database
    allocation = Allocation(
        house_id=house.id,
        allocated_kwh=result["pool_kwh"],
        source_type="pool" if result["grid_kwh"] == 0 else "hybrid",
        status="confirmed",
        ai_reasoning=result["ai_reasoning"],
        transaction_hash=result.get("blockchain_tx"),
    )
    db.add(allocation)
    db.commit()
    db.refresh(allocation)

    logger.info(
        f"IoT Demand matched: {data.house_id} → "
        f"Pool={result['pool_kwh']:.2f}kWh, Grid={result['grid_kwh']:.2f}kWh"
    )

    return {
        "status": "matched",
        "demand_kwh": data.demand_kwh,
        "allocated_kwh": result["pool_kwh"],
        "grid_required_kwh": result["grid_kwh"],
        "allocation_status": "matched" if result["grid_kwh"] == 0 else "partial",
        "ai_reasoning": result["ai_reasoning"],
        "sun_tokens_minted": result.get("sun_tokens_minted", 0),
        "blockchain_tx": result.get("blockchain_tx"),
    }


@router.get("/demand-status/{house_id}")
async def get_demand_status(house_id: str, db: Session = Depends(get_db)):
    """
    Get current IoT demand status and latest allocation for buyer dashboard.
    Returns real-time data for auto-updating frontend.
    """
    # Get device status
    iot_status = iot_service.get_buyer_demand(house_id)
    
    if not iot_status:
        return {
            "house_id": house_id,
            "current_demand_kwh": 0,
            "device_online": False,
            "allocation": None,
        }

    # Get latest demand record to check for allocation
    house = db.query(House).filter(House.house_id == house_id).first()
    if not house:
        return {
            "house_id": house_id,
            "current_demand_kwh": iot_status.get("demand_kwh", 0),
            "device_online": True,
            "allocation": None,
        }

    # Get the most recent demand record
    latest_demand = (
        db.query(DemandRecord)
        .filter(DemandRecord.house_id == house.id)
        .order_by(DemandRecord.created_at.desc())
        .first()
    )

    if latest_demand:
        # Get related allocation data
        allocation = (
            db.query(Allocation)
            .filter(Allocation.house_id == house.id)
            .order_by(Allocation.created_at.desc())
            .first()
        )
        
        allocated_kwh = allocation.allocated_kwh if allocation else 0
        grid_required = latest_demand.demand_kwh - allocated_kwh
        
        return {
            "house_id": house_id,
            "current_demand_kwh": iot_status.get("demand_kwh", 0),
            "device_online": True,
            "last_update": iot_status.get("last_update"),
            "allocation": {
                "demand_id": latest_demand.id,
                "demand_kwh": latest_demand.demand_kwh,
                "allocation_status": "matched" if latest_demand.status == "fulfilled" else "partial",
                "allocated_kwh": allocated_kwh,
                "grid_required_kwh": max(0, grid_required),
                "status": latest_demand.status,
                "ai_reasoning": allocation.ai_reasoning if allocation else "Matching in progress...",
                "estimated_cost_inr": (allocated_kwh * 9) + (max(0, grid_required) * 12),
                "sun_tokens_minted": 0,
                "blockchain_tx": allocation.transaction_hash if allocation else None,
                "created_at": latest_demand.created_at.isoformat(),
            },
        }

    return {
        "house_id": house_id,
        "current_demand_kwh": iot_status.get("demand_kwh", 0),
        "device_online": True,
        "allocation": None,
    }