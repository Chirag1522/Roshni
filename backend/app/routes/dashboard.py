"""
Dashboard endpoints for displaying real-time pool state and allocations.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import logging

from app.database import get_db
from app.schemas import DashboardResponse, HouseGenerationSummary, HouseDemandSummary, LivePoolState
from app.models import House, GenerationRecord, DemandRecord, PoolState
from app.services.pool_engine import PoolEngine

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/{house_id}", response_model=DashboardResponse)
async def get_dashboard(house_id: str, db: Session = Depends(get_db)):
    """
    Get dashboard data for a house (seller or buyer view).
    Includes live pool state, generation/demand summaries, earnings/savings.
    """
    house = db.query(House).filter(House.house_id == house_id).first()
    if not house:
        raise HTTPException(status_code=404, detail="House not found")

    # Generation summary (today)
    today = datetime.utcnow().date()
    today_generation = db.query(GenerationRecord).filter(
        GenerationRecord.house_id == house.id,
        GenerationRecord.created_at >= datetime.combine(today, datetime.min.time()),
    ).all()

    today_gen_kwh = sum(g.generation_kwh for g in today_generation)

    generation_summary = HouseGenerationSummary(
        house_id=house_id,
        today_generated_kwh=today_gen_kwh,
        this_month_generated_kwh=house.current_month_generation_kwh or 0,  # Use actual DB value
        average_hourly_kw=today_gen_kwh / 24 if today_gen_kwh > 0 else 0,
        peak_generation_kw=max(
            (g.generation_kwh for g in today_generation), default=0
        ),
        latest_generation_timestamp=max(
            (g.created_at for g in today_generation), default=None
        ),
    ) if today_generation else None

    # Demand summary (today)
    today_demand = db.query(DemandRecord).filter(
        DemandRecord.house_id == house.id,
        DemandRecord.created_at >= datetime.combine(today, datetime.min.time()),
    ).all()

    today_demand_kwh = sum(d.demand_kwh for d in today_demand)

    demand_summary = HouseDemandSummary(
        house_id=house_id,
        today_demand_kwh=today_demand_kwh,
        this_month_demand_kwh=today_demand_kwh * 30,
        average_hourly_kw=today_demand_kwh / 24 if today_demand_kwh > 0 else 0,
        allocation_rate=0.8,       # Placeholder
        grid_dependency_rate=0.2,  # Placeholder
    ) if today_demand else None

    # ── Live pool state (READ ONLY — no write on dashboard GET) ──────────────
    pool_engine = PoolEngine(db)
    pool_state = pool_engine.get_pool_state(house.feeder_id)  # was: update_pool_state()

    if pool_state:
        live_pool = LivePoolState(
            feeder_code=house.feeder.feeder_code,
            current_supply_kwh=pool_state.get("current_supply_kwh", 0),
            current_demand_kwh=pool_state.get("current_demand_kwh", 0),
            grid_drawdown_kwh=pool_state.get("grid_drawdown", 0),
            today_fulfilled_kwh=pool_state.get("today_fulfilled_kwh", 0),
            today_trade_count=pool_state.get("today_trade_count", 0),
            timestamp=pool_state.get("timestamp", datetime.utcnow()),
        )
    else:
        # No pool state yet — return zeroed state
        live_pool = LivePoolState(
            feeder_code=house.feeder.feeder_code,
            current_supply_kwh=0,
            current_demand_kwh=0,
            grid_drawdown_kwh=0,
            today_fulfilled_kwh=0,
            today_trade_count=0,
            timestamp=datetime.utcnow(),
        )

    # Earnings/savings estimate
    # prosumer_type in seed = "seller" | "buyer" (align with your seed data)
    allocation_earnings = today_gen_kwh * 9.0 if house.prosumer_type in ["seller", "generator", "prosumer"] else 0
    allocation_savings = today_demand_kwh * 9.0 if house.prosumer_type in ["buyer", "consumer", "prosumer"] else 0

    return DashboardResponse(
        house_id=house_id,
        feeder_code=house.feeder.feeder_code,
        prosumer_type=house.prosumer_type,
        generation_summary=generation_summary,
        demand_summary=demand_summary,
        live_pool_state=live_pool,
        allocation_earnings_estimate_inr=allocation_earnings,
        allocation_savings_estimate_inr=allocation_savings,
    )


@router.get("/pool/{feeder_code}")
async def get_pool_state(feeder_code: str, db: Session = Depends(get_db)):
    """Get current feeder pool state."""
    from app.models import Feeder

    feeder = db.query(Feeder).filter(Feeder.feeder_code == feeder_code).first()
    if not feeder:
        raise HTTPException(status_code=404, detail="Feeder not found")

    pool_engine = PoolEngine(db)
    state_data = pool_engine.get_pool_state(feeder.id)

    return {
        "feeder_code": feeder_code,
        **(state_data or {}),
        "timestamp": datetime.utcnow(),
    }