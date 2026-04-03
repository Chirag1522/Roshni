"""
Pydantic request/response schemas for API validation and documentation.
"""
from pydantic import BaseModel, Field, validator
from datetime import datetime
from typing import Optional, List

# ============= IoT Schemas =============

class GenerationUpdate(BaseModel):
    """IoT device generation update submission."""
    house_id: str = Field(..., description="House identifier, e.g., HOUSE_FDR12_001")
    generation_kwh: float = Field(..., gt=0, description="Current solar generation in kWh")
    device_id: Optional[str] = None
    signal_strength: Optional[float] = None
    auth_token: str = Field(..., description="IoT authentication token")

    class Config:
        json_schema_extra = {
            "example": {
                "house_id": "HOUSE_FDR12_001",
                "generation_kwh": 2.5,
                "device_id": "NodeMCU_001",
                "signal_strength": -60.0,
                "auth_token": "iot_secret_token_12345"
            }
        }

class GenerationResponse(BaseModel):
    """Response after generation update."""
    status: str
    allocation_status: str
    current_pool_supply: float
    current_pool_demand: float
    message: str

    class Config:
        from_attributes = True

# ============= Demand Schemas =============

class DemandSubmit(BaseModel):
    """Consumer demand submission."""
    house_id: str
    demand_kwh: float = Field(..., gt=0)
    priority_level: int = Field(default=5, ge=1, le=10)
    duration_hours: float = Field(default=1.0, gt=0)

    class Config:
        json_schema_extra = {
            "example": {
                "house_id": "HOUSE_FDR12_002",
                "demand_kwh": 5.0,
                "priority_level": 7,
                "duration_hours": 2.0
            }
        }

class DemandResponse(BaseModel):
    """Response after demand submission."""
    demand_id: int
    house_id: str
    demand_kwh: float
    allocation_status: str
    allocated_kwh: float
    grid_required_kwh: float
    ai_reasoning: str
    estimated_cost_inr: float
    sun_tokens_minted: float = 0.0
    blockchain_tx: Optional[str] = None

    class Config:
        from_attributes = True

# ============= Dashboard Schemas =============

class LivePoolState(BaseModel):
    """Live feeder pool state."""
    feeder_code: str
    current_supply_kwh: float
    current_demand_kwh: float
    grid_drawdown_kwh: float
    today_fulfilled_kwh: float = 0.0
    today_trade_count: int = 0
    timestamp: datetime

    class Config:
        from_attributes = True

class HouseGenerationSummary(BaseModel):
    """Summary of house generation for dashboard."""
    house_id: str
    today_generated_kwh: float
    this_month_generated_kwh: float
    average_hourly_kw: float
    peak_generation_kw: float
    latest_generation_timestamp: Optional[datetime]

    class Config:
        from_attributes = True

class HouseDemandSummary(BaseModel):
    """Summary of house demand."""
    house_id: str
    today_demand_kwh: float
    this_month_demand_kwh: float
    average_hourly_kw: float
    allocation_rate: float
    grid_dependency_rate: float

    class Config:
        from_attributes = True

class DashboardResponse(BaseModel):
    """Complete dashboard data for a house."""
    house_id: str
    feeder_code: str
    prosumer_type: str
    generation_summary: Optional[HouseGenerationSummary]
    demand_summary: Optional[HouseDemandSummary]
    live_pool_state: LivePoolState
    allocation_earnings_estimate_inr: float
    allocation_savings_estimate_inr: float

    class Config:
        from_attributes = True

# ============= Billing Schemas =============

class MonthlyBillDetail(BaseModel):
    """Detailed monthly bill."""
    # ✅ Fix 1: house_id is int FK in model, was str → causes ResponseValidationError
    bill_id: Optional[int] = None
    house_id: Optional[int] = None
    month_year: str

    # Metrics
    solar_generated_kwh: float = 0.0
    solar_exported_kwh: float = 0.0
    pool_bought_kwh: float = 0.0
    pool_sold_kwh: float = 0.0
    grid_bought_kwh: float = 0.0

    # Charges
    solar_export_credit: float = 0.0
    pool_sale_credit: float = 0.0
    pool_purchase_charge: float = 0.0
    grid_purchase_charge: float = 0.0
    discom_fixed_charge: float = 0.0
    discom_admin_fee: float = 0.0
    net_payable: float = 0.0

    # Blockchain
    sun_asa_minted: float = 0.0
    # ✅ Fix 2: bill_hash is None for draft bills, was non-optional str
    bill_hash: Optional[str] = None
    blockchain_txn: Optional[str] = None
    status: str = "draft"

    class Config:
        from_attributes = True

# ============= Admin Schemas =============

class NightModeToggle(BaseModel):
    """Admin toggle for night mode simulation."""
    enabled: bool
    feeder_code: Optional[str] = None
    reason: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "enabled": True,
                "feeder_code": "FDR_12",
                "reason": "Cloud cover simulation"
            }
        }

class NightModeResponse(BaseModel):
    """Response to night mode toggle."""
    status: str
    message: str
    affected_feeders: List[str]
    solar_generation_multiplier: float

# ============= Blockchain Schemas =============

class BlockchainTransaction(BaseModel):
    """Blockchain transaction record."""
    txn_id: str
    asset_id: int
    amount: float
    from_address: str
    to_address: str
    timestamp: datetime
    confirmed: bool

    class Config:
        from_attributes = True

class ASATransferRequest(BaseModel):
    """Request to transfer SUN ASA."""
    house_id: str
    amount: float = Field(..., gt=0, description="Amount of SUN tokens (1 = 1 kWh renewable)")
    reason: str = Field(default="allocation", description="Purpose of transfer")

class BillHashSubmit(BaseModel):
    """Submit bill hash to blockchain."""
    house_id: str
    month_year: str
    bill_hash: str = Field(..., description="SHA256 hash of monthly bill")

class BillHashResponse(BaseModel):
    """Response from bill hash submission."""
    status: str
    bill_hash: str
    blockchain_txn: str
    explorer_url: str
    timestamp: datetime