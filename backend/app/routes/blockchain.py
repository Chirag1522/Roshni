"""
Blockchain endpoints for SUN ASA and bill hash operations.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from datetime import datetime
import re
import logging
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.schemas import ASATransferRequest, BillHashSubmit, BillHashResponse
from app.services.blockchain_service import BlockchainService
from app.database import get_db
from app.models import House, Allocation, MonthlyBill, GenerationRecord

router = APIRouter()
logger = logging.getLogger(__name__)

blockchain_service = BlockchainService()

DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")


@router.get("/network-params")
async def get_network_params():
    """Get Algorand network parameters."""
    try:
        return blockchain_service.get_network_params()
    except Exception as e:
        logger.error(f"Network params error: {e}")
        raise HTTPException(status_code=503, detail="Algorand node unreachable")


# ─────────────────────────────────────────────
# LOCAL DB-based house history (always works)
# ─────────────────────────────────────────────

@router.get("/house-history/{house_id}")
async def get_house_history(
    house_id: str,
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    """
    Build a GPay-style transaction feed from the local database.
    Combines allocations, bills, and generation milestones.
    Always returns data regardless of Algorand indexer status.
    """
    house = db.query(House).filter(House.house_id == house_id).first()
    if not house:
        raise HTTPException(status_code=404, detail="House not found")

    txns = []

    # ── Allocations (energy bought from pool / grid) ──────────────
    allocations = (
        db.query(Allocation)
        .filter(Allocation.house_id == house.id)
        .order_by(desc(Allocation.created_at))
        .limit(limit)
        .all()
    )
    for alloc in allocations:
        is_pool = alloc.source_type == "pool"
        txn_id = alloc.transaction_hash or None
        txns.append({
            "id": f"alloc-{alloc.id}",
            "type": "allocation",
            "subtype": "pool" if is_pool else "grid",
            "title": "Solar from Pool" if is_pool else "Grid Backup",
            "subtitle": f"{alloc.allocated_kwh:.2f} kWh • {alloc.status}",
            "amount_kwh": alloc.allocated_kwh,
            "amount_sun": alloc.allocated_kwh if is_pool else 0,
            "timestamp": alloc.created_at.timestamp() if alloc.created_at else None,
            "status": alloc.status,
            "txn_id": txn_id,
            "explorer_url": f"https://testnet.explorer.perawallet.app/tx/{txn_id}" if txn_id else None,
            "note": alloc.ai_reasoning[:80] if alloc.ai_reasoning else None,
            "is_roshni": True,
        })

    # ── Monthly bills ─────────────────────────────────────────────
    bills = (
        db.query(MonthlyBill)
        .filter(MonthlyBill.house_id == house.id)
        .order_by(desc(MonthlyBill.created_at))
        .limit(20)
        .all()
    )
    for bill in bills:
        txn_id = bill.blockchain_txn or None
        txns.append({
            "id": f"bill-{bill.id}",
            "type": "bill",
            "subtype": "bill_hash",
            "title": "Bill Recorded on Chain",
            "subtitle": f"Month: {bill.month_year} • Net ₹{bill.net_payable:.0f}",
            "amount_kwh": bill.pool_bought_kwh,
            "amount_sun": bill.sun_asa_minted,
            "timestamp": bill.created_at.timestamp() if bill.created_at else None,
            "status": bill.status,
            "txn_id": txn_id,
            "explorer_url": f"https://testnet.explorer.perawallet.app/tx/{txn_id}" if txn_id else None,
            "note": f"ROSHNI|{house_id}|{bill.month_year}|{bill.bill_hash[:16]}..." if bill.bill_hash else None,
            "is_roshni": True,
            "net_payable": bill.net_payable,
            "month_year": bill.month_year,
        })

    # ── Sort all by timestamp descending ─────────────────────────
    txns.sort(key=lambda x: x.get("timestamp") or 0, reverse=True)

    # ── Summary stats ─────────────────────────────────────────────
    total_pool_kwh = sum(t["amount_kwh"] for t in txns if t["subtype"] == "pool")
    total_sun = sum(t["amount_sun"] for t in txns if t["amount_sun"])
    total_grid_kwh = sum(t["amount_kwh"] for t in txns if t["subtype"] == "grid")

    return {
        "status": "ok",
        "house_id": house_id,
        "algorand_address": house.algorand_address,
        "total": len(txns),
        "summary": {
            "total_pool_kwh": round(total_pool_kwh, 2),
            "total_sun_earned": round(total_sun, 2),
            "total_grid_kwh": round(total_grid_kwh, 2),
        },
        "transactions": txns[:limit],
    }


# ─────────────────────────────────────────────
# INDEXER — transaction history
# ─────────────────────────────────────────────

@router.get("/indexer/history/{address}")
async def get_transaction_history(
    address: str,
    limit: int = Query(default=50, ge=1, le=200),
):
    """
    Fetch full transaction history for an Algorand address.
    Includes SUN (axfer) and payment (pay) transactions.
    """
    if len(address) < 10:
        raise HTTPException(status_code=400, detail="Invalid Algorand address")
    result = blockchain_service.get_transaction_history(address=address, limit=limit)
    if result.get("status") == "error":
        raise HTTPException(status_code=502, detail=result.get("message", "Indexer error"))
    return result


@router.get("/indexer/sun-transfers/{address}")
async def get_sun_transfers(
    address: str,
    start_date: str = Query(default=None),
    end_date: str = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
):
    """
    Fetch SUN ASA transfer history for an address.
    Optionally filter by date range (YYYY-MM-DD).
    """
    if len(address) < 10:
        raise HTTPException(status_code=400, detail="Invalid Algorand address")
    if start_date and not DATE_PATTERN.match(start_date):
        raise HTTPException(status_code=400, detail="start_date must be YYYY-MM-DD")
    if end_date and not DATE_PATTERN.match(end_date):
        raise HTTPException(status_code=400, detail="end_date must be YYYY-MM-DD")

    result = blockchain_service.get_sun_transfers(
        address=address, start_date=start_date, end_date=end_date, limit=limit
    )
    if result.get("status") == "error":
        raise HTTPException(status_code=502, detail=result.get("message", "Indexer error"))
    return result


@router.post("/sun-asa/create")
async def create_sun_asa():
    """
    Create SUN ASA (Solar Utility Note token).
    Only needs to be called once per deployment.
    """
    try:
        result = blockchain_service.create_sun_asa()
        logger.info(f"SUN ASA creation request: {result.get('status')}")
        return result
    except Exception as e:
        logger.error(f"SUN ASA create error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sun-asa/transfer")
async def transfer_sun_asa(data: ASATransferRequest, db: Session = Depends(get_db)):
    """
    Transfer SUN ASA tokens to a house.
    Represents renewable allocation certificate.
    """
    try:
        # Get house from database
        house = db.query(House).filter(House.house_id == data.house_id).first()
        if not house:
            raise HTTPException(status_code=404, detail="House not found")
        if not house.algorand_address:
            raise HTTPException(status_code=400, detail="House has no Algorand wallet")
        if not house.opt_in_sun_asa:
            raise HTTPException(status_code=400, detail="House not opted into SUN ASA")

        result = blockchain_service.transfer_sun_asa(
            recipient_address=house.algorand_address,
            amount_kwh=data.amount,
            reason=data.reason,
        )
        logger.info(f"SUN ASA transfer: {data.amount:.2f} to {data.house_id} ({house.algorand_address[:10]}...)")
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"SUN ASA transfer error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/bill-hash/submit", response_model=BillHashResponse)
async def submit_bill_hash(data: BillHashSubmit):
    """
    Submit monthly bill hash to Algorand for immutability proof.
    """
    try:
        result = blockchain_service.record_bill_hash(
            bill_hash=data.bill_hash,
            house_id=data.house_id,
            month_year=data.month_year,
        )
        tx_id = result.get("tx_id", "")
        logger.info(f"Bill hash submitted: {data.house_id}/{data.month_year} tx={tx_id}")
        return BillHashResponse(
            status=result.get("status"),
            bill_hash=data.bill_hash,
            blockchain_txn=tx_id or result.get("message", "pending"),
            explorer_url=f"https://testnet.explorer.perawallet.app/tx/{tx_id}" if tx_id else "https://testnet.explorer.perawallet.app",
            timestamp=datetime.utcnow(),
        )
    except Exception as e:
        logger.error(f"Bill hash submit error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/bill-hash/verify/{txn_id}")
async def verify_bill_hash(txn_id: str):
    """
    Verify bill hash on Algorand blockchain.
    Returns transaction details if found.
    """
    if not txn_id or len(txn_id) < 10:
        raise HTTPException(status_code=400, detail="Invalid transaction ID")

    try:
        result = blockchain_service.verify_bill_hash(txn_id)
        return result
    except Exception as e:
        logger.error(f"Bill hash verify error for {txn_id}: {e}")
        # Return a structured error instead of crashing — prevents CORS-like failures
        return {
            "status": "error",
            "txn_id": txn_id,
            "message": str(e),
            "note": None,
        }