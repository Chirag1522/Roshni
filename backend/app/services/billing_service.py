"""
Monthly billing service with realistic slab-based electricity pricing.
Aggregates transactions, calculates net payable using Rajasthan tariff.
Ties to blockchain: SUN transfers, bill hashing.
"""
from sqlalchemy.orm import Session
from datetime import datetime
from dateutil.relativedelta import relativedelta
import logging
import json

from app.models import (
    House, GenerationRecord, DemandRecord, Allocation, MonthlyBill
)
from app.utils.hash_utils import sha256_hash
from app.utils.pricing_models import (
    RajasthanDomesticTariff,
    RajasthanCommercialTariff,
    SolarExportRates,
    PoolPricingModel,
    calculate_house_bill
)
from app.services.blockchain_service import BlockchainService
from config import settings

logger = logging.getLogger(__name__)

class BillingService:
    """Generates and manages monthly bills for houses."""

    def __init__(self, db: Session):
        self.db = db
        self.blockchain_service = BlockchainService()
    
    def generate_monthly_bill(self, house_id: int, month_year: str) -> MonthlyBill:
        """
        Generate monthly bill for a house using realistic slab-based pricing.
        Accounts for prosumer type: pure generator, pure consumer, or prosumer.
        month_year: "2024-03" format
        """
        house = self.db.query(House).filter(House.id == house_id).first()
        if not house:
            raise ValueError(f"House {house_id} not found")

        # Parse month
        year, month = month_year.split("-")
        start_date = datetime(int(year), int(month), 1)
        end_date = start_date + relativedelta(months=1) - relativedelta(seconds=1)

        # Calculate metrics from generation and demand records
        generation_records = self.db.query(GenerationRecord).filter(
            GenerationRecord.house_id == house_id,
            GenerationRecord.created_at >= start_date,
            GenerationRecord.created_at <= end_date,
        ).all()

        solar_generated = sum(g.generation_kwh for g in generation_records)

        # Get allocations for pool trading
        allocations = self.db.query(Allocation).filter(
            Allocation.house_id == house_id,
            Allocation.created_at >= start_date,
            Allocation.created_at <= end_date,
            Allocation.status == "completed",
        ).all()

        # Calculate pool trading metrics
        pool_sold_kwh = sum(
            a.allocated_kwh for a in allocations
            if house.prosumer_type in ["generator", "prosumer"]
        )
        pool_bought_kwh = sum(
            a.allocated_kwh for a in allocations
            if house.prosumer_type in ["consumer", "prosumer"]
        )

        # Determine grid consumption (simplified - would come from DISCOM data)
        # For prosumers: grid consumption = average monthly consumption - pool bought
        # For pure consumers: grid consumption = average monthly consumption - pool bought
        # For pure generators: grid consumption = 0 (or minimal household use)
        grid_bought_kwh = max(0, house.monthly_avg_consumption - pool_bought_kwh)

        # ============ REALISTIC SLAB-BASED PRICING ============

        # 1. DISCOM CHARGES (for grid consumption)
        house_type = "domestic"  # Default - can be determined from house_id pattern or additional field

        # Calculate DISCOM bill for grid consumption
        discom_bill_breakdown = calculate_house_bill(
            house_type=house_type,
            consumption_kwh=grid_bought_kwh,
            grid_consumption_kwh=grid_bought_kwh,
            sanctioned_load_kw=2.0  # Default, can be customized per house
        )

        grid_purchase_charge = discom_bill_breakdown["total_bill"]
        discom_fixed_charge = discom_bill_breakdown["fixed_charge"]

        # 2. SOLAR EXPORT CREDIT
        # Solar exported to grid gets buyback rates
        solar_export_credit = solar_generated * SolarExportRates.RESIDENTIAL_EXPORT_RATE

        # 3. POOL TRADING CREDITS AND CHARGES
        # Pool sold: prosumers receive money for surplus sold to other consumers
        pool_sale_credit = pool_sold_kwh * PoolPricingModel.BASE_POOL_PRICE

        # Pool bought: consumers pay pool rate (cheaper than grid rate)
        pool_purchase_charge = pool_bought_kwh * PoolPricingModel.BASE_POOL_PRICE

        # 4. DISCOM ADMIN FEE
        # Fee on total settlement (pool sale + grid purchase)
        discom_admin_fee = (pool_sale_credit + grid_purchase_charge) * (
            settings.discom_admin_fee_percent / 100.0
        )

        # ============ NET PAYABLE CALCULATION ============
        # Positive = house owes money
        # Negative = house gets credit
        net_payable = (
            grid_purchase_charge          # What they owe to DISCOM for grid
            + discom_admin_fee            # Admin fees
            + pool_purchase_charge        # What they owe for pool purchases
        ) - (
            solar_export_credit           # What they earn from solar export
            + pool_sale_credit            # What they earn from pool sales
        )

        # Create bill record
        bill = MonthlyBill(
            house_id=house_id,
            month_year=month_year,
            solar_generated_kwh=solar_generated,
            solar_exported_kwh=solar_generated,  # Assume all can be exported/sold
            pool_bought_kwh=pool_bought_kwh,
            pool_sold_kwh=pool_sold_kwh,
            grid_bought_kwh=grid_bought_kwh,
            solar_export_credit=round(solar_export_credit, 2),
            pool_sale_credit=round(pool_sale_credit, 2),
            pool_purchase_charge=round(pool_purchase_charge, 2),
            grid_purchase_charge=round(grid_purchase_charge, 2),
            discom_fixed_charge=round(discom_fixed_charge, 2),
            discom_admin_fee=round(discom_admin_fee, 2),
            net_payable=round(net_payable, 2),
            sun_asa_minted=solar_generated,  # 1 SUN = 1 kWh renewable
        )

        self.db.add(bill)
        self.db.commit()
        self.db.refresh(bill)

        logger.info(
            f"Bill generated for {house.house_id} ({month_year}): "
            f"Grid: {grid_bought_kwh:.1f} kWh @ ₹{grid_purchase_charge:.2f}, "
            f"Pool sold: {pool_sold_kwh:.1f} kWh @ ₹{pool_sale_credit:.2f}, "
            f"Net payable: ₹{net_payable:.2f} (Slab-based pricing)"
        )

        return bill
    
    def finalize_bill(self, bill_id: int, bill_hash: str = None) -> MonthlyBill:
        """
        Finalize bill: create hash and record on blockchain.
        Bill hash = SHA256(full bill JSON) for integrity.
        """
        bill = self.db.query(MonthlyBill).filter(MonthlyBill.id == bill_id).first()
        if not bill:
            raise ValueError(f"Bill {bill_id} not found")

        house = self.db.query(House).filter(House.id == bill.house_id).first()

        if not bill_hash:
            # Create hash from complete bill data (JSON)
            bill_data = {
                "house_id": house.house_id if house else bill.house_id,
                "month_year": bill.month_year,
                "solar_generated": bill.solar_generated_kwh,
                "solar_exported": bill.solar_exported_kwh,
                "pool_bought": bill.pool_bought_kwh,
                "pool_sold": bill.pool_sold_kwh,
                "grid_bought": bill.grid_bought_kwh,
                "solar_export_credit": bill.solar_export_credit,
                "pool_sale_credit": bill.pool_sale_credit,
                "pool_purchase_charge": bill.pool_purchase_charge,
                "grid_purchase_charge": bill.grid_purchase_charge,
                "discom_fixed_charge": bill.discom_fixed_charge,
                "discom_admin_fee": bill.discom_admin_fee,
                "net_payable": bill.net_payable,
                "sun_asa_minted": bill.sun_asa_minted,
            }
            bill_json = json.dumps(bill_data, sort_keys=True)
            bill_hash = sha256_hash(bill_json)

        bill.bill_hash = bill_hash
        bill.status = "finalized"
        bill.finalized_at = datetime.utcnow()

        # Record bill hash on blockchain
        blockchain_result = self.blockchain_service.record_bill_hash(
            bill_hash,
            house.house_id if house else f"HOUSE_{bill.house_id}",
            bill.month_year,
        )

        if blockchain_result.get("status") == "submitted":
            bill.blockchain_txn = blockchain_result.get("tx_id")
            logger.info(
                f"Bill {bill.month_year} for {house.house_id if house else bill.house_id} "
                f"recorded on blockchain: {blockchain_result.get('tx_id')}"
            )

        self.db.commit()
        self.db.refresh(bill)

        return bill