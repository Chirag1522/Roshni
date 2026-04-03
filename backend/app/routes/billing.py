"""
Billing and financial statement endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import logging

from app.database import get_db
from app.schemas import MonthlyBillDetail
from app.models import House, MonthlyBill
from app.services.billing_service import BillingService

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/generate/{house_id}/{month_year}")
async def generate_bill(
    house_id: str,
    month_year: str,
    db: Session = Depends(get_db),
):
    """Generate bill for a house for given month."""
    house = db.query(House).filter(House.house_id == house_id).first()
    if not house:
        raise HTTPException(status_code=404, detail="House not found")

    existing = db.query(MonthlyBill).filter(
        MonthlyBill.house_id == house.id,
        MonthlyBill.month_year == month_year,
    ).first()

    if existing:
        return {"status": "already_exists", "bill_id": existing.id}

    billing_service = BillingService(db)
    bill = billing_service.generate_monthly_bill(house.id, month_year)

    logger.info(f"Bill generated: {house_id} / {month_year}")

    return {
        "status": "generated",
        "bill_id": bill.id,
        "net_payable": bill.net_payable,
    }


# ✅ Fix: this MUST be before /{house_id}/{month_year}
# Otherwise FastAPI matches /HOUSE_X/monthly-list as month_year="monthly-list"
@router.get("/{house_id}/monthly-list")
async def get_bill_list(house_id: str, db: Session = Depends(get_db)):
    """Get list of all bills for a house."""
    house = db.query(House).filter(House.house_id == house_id).first()
    if not house:
        raise HTTPException(status_code=404, detail="House not found")

    bills = db.query(MonthlyBill).filter(
        MonthlyBill.house_id == house.id,
    ).order_by(MonthlyBill.month_year.desc()).all()

    return [
        {
            "bill_id": b.id,
            "month_year": b.month_year,
            "net_payable": b.net_payable,
            "status": b.status,
        }
        for b in bills
    ]


@router.get("/{house_id}/{month_year}", response_model=MonthlyBillDetail)
async def get_bill(
    house_id: str,
    month_year: str,
    db: Session = Depends(get_db),
):
    """Retrieve detailed monthly bill."""
    house = db.query(House).filter(House.house_id == house_id).first()
    if not house:
        raise HTTPException(status_code=404, detail="House not found")

    bill = db.query(MonthlyBill).filter(
        MonthlyBill.house_id == house.id,
        MonthlyBill.month_year == month_year,
    ).first()

    if not bill:
        raise HTTPException(status_code=404, detail="Bill not found")

    return bill


@router.post("/{bill_id}/finalize")
async def finalize_bill(bill_id: int, db: Session = Depends(get_db)):
    """Finalize bill and record on blockchain."""
    bill = db.query(MonthlyBill).filter(MonthlyBill.id == bill_id).first()
    if not bill:
        raise HTTPException(status_code=404, detail="Bill not found")

    billing_service = BillingService(db)
    bill = billing_service.finalize_bill(bill_id)

    from app.services.blockchain_service import BlockchainService
    blockchain = BlockchainService()
    blockchain_result = blockchain.record_bill_hash(
        bill_hash=bill.bill_hash,
        house_id=bill.house.house_id,
        month_year=bill.month_year,
    )

    if blockchain_result.get("status") == "pending_signature":
        bill.blockchain_txn = blockchain_result.get("message")
        db.commit()

    return {
        "status": "finalized",
        "bill_id": bill.id,
        "net_payable": bill.net_payable,
        "bill_hash": bill.bill_hash,
        "blockchain_status": blockchain_result.get("status"),
    }