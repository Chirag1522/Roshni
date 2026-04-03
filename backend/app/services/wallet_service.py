"""
Custodial Wallet Service for ROSHNI
Manages wallet lifecycle: creation, opt-in, fund tracking.
IMPORTANT: This is DEMO custodial management. For production use HSM/AWS KMS.
"""

import logging
import base64
from algosdk import account, mnemonic
from algosdk.v2client import algod
from algosdk.transaction import PaymentTxn, wait_for_confirmation
from config import settings

logger = logging.getLogger(__name__)


class CustodialWalletService:
    """Manage custodial wallets for houses (DEMO ONLY)."""

    def __init__(self):
        """Initialize Algorand client."""
        self.algod_client = algod.AlgodClient("", settings.algorand_node_url)

    def fund_wallet(self, recipient_address: str, amount_algos: float = 0.1) -> dict:
        """
        Fund a new wallet with Algo to pay transaction fees.
        Uses admin wallet (from mnemonic or private key) to send funds.
        amount_algos: Amount in Algos (default 0.1 = 100,000 microAlgos)
        """
        try:
            logger.info(f"Starting wallet funding: {recipient_address[:10]}... with {amount_algos} Algo")

            # Get admin wallet credentials
            admin_address = None
            admin_private_key = None

            if settings.algorand_admin_mnemonic:
                logger.debug("Using admin mnemonic for funding")
                admin_private_key = mnemonic.to_private_key(settings.algorand_admin_mnemonic)
                admin_address = account.address_from_private_key(admin_private_key)
            elif settings.algorand_admin_private_key:
                logger.debug("Using admin private key for funding")
                admin_private_key = settings.algorand_admin_private_key
                admin_address = account.address_from_private_key(admin_private_key)
            else:
                logger.warning("No admin wallet configured - skipping wallet funding")
                return {
                    "status": "warning",
                    "message": "Admin wallet not configured. New wallet needs manual funding.",
                }

            logger.info(f"Admin wallet: {admin_address[:10]}...")

            # Get suggested parameters
            params = self.algod_client.suggested_params()
            logger.debug(f"Got Algorand params, fee: {params.flat_fee} microAlgos")

            # Create payment transaction
            amount_microalgos = int(amount_algos * 1_000_000)
            logger.debug(f"Creating payment transaction: {amount_microalgos} microAlgos")

            txn = PaymentTxn(
                sender=admin_address,
                receiver=recipient_address,
                amt=amount_microalgos,
                sp=params,
            )

            # Sign and submit
            logger.debug("Signing transaction with admin wallet")
            signed_txn = txn.sign(admin_private_key)

            logger.debug("Submitting transaction to network")
            txid = self.algod_client.send_transaction(signed_txn)
            logger.info(f"Transaction submitted: {txid}")

            # Wait for confirmation
            logger.debug("Waiting for confirmation...")
            result = wait_for_confirmation(self.algod_client, txid, 4)
            logger.info(f"Transaction confirmed in round {result.get('confirmed-round')}")

            logger.info(
                f"Funded wallet {recipient_address[:10]}... with {amount_algos} Algo (TX: {txid})"
            )

            return {
                "status": "success",
                "txid": txid,
                "amount_algos": amount_algos,
                "message": f"Wallet funded with {amount_algos} Algo",
            }

        except Exception as e:
            logger.error(f"Wallet funding error: {str(e)}", exc_info=True)
            return {
                "status": "error",
                "message": str(e),
            }

    def create_house_wallet(self) -> dict:
        """
        Create a new Algorand wallet for a house.
        Returns address and private key.

        CRITICAL: Private keys are stored in database for DEMO.
        PRODUCTION: Use AWS KMS, Hashicorp Vault, or hardware wallet.
        """
        try:
            # Generate new account - algosdk returns private key as BASE64
            private_key, address = account.generate_account()

            logger.info(f"Wallet created: {address[:10]}...")

            return {
                "status": "success",
                "algorand_address": address,
                "algorand_private_key": private_key,  # Store as-is (already BASE64 from algosdk)
                "message": "Custodial wallet created. Private key managed by backend.",
            }

        except Exception as e:
            logger.error(f"Wallet creation error: {str(e)}")
            return {
                "status": "error",
                "message": str(e),
            }

    def opt_in_to_sun_asa(
        self,
        algorand_address: str,
        algorand_private_key: str,
    ) -> dict:
        """
        Opt-in house wallet to SUN ASA token.
        Must be done before receiving SUN tokens.

        Transaction: Zero-amount transfer from self to self with asset index.
        """
        try:
            from algosdk.transaction import AssetTransferTxn, wait_for_confirmation

            # Private key is already in correct format from database
            params = self.algod_client.suggested_params()

            logger.debug(f"Opting in to SUN ASA ID: {settings.sun_asa_id} for {algorand_address[:10]}...")

            # Create zero-amount asset transfer (opt-in)
            txn = AssetTransferTxn(
                sender=algorand_address,
                sp=params,
                receiver=algorand_address,
                amt=0,  # Zero amount = opt-in
                index=settings.sun_asa_id,
            )

            # Sign transaction
            signed_txn = txn.sign(algorand_private_key)

            # Submit transaction
            txid = self.algod_client.send_transaction(signed_txn)

            # Wait for confirmation
            result = wait_for_confirmation(self.algod_client, txid, 4)

            logger.info(
                f"Opted in to SUN ASA: {algorand_address[:10]}... (TX: {txid})"
            )

            return {
                "status": "success",
                "txid": txid,
                "round": result["confirmed-round"],
                "message": f"Successfully opted into SUN ASA",
            }

        except Exception as e:
            logger.error(f"Opt-in error for {algorand_address[:10]}...: {str(e)}")
            return {
                "status": "error",
                "message": str(e),
            }

    def get_wallet_info(self, algorand_address: str) -> dict:
        """Get wallet account information including ASA balance."""
        try:
            account_info = self.algod_client.account_info(algorand_address)

            # Extract SUN ASA balance if exists
            sun_balance = 0
            if "assets" in account_info:
                for asset in account_info["assets"]:
                    if asset["asset-id"] == settings.sun_asa_id:
                        sun_balance = asset["amount"]
                        break

            return {
                "status": "success",
                "address": algorand_address,
                "amount": account_info.get("amount") / 1_000_000,  # μAlgos to Algos
                "sun_asa_balance": sun_balance,
                "created_at": account_info.get("created-at-round"),
            }

        except Exception as e:
            logger.error(f"Wallet info error: {str(e)}")
            return {
                "status": "error",
                "message": str(e),
            }

    def get_explorer_url(self, address: str) -> str:
        """Get Algoexplorer/Dappflow link for wallet."""
        if settings.algorand_network == "testnet":
            # Use Dappflow as it's more reliable than testnet.algoexplorer.io
            return f"https://dappflow.org/explore/accounts/{address}/overview"
        else:
            return f"https://algoexplorer.io/address/{address}"


# Singleton instance
wallet_service = CustodialWalletService()
