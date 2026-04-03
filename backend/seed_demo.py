"""
Seed demo data for ROSHNI (compatible with current models).
Run once before testing dashboard.
"""

from app.database import get_db
from app import models
from datetime import datetime


def seed():
    db = next(get_db())

    # -------------------------
    # Prevent duplicate seeding
    # -------------------------
    if db.query(models.Feeder).first():
        print("⚠️ Feeders already exist. Skipping seed.")
        return

    # -------------------------
    # Create Feeder
    # -------------------------
    feeder = models.Feeder(
        feeder_code="FDR_12",
        location="Jaipur Urban Zone",
        total_capacity_kw=500.0
    )
    db.add(feeder)
    db.commit()
    db.refresh(feeder)

    # -------------------------
    # Create Houses
    # -------------------------

    # Solar Prosumer
    house1 = models.House(
        house_id="HOUSE_FDR12_001",
        feeder_id=feeder.id,
        prosumer_type="prosumer",
        owner_name="Rahul Sharma",
        solar_capacity_kw=5.0,
        monthly_avg_consumption=300.0
    )

    # Pure Consumer
    house2 = models.House(
        house_id="HOUSE_FDR12_002",
        feeder_id=feeder.id,
        prosumer_type="consumer",
        owner_name="Neha Gupta",
        solar_capacity_kw=0.0,
        monthly_avg_consumption=450.0
    )

    db.add_all([house1, house2])
    db.commit()

    # -------------------------
    # Add Initial Pool State
    # -------------------------
    pool = models.PoolState(
        feeder_id=feeder.id,
        current_supply_kwh=0.0,
        current_demand_kwh=0.0,
        grid_drawdown=0.0,
        timestamp=datetime.utcnow()
    )

    db.add(pool)
    db.commit()

    print("✅ Demo feeder and houses created successfully!")


if __name__ == "__main__":
    seed()
