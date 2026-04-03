"""
AI-powered matching engine for supply-demand allocation.
Coordinates with the AI pricing service and mints SUN tokens on allocation.
"""
from sqlalchemy.orm import Session
from datetime import datetime
import logging

from app.models import House, GenerationRecord, DemandRecord, Allocation, PoolState
from app.services.ai_pricing import AIPricingService
from app.services.pool_engine import PoolEngine

logger = logging.getLogger(__name__)


class MatchingEngine:
    """Matches solar supply to consumer demand with AI optimization."""

    def __init__(self, db: Session):
        self.db = db
        self.pool_engine = PoolEngine(db)
        self.ai_service = AIPricingService()

    def match_demand(self, house_id: int, demand_kwh: float) -> dict:
        """
        Match consumer demand with pool supply.
        Returns allocation breakdown, AI reasoning, and triggers SUN token mint.
        """
        house = self.db.query(House).filter(House.id == house_id).first()
        if not house:
            raise ValueError(f"House {house_id} not found")

        # ✅ Use live recalculated pool state (not cached DB value)
        pool_state = self.pool_engine.get_pool_state(house.feeder_id)
        available_supply = pool_state["current_supply_kwh"]

        # Get AI allocation decision
        ai_recommendation = self.ai_service.get_allocation_strategy(
            available_pool_kwh=available_supply,
            demand_kwh=demand_kwh,
            grid_rate_inr=self._get_grid_rate(),
            pool_rate_inr=self._get_pool_rate(),
            house_priority=5,
        )

        pool_allocation_kwh = min(
            ai_recommendation.get("pool_kwh", 0),
            available_supply,
            demand_kwh,
        )
        grid_fallback_kwh = max(0, demand_kwh - pool_allocation_kwh)

        # Save allocation record
        allocation = Allocation(
            house_id=house_id,
            allocated_kwh=pool_allocation_kwh,
            source_type="pool" if pool_allocation_kwh > 0 else "grid",
            status="confirmed",
            ai_reasoning=ai_recommendation.get("reasoning", ""),
        )
        self.db.add(allocation)

        # Update house monthly SUN received
        if pool_allocation_kwh > 0:
            house.current_month_sun_received = (
                (house.current_month_sun_received or 0) + pool_allocation_kwh
            )

        self.db.commit()
        self.db.refresh(allocation)

        # ✅ Mint SUN tokens to buyer if pool allocation happened
        blockchain_result = {"status": "skipped"}
        if pool_allocation_kwh > 0 and house.algorand_address and house.opt_in_sun_asa:
            try:
                from app.services.blockchain_service import BlockchainService
                blockchain = BlockchainService()
                blockchain_result = blockchain.transfer_sun_asa(
                    recipient_address=house.algorand_address,
                    amount_kwh=pool_allocation_kwh,
                    reason=f"pool_allocation_{allocation.id}",
                )
                if blockchain_result.get("status") == "submitted":
                    logger.info(
                        f"SUN tokens minted: {pool_allocation_kwh:.2f} SUN → "
                        f"{house.house_id} (TX: {blockchain_result.get('tx_id')})"
                    )
            except Exception as e:
                logger.warning(f"SUN mint skipped (non-critical): {e}")

        # ✅ Also update seller's SUN minted for houses that contributed supply
        self._credit_sellers(house.feeder_id, pool_allocation_kwh)

        # Update pool state in DB after allocation
        self.pool_engine.update_pool_state(house.feeder_id)

        logger.info(
            f"Demand matched: {house.house_id} → "
            f"Pool={pool_allocation_kwh:.2f}kWh, Grid={grid_fallback_kwh:.2f}kWh"
        )

        return {
            "allocation_id": allocation.id,
            "pool_kwh": pool_allocation_kwh,
            "grid_kwh": grid_fallback_kwh,
            "ai_reasoning": ai_recommendation.get("reasoning", ""),
            "estimated_pool_cost_inr": round(pool_allocation_kwh * self._get_pool_rate(), 2),
            "estimated_grid_cost_inr": round(grid_fallback_kwh * self._get_grid_rate(), 2),
            "sun_tokens_minted": pool_allocation_kwh if pool_allocation_kwh > 0 else 0,
            "blockchain_tx": blockchain_result.get("tx_id"),
        }

    def _credit_sellers(self, feeder_id: int, pool_kwh_sold: float):
        """
        Proportionally credit SUN tokens to active generators on this feeder.
        Each seller gets SUN proportional to their contribution to the pool.
        """
        if pool_kwh_sold <= 0:
            return

        from datetime import timedelta
        two_min_ago = datetime.utcnow() - timedelta(minutes=2)

        # Find active generating houses
        active_sellers = []
        seller_houses = self.db.query(House).filter(
            House.feeder_id == feeder_id,
            House.prosumer_type.in_(["seller", "generator", "prosumer"]),
            House.is_active == True,
        ).all()

        for h in seller_houses:
            latest = self.db.query(GenerationRecord).filter(
                GenerationRecord.house_id == h.id,
                GenerationRecord.created_at >= two_min_ago,
            ).order_by(GenerationRecord.created_at.desc()).first()
            if latest:
                active_sellers.append((h, latest.generation_kwh))

        if not active_sellers:
            return

        total_gen = sum(g for _, g in active_sellers)
        if total_gen == 0:
            return

        for seller_house, gen_kwh in active_sellers:
            share = gen_kwh / total_gen
            sun_earned = pool_kwh_sold * share
            seller_house.current_month_sun_minted = (
                (seller_house.current_month_sun_minted or 0) + sun_earned
            )

        self.db.commit()

    def _get_grid_rate(self) -> float:
        from config import settings
        return settings.discom_grid_rate

    def _get_pool_rate(self) -> float:
        from config import settings
        return settings.solar_pool_rate