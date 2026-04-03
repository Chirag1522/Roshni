"""
SQLAlchemy ORM models for ROSHNI.
Represents feeder-level solar energy pool entities.
"""
from sqlalchemy import Column, String, Float, Integer, DateTime, Boolean, Text, Enum, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from app.database import Base

class ProsumerType(str, enum.Enum):
    """Types of prosumers in the pool."""
    PURE_GENERATOR = "generator"  # Only produces
    PURE_CONSUMER = "consumer"    # Only consumes
    PROSUMER = "prosumer"         # Both produces and consumes

class AllocationStatus(str, enum.Enum):
    """Status of energy allocation."""
    PENDING = "pending"
    MATCHED = "matched"
    COMPLETED = "completed"
    FAILED = "failed"

class Feeder(Base):
    """
    Represents a feeder (sub-station district).
    E.g., FDR_12, FDR_NORTH_15
    """
    __tablename__ = "feeders"
    
    id = Column(Integer, primary_key=True, index=True)
    feeder_code = Column(String(50), unique=True, nullable=False)  # FDR_12
    location = Column(String(255))
    total_capacity_kw = Column(Float, default=1000.0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    houses = relationship("House", back_populates="feeder")
    pool_states = relationship("PoolState", back_populates="feeder")
    daily_logs = relationship("DailyLog", back_populates="feeder")

class House(Base):
    """
    Represents a consumer/prosumer house on the feeder.
    """
    __tablename__ = "houses"
    
    id = Column(Integer, primary_key=True, index=True)
    house_id = Column(String(50), unique=True, nullable=False)  # HOUSE_FDR12_001
    feeder_id = Column(Integer, ForeignKey("feeders.id"), nullable=False)
    prosumer_type = Column(String(20), default="prosumer")
    owner_name = Column(String(255))
    phone = Column(String(20))
    email = Column(String(255))
    algorand_address = Column(String(58), nullable=True, unique=True)  # Custodial wallet
    algorand_private_key = Column(Text, nullable=True)  # BASE64 encoded (DEMO ONLY)
    opt_in_sun_asa = Column(Boolean, default=False)  # Opted into SUN ASA
    wallet_created_at = Column(DateTime, nullable=True)
    solar_capacity_kw = Column(Float, default=5.0)  # Installed solar
    monthly_avg_consumption = Column(Float, default=300.0)  # kWh
    current_month_generation_kwh = Column(Float, default=0.0)
    current_month_sun_minted = Column(Float, default=0.0)  # SUN tokens minted
    current_month_sun_received = Column(Float, default=0.0)  # SUN tokens received
    current_month_sun_transferred = Column(Float, default=0.0)  # SUN tokens transferred to others
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    feeder = relationship("Feeder", back_populates="houses")
    generation_records = relationship("GenerationRecord", back_populates="house")
    demand_records = relationship("DemandRecord", back_populates="house")
    allocations = relationship("Allocation", back_populates="house")
    bills = relationship("MonthlyBill", back_populates="house")

class GenerationRecord(Base):
    """
    Real-time solar generation data from IoT devices.
    """
    __tablename__ = "generation_records"
    
    id = Column(Integer, primary_key=True, index=True)
    house_id = Column(Integer, ForeignKey("houses.id"), nullable=False)
    generation_kwh = Column(Float, nullable=False)  # Current generation
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    device_id = Column(String(50))  # e.g., NodeMCU_001
    signal_strength = Column(Float)  # WiFi RSSI
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    house = relationship("House", back_populates="generation_records")

class DemandRecord(Base):
    """
    Consumer demand submission for matching.
    """
    __tablename__ = "demand_records"
    
    id = Column(Integer, primary_key=True, index=True)
    house_id = Column(Integer, ForeignKey("houses.id"), nullable=False)
    demand_kwh = Column(Float, nullable=False)  # Requested allocation
    priority_level = Column(Integer, default=5)  # 1-10, higher = more urgent
    duration_hours = Column(Float, default=1.0)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    status = Column(String(20), default="pending")  # pending, fulfilled, partial
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    house = relationship("House", back_populates="demand_records")

class Allocation(Base):
    """
    Represents matched allocation between supply and demand.
    """
    __tablename__ = "allocations"
    
    id = Column(Integer, primary_key=True, index=True)
    house_id = Column(Integer, ForeignKey("houses.id"), nullable=False)
    allocated_kwh = Column(Float, nullable=False)
    source_type = Column(String(20))  # "pool", "grid", "own"
    status = Column(String(20), default="pending")  # pending, confirmed, completed
    ai_reasoning = Column(Text)  # Gemini reasoning
    transaction_hash = Column(String(100))  # Blockchain tx if applicable
    created_at = Column(DateTime, default=datetime.utcnow)
    settlement_date = Column(DateTime)
    
    # Relationships
    house = relationship("House", back_populates="allocations")

class PoolState(Base):
    """
    Tracks feeder-level pool state (buffer state).
    Updated every 5 minutes or on demand.
    """
    __tablename__ = "pool_states"
    
    id = Column(Integer, primary_key=True, index=True)
    feeder_id = Column(Integer, ForeignKey("feeders.id"), nullable=False)
    current_supply_kwh = Column(Float, default=0.0)  # Live generation in pool
    current_demand_kwh = Column(Float, default=0.0)  # Pending requests
    potential_shortage = Column(Float, default=0.0)
    grid_drawdown = Column(Float, default=0.0)  # What needs to come from grid
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    feeder = relationship("Feeder", back_populates="pool_states")

class DailyLog(Base):
    """
    Daily aggregate for blockchain storage (hash only).
    """
    __tablename__ = "daily_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    feeder_id = Column(Integer, ForeignKey("feeders.id"), nullable=False)
    log_date = Column(String(10), unique=True, index=True)  # YYYY-MM-DD
    total_generation_kwh = Column(Float)
    total_demand_kwh = Column(Float)
    total_pool_allocation_kwh = Column(Float)
    total_grid_drawdown_kwh = Column(Float)
    log_hash = Column(String(100))  # SHA256 of aggregate
    blockchain_txn = Column(String(100))  # Algorand TextNote tx
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    feeder = relationship("Feeder", back_populates="daily_logs")

class MonthlyBill(Base):
    """
    Monthly bill with blockchain-backed hash.
    """
    __tablename__ = "monthly_bills"
    
    id = Column(Integer, primary_key=True, index=True)
    house_id = Column(Integer, ForeignKey("houses.id"), nullable=False)
    month_year = Column(String(7), index=True)  # YYYY-MM
    
    # Physical metrics
    solar_generated_kwh = Column(Float, default=0.0)
    solar_exported_kwh = Column(Float, default=0.0)
    pool_bought_kwh = Column(Float, default=0.0)
    pool_sold_kwh = Column(Float, default=0.0)
    grid_bought_kwh = Column(Float, default=0.0)
    
    # Charges (INR)
    solar_export_credit = Column(Float, default=0.0)
    pool_sale_credit = Column(Float, default=0.0)
    pool_purchase_charge = Column(Float, default=0.0)
    grid_purchase_charge = Column(Float, default=0.0)
    discom_fixed_charge = Column(Float, default=0.0)
    discom_admin_fee = Column(Float, default=0.0)
    net_payable = Column(Float, default=0.0)
    
    # Blockchain
    bill_hash = Column(String(100))  # SHA256
    blockchain_txn = Column(String(100))  # Algorand tx
    sun_asa_minted = Column(Float, default=0.0)  # SUN tokens (1 = 1kWh renewable)
    
    status = Column(String(20), default="draft")  # draft, finalized, paid
    created_at = Column(DateTime, default=datetime.utcnow)
    finalized_at = Column(DateTime)
    
    # Relationships
    house = relationship("House", back_populates="bills")
    