"""
Administrative endpoints for system control and dashboard.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
import logging

from app.database import get_db
from app.schemas import NightModeToggle, NightModeResponse
from app.models import (
    Feeder, House, GenerationRecord, DemandRecord, Allocation,
    MonthlyBill, PoolState
)

router = APIRouter()
logger = logging.getLogger(__name__)

# Global night mode state (in production, use cache/database)
_night_mode_state = {}

@router.post("/night-mode", response_model=NightModeResponse)
async def toggle_night_mode(
    data: NightModeToggle,
    db: Session = Depends(get_db),
):
    """
    Admin endpoint to toggle night mode for simulation/testing.
    In night mode, solar generation drops to 0.
    """
    if data.feeder_code:
        feeder = db.query(Feeder).filter(
            Feeder.feeder_code == data.feeder_code
        ).first()
        if not feeder:
            raise HTTPException(status_code=404, detail="Feeder not found")
        affected_feeders = [data.feeder_code]
    else:
        # All feeders
        feeders = db.query(Feeder).all()
        affected_feeders = [f.feeder_code for f in feeders]
    
    _night_mode_state[data.feeder_code or "all"] = data.enabled
    
    logger.info(
        f"Night mode {'enabled' if data.enabled else 'disabled'} "
        f"for: {','.join(affected_feeders[:5])}"
    )
    
    return NightModeResponse(
        status="updated",
        message=f"Night mode {'enabled' if data.enabled else 'disabled'}",
        affected_feeders=affected_feeders,
        solar_generation_multiplier=0.0 if data.enabled else 1.0,
    )

@router.get("/night-mode-status")
async def get_night_mode_status():
    """Get current night mode status."""
    return {
        "night_mode_enabled": bool(_night_mode_state.get("all")),
        "state_by_feeder": _night_mode_state,
    }

@router.get("/feeders/{feeder_code}")
async def get_feeder_details(feeder_code: str, db: Session = Depends(get_db)):
    """Get feeder details."""
    feeder = db.query(Feeder).filter(
        Feeder.feeder_code == feeder_code
    ).first()
    
    if not feeder:
        raise HTTPException(status_code=404, detail="Feeder not found")
    
    house_count = len(feeder.houses)
    
    return {
        "feeder_code": feeder.feeder_code,
        "location": feeder.location,
        "total_capacity_kw": feeder.total_capacity_kw,
        "house_count": house_count,
        "created_at": feeder.created_at,
    }

@router.get("/houses/{feeder_code}")
async def list_houses_in_feeder(feeder_code: str, db: Session = Depends(get_db)):
    """List all houses in a feeder."""
    feeder = db.query(Feeder).filter(
        Feeder.feeder_code == feeder_code
    ).first()

    if not feeder:
        raise HTTPException(status_code=404, detail="Feeder not found")

    return [
        {
            "house_id": h.house_id,
            "prosumer_type": h.prosumer_type,
            "solar_capacity_kw": h.solar_capacity_kw,
            "is_active": h.is_active,
        }
        for h in feeder.houses
    ]


# ============= ADMIN DASHBOARD ENDPOINTS =============

@router.get("/dashboard/feeder/{feeder_code}/daily")
async def get_feeder_daily_summary(feeder_code: str, db: Session = Depends(get_db)):
    """
    Admin dashboard: daily summary for a feeder.
    Shows generation, demand, allocations, grid fallback.
    """
    feeder = db.query(Feeder).filter(Feeder.feeder_code == feeder_code).first()
    if not feeder:
        raise HTTPException(status_code=404, detail="Feeder not found")

    # Today's data
    today = datetime.utcnow().date()
    start = datetime.combine(today, datetime.min.time())
    end = datetime.combine(today, datetime.max.time())

    # Get all houses on feeder
    houses = db.query(House).filter(House.feeder_id == feeder.id).all()
    house_ids = [h.id for h in houses]

    # Generation sum
    generation_records = db.query(GenerationRecord).filter(
        GenerationRecord.house_id.in_(house_ids) if house_ids else False,
        GenerationRecord.created_at >= start,
        GenerationRecord.created_at <= end,
    ).all()
    total_generation = sum(g.generation_kwh for g in generation_records)

    # Demand sum
    demand_records = db.query(DemandRecord).filter(
        DemandRecord.house_id.in_(house_ids) if house_ids else False,
        DemandRecord.created_at >= start,
        DemandRecord.created_at <= end,
        DemandRecord.status == "fulfilled",
    ).all()
    total_demand = sum(d.demand_kwh for d in demand_records)

    # Allocations
    allocations = db.query(Allocation).filter(
        Allocation.house_id.in_(house_ids) if house_ids else False,
        Allocation.created_at >= start,
        Allocation.created_at <= end,
        Allocation.status == "completed",
    ).all()
    pool_allocated = sum(a.allocated_kwh for a in allocations if a.source_type == "pool")
    grid_fallback = sum(a.allocated_kwh for a in allocations if a.source_type == "grid")

    # Latest pool state
    pool_state = db.query(PoolState).filter(
        PoolState.feeder_id == feeder.id
    ).order_by(PoolState.timestamp.desc()).first() if house_ids else None

    return {
        "status": "success",
        "feeder_code": feeder_code,
        "date": today.isoformat(),
        "metrics": {
            "total_generation_kwh": round(total_generation, 2),
            "total_demand_kwh": round(total_demand, 2),
            "pool_allocated_kwh": round(pool_allocated, 2),
            "grid_fallback_kwh": round(grid_fallback, 2),
            "surplus_kwh": round(max(0, total_generation - total_demand), 2),
        },
        "houses": {
            "total": len(houses),
            "active": len([h for h in houses if h.is_active]),
            "with_wallet": len([h for h in houses if h.algorand_address]),
            "opted_in_sun": len([h for h in houses if h.opt_in_sun_asa]),
        },
        "pool_state_latest": {
            "supply": pool_state.current_supply_kwh if pool_state else 0,
            "demand": pool_state.current_demand_kwh if pool_state else 0,
            "timestamp": pool_state.timestamp.isoformat() if pool_state else None,
        },
    }


@router.get("/dashboard/feeder/{feeder_code}/monthly")
async def get_feeder_monthly_summary(feeder_code: str, db: Session = Depends(get_db)):
    """
    Admin dashboard: monthly summary for a feeder.
    Revenue, costs, net profit, SUN tokens.
    """
    feeder = db.query(Feeder).filter(Feeder.feeder_code == feeder_code).first()
    if not feeder:
        raise HTTPException(status_code=404, detail="Feeder not found")

    houses = db.query(House).filter(House.feeder_id == feeder.id).all()
    house_ids = [h.id for h in houses]

    # Get all bills for houses this month
    today = datetime.utcnow()
    month_start = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    month_year = month_start.strftime("%Y-%m")

    bills = db.query(MonthlyBill).filter(
        MonthlyBill.house_id.in_(house_ids) if house_ids else False,
        MonthlyBill.month_year == month_year,
        MonthlyBill.status == "finalized",
    ).all()

    # Aggregate metrics
    total_generation = sum(b.solar_generated_kwh for b in bills)
    total_exported = sum(b.solar_exported_kwh for b in bills)
    total_pool_bought = sum(b.pool_bought_kwh for b in bills)
    total_pool_sold = sum(b.pool_sold_kwh for b in bills)
    total_grid_bought = sum(b.grid_bought_kwh for b in bills)

    # Revenue
    solar_export_revenue = sum(b.solar_export_credit for b in bills)
    pool_sales_revenue = sum(b.pool_sale_credit for b in bills)

    # Costs
    pool_purchase_cost = sum(b.pool_purchase_charge for b in bills)
    grid_purchase_cost = sum(b.grid_purchase_charge for b in bills)
    discom_fees = sum(b.discom_fixed_charge + b.discom_admin_fee for b in bills)

    # SUN tokens
    total_sun_minted = sum(b.sun_asa_minted for b in bills)

    # Net
    net_revenue = (
        (solar_export_revenue + pool_sales_revenue)
        - (pool_purchase_cost + grid_purchase_cost + discom_fees)
    )

    return {
        "status": "success",
        "feeder_code": feeder_code,
        "month_year": month_year,
        "energy_metrics": {
            "total_generation_kwh": round(total_generation, 2),
            "total_exported_kwh": round(total_exported, 2),
            "pool_bought_kwh": round(total_pool_bought, 2),
            "pool_sold_kwh": round(total_pool_sold, 2),
            "grid_bought_kwh": round(total_grid_bought, 2),
        },
        "financial": {
            "revenue": {
                "solar_export_credit_inr": round(solar_export_revenue, 2),
                "pool_sales_credit_inr": round(pool_sales_revenue, 2),
                "total_revenue_inr": round(solar_export_revenue + pool_sales_revenue, 2),
            },
            "costs": {
                "pool_purchase_charge_inr": round(pool_purchase_cost, 2),
                "grid_purchase_charge_inr": round(grid_purchase_cost, 2),
                "discom_fixed_and_admin_fee_inr": round(discom_fees, 2),
                "total_costs_inr": round(pool_purchase_cost + grid_purchase_cost + discom_fees, 2),
            },
            "net_revenue_inr": round(net_revenue, 2),
        },
        "blockchain": {
            "sun_tokens_minted": round(total_sun_minted, 0),
            "bills_recorded_on_chain": len([b for b in bills if b.blockchain_txn]),
        },
    }


@router.get("/dashboard/all-feeders")
async def get_all_feeders_summary(db: Session = Depends(get_db)):
    """
    Admin dashboard: summary for all feeders.
    High-level DISCOM view.
    """
    feeders = db.query(Feeder).all()

    feeder_list = []
    for feeder in feeders:
        houses = db.query(House).filter(House.feeder_id == feeder.id).all()
        houses_with_wallet = len([h for h in houses if h.algorand_address])
        houses_opted_in = len([h for h in houses if h.opt_in_sun_asa])

        feeder_list.append({
            "feeder_code": feeder.feeder_code,
            "location": feeder.location,
            "total_capacity_kw": feeder.total_capacity_kw,
            "houses": {
                "total": len(houses),
                "active": len([h for h in houses if h.is_active]),
                "with_wallet": houses_with_wallet,
                "opted_in_sun": houses_opted_in,
                "deployment_percent": round((houses_opted_in / len(houses) * 100) if houses else 0, 1),
            },
        })

    return {
        "status": "success",
        "total_feeders": len(feeders),
        "feeders": feeder_list,
    }


@router.get("/setup/status")
async def get_setup_status(db: Session = Depends(get_db)):
    """
    Admin endpoint: Check current setup status.
    Shows which houses have wallets, generation records, etc.
    """
    from app.services.iot_service import iot_service
    
    houses = db.query(House).all()
    feeders = db.query(Feeder).all()
    
    house_details = []
    for house in houses:
        gen_records = db.query(GenerationRecord).filter(GenerationRecord.house_id == house.id).all()
        demand_records = db.query(DemandRecord).filter(DemandRecord.house_id == house.id).all()
        
        iot_status = iot_service.get_device_status(house.house_id)
        
        house_details.append({
            "house_id": house.house_id,
            "prosumer_type": house.prosumer_type,
            "has_wallet": bool(house.algorand_address),
            "opted_in_sun": house.opt_in_sun_asa,
            "generation_records": len(gen_records),
            "total_generated_kwh": sum(g.generation_kwh for g in gen_records),
            "demand_records": len(demand_records),
            "total_demanded_kwh": sum(d.demand_kwh for d in demand_records),
            "iot_status": "online" if iot_status and iot_status.get("status") == "online" else "offline",
            "current_generation_kw": iot_status.get("generation_kwh", 0) if iot_status else 0,
        })
    
    return {
        "status": "success",
        "feeders": len(feeders),
        "houses": house_details,
        "iot_service": {
            "all_devices": iot_service.get_all_status(),
        },
    }
async def initialize_all_wallets(db: Session = Depends(get_db)):
    """
    Admin endpoint: Initialize wallets for all houses in the system.
    Useful for demo/testing.
    """
    from app.services.wallet_service import WalletService
    
    houses = db.query(House).all()
    wallet_service = WalletService()
    
    results = {
        "initialized": [],
        "already_initialized": [],
        "errors": [],
    }
    
    for house in houses:
        if house.algorand_address:
            results["already_initialized"].append(house.house_id)
            continue
        
        try:
            # Create wallet
            wallet_result = wallet_service.create_wallet()
            house.algorand_address = wallet_result["algorand_address"]
            house.algorand_private_key = wallet_result["algorand_private_key"]
            
            # Fund wallet
            fund_result = wallet_service.fund_wallet(wallet_result["algorand_address"], 2.0)
            
            # Opt-in to SUN ASA
            opt_in_result = wallet_service.opt_in_to_sun_asa(
                algorand_address=wallet_result["algorand_address"],
                algorand_private_key=wallet_result["algorand_private_key"],
            )
            
            if opt_in_result.get("status") == "success":
                house.opt_in_sun_asa = True
            
            db.commit()
            results["initialized"].append({
                "house_id": house.house_id,
                "address": wallet_result["algorand_address"][:15] + "...",
                "funded": fund_result.get("status") == "success",
                "opted_in": opt_in_result.get("status") == "success",
            })
            
            logger.info(f"Initialized wallet for {house.house_id}")
        except Exception as e:
            results["errors"].append({
                "house_id": house.house_id,
                "error": str(e),
            })
            logger.error(f"Failed to initialize wallet for {house.house_id}: {e}")
    
    return {
        "status": "success",
        "results": results,
    }