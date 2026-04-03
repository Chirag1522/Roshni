"""
SUN ASA Pool Management Service
Handles minting on surplus and transferring during allocations.
Blockchain = source of truth for renewable allocation.
"""

import logging
from datetime import datetime
from sqlalchemy.orm import Session
from algosdk.transaction import AssetTransferTxn, wait_for_confirmation
from algosdk.v2client import algod

from config import settings
from app.models import House, GenerationRecord, DemandRecord, Allocation
from app.services.blockchain_service import BlockchainService

logger = logging.getLogger(__name__)


class PoolSUNService:
    """Manage SUN ASA minting and transfers for feeder pools."""

    def __init__(self, db: Session):
        self.db = db
        self.algod_client = algod.AlgodClient("", settings.algorand_node_url)
        self.blockchain_service = BlockchainService()
        self.sun_asa_id = settings.sun_asa_id
        self.admin_address = self.blockchain_service.admin_public_key
        self.admin_private_key = self.blockchain_service.admin_private_key

    def calculate_daily_surplus(self, house_id: int) -> dict:
        """
        Calculate surplus generation for a house today.
        Surplus = generation - consumption.
        If surplus > 0, eligible for SUN minting.
        """
        house = self.db.query(House).filter(House.id == house_id).first()
        if not house:
            return {"status": "error", "message": "House not found"}

        # Today's generation
        today_generation = self.db.query(GenerationRecord).filter(
            GenerationRecord.house_id == house_id,
            GenerationRecord.created_at >= datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0),
        ).all()

        total_generation = sum(g.generation_kwh for g in today_generation)

        # Today's consumption/demand
        today_demand = self.db.query(DemandRecord).filter(
            DemandRecord.house_id == house_id,
            DemandRecord.created_at >= datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0),
            DemandRecord.status == "fulfilled",
        ).all()

        total_consumption = sum(d.demand_kwh for d in today_demand)

        surplus = max(0, total_generation - total_consumption)

        return {
            "status": "success",
            "house_id": house.house_id,
            "generation_kwh": total_generation,
            "consumption_kwh": total_consumption,
            "surplus_kwh": surplus,
            "eligible_for_sun": surplus > 0,
        }

    def mint_sun_for_surplus(
        self,
        house_id: int,
        surplus_kwh: float,
        reason: str = "daily_surplus",
    ) -> dict:
        """
        Mint SUN tokens to house wallet for surplus generation.
        Only mimes if wallet is opted in and surplus > 0.

        Transaction: Admin sends SUN to house address.
        """
        if surplus_kwh <= 0:
            return {
                "status": "error",
                "message": "Surplus must be positive",
            }

        house = self.db.query(House).filter(House.id == house_id).first()
        if not house:
            return {"status": "error", "message": "House not found"}

        if not house.algorand_address:
            return {
                "status": "error",
                "message": f"House {house.house_id} has no Algorand wallet",
            }

        if not house.opt_in_sun_asa:
            return {
                "status": "error",
                "message": f"House {house.house_id} not opted into SUN ASA",
            }

        try:
            params = self.algod_client.suggested_params()

            # Admin transfers SUN to house address
            txn = AssetTransferTxn(
                sender=self.admin_address,
                sp=params,
                receiver=house.algorand_address,
                amt=int(surplus_kwh),  # 1 SUN = 1 kWh
                index=self.sun_asa_id,
            )

            signed_txn = txn.sign(self.admin_private_key)
            txid = self.algod_client.send_transaction(signed_txn)

            result = wait_for_confirmation(self.algod_client, txid, 4)

            # Update house record
            house.current_month_sun_minted += surplus_kwh
            self.db.commit()

            logger.info(
                f"SUN minted: {surplus_kwh} to {house.house_id} "
                f"({house.algorand_address[:10]}...) TX: {txid}"
            )

            return {
                "status": "success",
                "txid": txid,
                "house_id": house.house_id,
                "sun_minted": surplus_kwh,
                "reason": reason,
                "round": result["confirmed-round"],
            }

        except Exception as e:
            logger.error(f"SUN mint error: {str(e)}")
            return {
                "status": "error",
                "message": str(e),
            }

    def transfer_sun_during_allocation(
        self,
        from_house_id: int,
        to_house_id: int,
        amount_kwh: float,
    ) -> dict:
        """
        Transfer SUN tokens from seller to buyer during pool allocation.

        Normal flow:
        1. Buyer requests energy
        2. Matching engine finds seller with SUN balance
        3. Transfer via direct transaction (seller signs)
        4. Allocation recorded on-chain

        SIMPLIFIED: Admin facilitates transfer (DEMO).
        """
        if amount_kwh <= 0:
            return {"status": "error", "message": "Amount must be positive"}

        from_house = self.db.query(House).filter(House.id == from_house_id).first()
        to_house = self.db.query(House).filter(House.id == to_house_id).first()

        if not from_house or not to_house:
            return {"status": "error", "message": "House not found"}

        if not from_house.algorand_address or not to_house.algorand_address:
            return {"status": "error", "message": "One or both houses missing wallet"}

        # Verify sender has balance (check on-chain)
        sender_wallet = self.blockchain_service.get_wallet_info(from_house.algorand_address)
        if sender_wallet.get("sun_asa_balance", 0) < amount_kwh:
            return {
                "status": "error",
                "message": f"{from_house.house_id} insufficient SUN balance",
            }

        try:
            params = self.algod_client.suggested_params()

            # Sender transfers SUN to buyer
            txn = AssetTransferTxn(
                sender=from_house.algorand_address,
                sp=params,
                receiver=to_house.algorand_address,
                amt=int(amount_kwh),
                index=self.sun_asa_id,
            )

            # Sign with sender's private key (demo: admin signs)
            signed_txn = txn.sign(from_house.algorand_private_key)
            txid = self.algod_client.send_transaction(signed_txn)

            result = wait_for_confirmation(self.algod_client, txid, 4)

            # Update house records
            from_house.current_month_sun_transferred += amount_kwh
            to_house.current_month_sun_received += amount_kwh
            self.db.commit()

            logger.info(
                f"SUN transferred: {amount_kwh} from {from_house.house_id} "
                f"to {to_house.house_id} TX: {txid}"
            )

            return {
                "status": "success",
                "txid": txid,
                "from": from_house.house_id,
                "to": to_house.house_id,
                "amount": amount_kwh,
                "round": result["confirmed-round"],
            }

        except Exception as e:
            logger.error(f"SUN transfer error: {str(e)}")
            return {
                "status": "error",
                "message": str(e),
            }

    def get_sun_balance(self, house_id: int) -> dict:
        """Get SUN ASA balance for a house."""
        house = self.db.query(House).filter(House.id == house_id).first()
        if not house or not house.algorand_address:
            return {"status": "error", "message": "House not found or no wallet"}

        wallet_info = self.blockchain_service.get_wallet_info(
            house.algorand_address
        )

        if wallet_info.get("status") == "error":
            return wallet_info

        return {
            "status": "success",
            "house_id": house.house_id,
            "algorand_address": house.algorand_address,
            "sun_balance": wallet_info.get("sun_asa_balance", 0),
            "minted_this_month": house.current_month_sun_minted,
            "transferred_this_month": house.current_month_sun_transferred,
            "received_this_month": house.current_month_sun_received,
        }
