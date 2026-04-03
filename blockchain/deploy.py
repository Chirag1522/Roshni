"""
SUN ASA deployment script.
Run this once to deploy SUN token on Algorand.
Uses PRIVATE KEY directly (Base64 string).
"""

import sys
import json
from algosdk import account
from algosdk.transaction import wait_for_confirmation
from algorand_config import AlgorandConfig
from contracts import RoshniContracts


def deploy_sun_asa(admin_private_key, network="testnet"):

    print(f"🌞 Deploying SUN ASA on {network.upper()}...")

    config = AlgorandConfig(network)

    # DO NOT decode the key
    try:
        admin_address = account.address_from_private_key(admin_private_key)
    except Exception as e:
        print(f"❌ Invalid private key: {e}")
        sys.exit(1)

    print(f"Admin: {admin_address}")

    # Check balance
    account_info = config.get_account_info(admin_address)
    balance_algos = account_info.get("amount", 0) / 1_000_000
    print(f"Balance: {balance_algos:.2f} ALGO")

    if balance_algos < 1:
        print("❌ Insufficient balance (need at least 1 ALGO)")
        return {"status": "failed"}

    # Suggested params
    sp = config.suggest_params()

    # Create SUN ASA transaction
    txn = RoshniContracts.get_sun_asa_init_txn(admin_address, sp)

    # SIGN WITH BASE64 STRING DIRECTLY
    signed_txn = txn.sign(admin_private_key)

    try:
        txid = config.algod_client.send_transaction(signed_txn)
        print(f"Transaction sent: {txid}")

        print("Waiting for confirmation...")
        confirmed_txn = wait_for_confirmation(config.algod_client, txid, 4)

        asa_id = confirmed_txn["asset-index"]

        print("✅ SUN ASA deployed!")
        print(f"ASA ID: {asa_id}")
        print(f"Explorer: https://{network}.algoexplorer.io/asset/{asa_id}")

        return {
            "status": "deployed",
            "asa_id": asa_id,
            "transaction_id": txid,
            "explorer_url": f"https://{network}.algoexplorer.io/asset/{asa_id}",
        }

    except Exception as e:
        print(f"❌ Deployment failed: {e}")
        return {"status": "failed", "error": str(e)}


if __name__ == "__main__":

    if len(sys.argv) < 2:
        print("Usage: python deploy.py '<BASE64_PRIVATE_KEY>'")
        sys.exit(1)

    admin_private_key = sys.argv[1]

    result = deploy_sun_asa(admin_private_key, "testnet")

    print("\n" + "=" * 50)
    print(json.dumps(result, indent=2))
    print("=" * 50)