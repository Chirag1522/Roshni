"""
Setup script to create IoT test houses in the database
"""
from app.database import SessionLocal
from app.models import House, Feeder

db = SessionLocal()

# Create or get feeder
feeder = db.query(Feeder).filter(Feeder.feeder_code == "FDR_12").first()
if not feeder:
    feeder = Feeder(
        feeder_code="FDR_12",
        location="Sector 12, New Delhi",
        total_capacity_kw=1000.0
    )
    db.add(feeder)
    db.commit()
    print("✅ Created FDR_12 Feeder")
else:
    print("✓ FDR_12 Feeder already exists")

# Create or get seller house
seller_house = db.query(House).filter(House.house_id == "HOUSE_FDR12_001").first()
if not seller_house:
    seller_house = House(
        house_id="HOUSE_FDR12_001",
        feeder_id=feeder.id,
        prosumer_type="generator",
        owner_name="Solar Seller One",
        email="seller1@test.com",
        phone="91-9999999001",
        solar_capacity_kw=5.0,
        monthly_avg_consumption=0
    )
    db.add(seller_house)
    db.commit()
    print("✅ Created HOUSE_FDR12_001 (Seller)")
else:
    print("✓ HOUSE_FDR12_001 already exists")

# Create or get buyer house
buyer_house = db.query(House).filter(House.house_id == "HOUSE_FDR12_002").first()
if not buyer_house:
    buyer_house = House(
        house_id="HOUSE_FDR12_002",
        feeder_id=feeder.id,
        prosumer_type="consumer",
        owner_name="Solar Buyer One",
        email="buyer1@test.com",
        phone="91-9999999002",
        solar_capacity_kw=0,
        monthly_avg_consumption=400
    )
    db.add(buyer_house)
    db.commit()
    print("✅ Created HOUSE_FDR12_002 (Buyer)")
else:
    print("✓ HOUSE_FDR12_002 already exists")

print("\n✅ IoT houses setup complete!")
print(f"Seller: {seller_house.house_id}")
print(f"Buyer: {buyer_house.house_id}")

# Verify they can connect
print("\n📡 IoT Code should use:")
print(f"  Seller: device_id='NodeMCU_001', house_id='{seller_house.house_id}'")
print(f"  Buyer: device_id='NodeMCU_002', house_id='{buyer_house.house_id}'")
print(f"  Auth Token: 'iot_secret_token_12345'")
print(f"  Backend URL: 'http://localhost:8000/api/iot/update'")

db.close()
