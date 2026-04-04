"""
Consumer demand submission and matching endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import logging

from app.database import get_db
from app.schemas import DemandSubmit, DemandResponse
from app.models import House, DemandRecord
from app.services.matching_engine import MatchingEngine
from config import settings

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/submit", response_model=DemandResponse)
async def submit_demand(data: DemandSubmit, db: Session = Depends(get_db)):
    """Submit energy demand and trigger AI matching."""
    house = db.query(House).filter(House.house_id == data.house_id).first()
    if not house:
        raise HTTPException(status_code=404, detail="House not found")

    # Record demand as pending
    demand = DemandRecord(
        house_id=house.id,
        demand_kwh=data.demand_kwh,
        priority_level=data.priority_level,
        duration_hours=data.duration_hours,
        status="pending",
    )
    db.add(demand)
    db.commit()
    db.refresh(demand)

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
            "estimated_grid_cost_inr": data.demand_kwh * settings.discom_grid_rate,
            "sun_tokens_minted": 0,
            "blockchain_tx": None,
            "allocation_id": None,
        }

    # ✅ Fix: mark demand as fulfilled so it stops counting in pool demand
    demand.status = "fulfilled" if result["grid_kwh"] == 0 else "partial"
    db.commit()

    logger.info(
        f"Demand matched: {data.house_id} → "
        f"Pool={result['pool_kwh']:.2f}kWh, Grid={result['grid_kwh']:.2f}kWh"
    )

    return DemandResponse(
        demand_id=demand.id,
        allocation_id=result.get("allocation_id"),
        house_id=data.house_id,
        demand_kwh=data.demand_kwh,
        allocation_status="matched" if result["grid_kwh"] == 0 else "partial",
        allocated_kwh=result["pool_kwh"],
        grid_required_kwh=result["grid_kwh"],
        ai_reasoning=result["ai_reasoning"],
        estimated_cost_inr=result["estimated_pool_cost_inr"] + result["estimated_grid_cost_inr"],
        estimated_pool_cost_inr=result["estimated_pool_cost_inr"],
        estimated_grid_cost_inr=result["estimated_grid_cost_inr"],
        sun_tokens_minted=result.get("sun_tokens_minted", 0),
        blockchain_tx=result.get("blockchain_tx"),
    )


@router.get("/status/{demand_id}")
async def get_demand_status(demand_id: int, db: Session = Depends(get_db)):
    """Get status of a demand request."""
    demand = db.query(DemandRecord).filter(DemandRecord.id == demand_id).first()
    if not demand:
        raise HTTPException(status_code=404, detail="Demand not found")

    return {
        "demand_id": demand.id,
        "demand_kwh": demand.demand_kwh,
        "status": demand.status,
        "created_at": demand.created_at,
    }