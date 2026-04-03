"""
Wallet Registration & Initialization Endpoints
Handles custodial wallet lifecycle for houses.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
import logging

from app.database import get_db
from app.models import House
from app.services.wallet_service import wallet_service
from app.services.pool_sun_service import PoolSUNService

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/{house_id}")
async def get_house_wallet(house_id: str, db: Session = Depends(get_db)):
    """
    Get wallet information and live on-chain SUN balance for a house.
    """
    house = db.query(House).filter(House.house_id == house_id).first()
    if not house:
        return {
            "status": "not_initialized",
            "house_id": house_id,
            "algorand_address": None,
            "opt_in_sun_asa": False,
            "sun_balance_on_chain": 0,
            "message": "Wallet not initialized",
        }

    if not house.algorand_address:
        return {
            "status": "not_initialized",
            "house_id": house.house_id,
            "algorand_address": None,
            "opt_in_sun_asa": False,
            "sun_balance_on_chain": 0,
            "message": "Wallet not initialized",
        }

    # Always query on-chain for live balance consistency
    wallet_info = wallet_service.get_wallet_info(house.algorand_address)

    return {
        "status": "success",
        "house_id": house.house_id,
        "algorand_address": house.algorand_address,
        "opt_in_sun_asa": house.opt_in_sun_asa,
        "sun_balance_on_chain": wallet_info.get("sun_asa_balance", 0),
        "sun_minted_this_month": house.current_month_sun_minted,
        "sun_received_this_month": house.current_month_sun_received,
        "sun_transferred_this_month": house.current_month_sun_transferred,
        "wallet_created_at": house.wallet_created_at,
        "explorer_url": wallet_service.get_explorer_url(house.algorand_address),
    }


class WalletInitRequest:
    """Request to initialize wallet for a house."""

    house_id: str


class WalletOkptInRequest:
    """Request to opt-in to SUN ASA."""

    house_id: str


@router.post("/initialize/{house_id}")
async def initialize_house_wallet(house_id: str, db: Session = Depends(get_db)):
    """
    Initialize custodial wallet for a house.
    Creates Algorand address and stores private key.
    Opt-in to SUN ASA is optional (can be done separately).
    """
    house = db.query(House).filter(House.house_id == house_id).first()
    if not house:
        raise HTTPException(status_code=404, detail="House not found")

    if house.algorand_address:
        return {
            "status": "already_initialized",
            "house_id": house.house_id,
            "algorand_address": house.algorand_address,
            "opt_in_sun_asa": house.opt_in_sun_asa,
            "message": "Wallet already initialized",
        }

    # Create new custodial wallet
    wallet_result = wallet_service.create_house_wallet()

    if wallet_result.get("status") != "success":
        logger.error(f"Wallet creation failed for {house_id}: {wallet_result.get('message')}")
        raise HTTPException(status_code=500, detail=wallet_result.get("message"))

    # Fund the wallet with Algo so it can pay transaction fees
    fund_result = wallet_service.fund_wallet(wallet_result["algorand_address"], amount_algos=2.0)

    if fund_result.get("status") == "error":
        logger.error(f"Wallet funding failed for {house_id}: {fund_result.get('message')}")
        raise HTTPException(
            status_code=500,
            detail=f"Wallet created but funding failed: {fund_result.get('message')}"
        )
    elif fund_result.get("status") == "warning":
        logger.warning(f"Wallet funding skipped for {house_id}: {fund_result.get('message')}")
        # Continue anyway with warning - user will need to fund manually

    # Opt-in to SUN ASA
    opt_in_result = wallet_service.opt_in_to_sun_asa(
        algorand_address=wallet_result["algorand_address"],
        algorand_private_key=wallet_result["algorand_private_key"],
    )

    if opt_in_result.get("status") == "success":
        house.opt_in_sun_asa = True
        logger.info(f"Auto-opted into SUN ASA for {house_id}")
    else:
        logger.warning(f"SUN ASA opt-in failed for {house_id}: {opt_in_result.get('message')}")
        # Continue anyway - user can opt-in manually later

    # Store in database
    house.algorand_address = wallet_result["algorand_address"]
    house.algorand_private_key = wallet_result["algorand_private_key"]
    house.wallet_created_at = datetime.utcnow()
    db.commit()
    db.refresh(house)

    logger.info(
        f"Wallet initialized for {house.house_id}: {house.algorand_address[:10]}... (funded)"
    )

    return {
        "status": "success",
        "house_id": house.house_id,
        "algorand_address": house.algorand_address,
        "opt_in_sun_asa": house.opt_in_sun_asa,
        "explorer_url": wallet_service.get_explorer_url(house.algorand_address),
        "message": "✅ Wallet created, funded, and opted into SUN ASA! Ready to receive renewable energy tokens.",
    }


@router.post("/opt-in-sun/{house_id}")
async def opt_in_to_sun(house_id: str, db: Session = Depends(get_db)):
    """
    Opt-in house wallet to SUN ASA.
    Must be done before receiving SUN tokens.
    """
    try:
        house = db.query(House).filter(House.house_id == house_id).first()
        if not house:
            raise HTTPException(status_code=404, detail="House not found")

        if not house.algorand_address or not house.algorand_private_key:
            raise HTTPException(
                status_code=400,
                detail="House wallet must be initialized first",
            )

        if house.opt_in_sun_asa:
            return {
                "status": "already_opted_in",
                "house_id": house.house_id,
                "message": "Already opted into SUN ASA",
            }

        # Opt-in via blockchain service
        opt_in_result = wallet_service.opt_in_to_sun_asa(
            house.algorand_address,
            house.algorand_private_key,
        )

        if opt_in_result.get("status") != "success":
            error_msg = opt_in_result.get("message", "Unknown opt-in error")
            logger.error(f"Opt-in failed for {house_id}: {error_msg}")
            raise HTTPException(
                status_code=500,
                detail=f"Opt-in failed: {error_msg}",
            )

        # Update house record
        house.opt_in_sun_asa = True
        db.commit()
        db.refresh(house)

        logger.info(f"Opted into SUN ASA: {house.house_id}")

        return {
            "status": "success",
            "house_id": house.house_id,
            "opt_in_tx_id": opt_in_result["txid"],
            "explorer_url": wallet_service.get_explorer_url(house.algorand_address),
            "message": "Successfully opted into SUN ASA",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error during opt-in for {house_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Opt-in failed: {str(e)}",
        )



@router.post("/check-balance/{house_id}")
async def check_sun_balance(house_id: str, db: Session = Depends(get_db)):
    """Synchronize and check SUN balance from blockchain."""
    house = db.query(House).filter(House.house_id == house_id).first()
    if not house:
        raise HTTPException(status_code=404, detail="House not found")

    if not house.algorand_address:
        raise HTTPException(status_code=400, detail="House has no wallet")

    # Query on-chain
    wallet_info = wallet_service.get_wallet_info(house.algorand_address)

    if wallet_info.get("status") == "error":
        raise HTTPException(status_code=500, detail=wallet_info.get("message"))

    return {
        "status": "success",
        "house_id": house.house_id,
        "address": house.algorand_address,
        "sun_balance": wallet_info["sun_asa_balance"],
        "algo_balance": wallet_info["amount"],
    }
