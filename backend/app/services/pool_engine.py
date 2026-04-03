"""
Feeder-level energy pool engine.
Maintains pool state and manages supply/demand balance.
"""
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, timezone
import logging

from app.models import (
    Feeder, House, GenerationRecord, DemandRecord,
    Allocation, PoolState
)

logger = logging.getLogger(__name__)


class PoolEngine:
    """Manages feeder-level solar energy pool operations."""

    def __init__(self, db: Session):
        self.db = db

    def get_or_create_feeder(self, feeder_code: str) -> Feeder:
        """Get feeder by code or create if doesn't exist."""
        feeder = self.db.query(Feeder).filter(
            Feeder.feeder_code == feeder_code
        ).first()

        if not feeder:
            feeder = Feeder(feeder_code=feeder_code)
            self.db.add(feeder)
            self.db.commit()
            self.db.refresh(feeder)

        return feeder

    def get_pool_state(self, feeder_id: int) -> dict:
        """
        Get current pool state for a feeder.
        Uses latest generation reading per house (not sum of all records).
        A house is considered active if it sent data in last 2 minutes.
        Includes real-time IoT data from connected devices.
        """
        logger.debug(f"Getting pool state for feeder {feeder_id}")
        two_min_ago = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(minutes=10)

        # Get all active houses on this feeder
        houses = self.db.query(House).filter(
            House.feeder_id == feeder_id,
            House.is_active == True,
        ).all()

        logger.debug(f"Found {len(houses)} active houses on feeder {feeder_id}")
        total_supply = 0.0
        active_generators = 0

        for house in houses:
            logger.debug(f"Checking house {house.house_id} (feeder: {house.feeder_id})")
            # First check real-time IoT data (from main.py global dict)
            iot_generation = self._get_realtime_iot_generation(house.house_id)
            if iot_generation is not None:
                # Use real-time IoT data if available
                total_supply += iot_generation
                active_generators += 1
                logger.info(f"Using IoT data for {house.house_id}: {iot_generation} kW")
            else:
                # Fallback to latest database record
                latest = self.db.query(GenerationRecord).filter(
                    GenerationRecord.house_id == house.id,
                    GenerationRecord.created_at >= two_min_ago,
                ).order_by(GenerationRecord.created_at.desc()).first()

                if latest:
                    total_supply += latest.generation_kwh
                    active_generators += 1
                    logger.debug(f"Using DB data for {house.house_id}: {latest.generation_kwh} kW")

        # Subtract recently allocated pool energy (simulates committed supply)
        recent_allocations = self.db.query(Allocation).join(House).filter(
            House.feeder_id == feeder_id,
            Allocation.source_type == "pool",
            Allocation.created_at >= two_min_ago,
        ).all()
        allocated_supply = sum(a.allocated_kwh for a in recent_allocations)
        total_supply = max(0, total_supply - allocated_supply)  # Pool decreases when allocated

        # Get pending demand across feeder
        pending_demand = self.db.query(DemandRecord).join(House).filter(
            House.feeder_id == feeder_id,
            DemandRecord.status == "pending",
        ).all()

        total_demand = sum(d.demand_kwh for d in pending_demand)
        grid_drawdown = max(0, total_demand - total_supply)

        # Count today's fulfilled trades for dashboard display
        today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0).replace(tzinfo=None)
        fulfilled_today = self.db.query(DemandRecord).join(House).filter(
            House.feeder_id == feeder_id,
            DemandRecord.status.in_(["fulfilled", "partial"]),
            DemandRecord.created_at >= today_start,
        ).all()
        today_fulfilled_kwh = sum(d.demand_kwh for d in fulfilled_today)

        result = {
            "current_supply_kwh": total_supply,
            "current_demand_kwh": total_demand,
            "today_fulfilled_kwh": today_fulfilled_kwh,
            "today_trade_count": len(fulfilled_today),
            "grid_drawdown": grid_drawdown,
            "surplus": max(0, total_supply - total_demand),
            "shortage": grid_drawdown,
            "active_generators": active_generators,
            "timestamp": datetime.utcnow(),
        }
        logger.info(f"Pool state for feeder {feeder_id}: Supply={total_supply:.2f}, Demand={total_demand:.2f}, Traded={today_fulfilled_kwh:.2f}")
        return result

    def _get_realtime_iot_generation(self, house_id: str) -> float:
        """Get current generation from IoT devices for pool calculations."""
        try:
            # Try to get IoT data from a global registry
            # This avoids circular imports with main.py
            import sys
            main_module = sys.modules.get('main')
            if main_module and hasattr(main_module, 'iot_service'):
                iot_service = main_module.iot_service
                # Return current generation for pool supply
                current = iot_service.get_generation(house_id)
                if current > 0:
                    return current
            return None
        except Exception as e:
            logger.debug(f"Could not get IoT data for {house_id}: {e}")
            return None

    def update_pool_state(self, feeder_id: int) -> PoolState:
        """Update or create pool state record in DB."""
        state_data = self.get_pool_state(feeder_id)

        pool_state = self.db.query(PoolState).filter(
            PoolState.feeder_id == feeder_id
        ).order_by(PoolState.created_at.desc()).first()

        if not pool_state:
            pool_state = PoolState(feeder_id=feeder_id)

        pool_state.current_supply_kwh = state_data["current_supply_kwh"]
        pool_state.current_demand_kwh = state_data["current_demand_kwh"]
        pool_state.grid_drawdown = state_data["grid_drawdown"]
        pool_state.timestamp = datetime.utcnow()

        self.db.add(pool_state)
        self.db.commit()
        self.db.refresh(pool_state)

        logger.debug(
            f"Pool state updated: "
            f"Supply={state_data['current_supply_kwh']:.2f}kWh, "
            f"Demand={state_data['current_demand_kwh']:.2f}kWh, "
            f"GridDrawdown={state_data['grid_drawdown']:.2f}kWh"
        )

        return pool_state