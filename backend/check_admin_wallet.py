#!/usr/bin/env python3
"""Check admin wallet balance on Algorand testnet."""

from algosdk import account, mnemonic
from algosdk.v2client import algod
from config import settings

def check_admin_wallet():
    """Check admin wallet balance and address."""
    
    print("=" * 60)
    print("ADMIN WALLET CHECKER")
    print("=" * 60)
    
    # Get admin wallet
    if settings.algorand_admin_mnemonic:
        print("Using MNEMONIC for admin wallet")
        admin_private_key = mnemonic.to_private_key(settings.algorand_admin_mnemonic)
        admin_address = account.address_from_private_key(admin_private_key)
    elif settings.algorand_admin_private_key:
        print("Using PRIVATE KEY for admin wallet")
        admin_private_key = settings.algorand_admin_private_key
        admin_address = account.address_from_private_key(admin_private_key)
    else:
        print("❌ No admin wallet configured!")
        return

    print(f"Admin Address: {admin_address}")
    
    # Connect to Algorand
    print(f"Connecting to: {settings.algorand_node_url}")
    client = algod.AlgodClient("", settings.algorand_node_url)
    
    try:
        # Get account info
        account_info = client.account_info(admin_address)
        balance_algos = account_info.get("amount") / 1_000_000
        
        print(f"✅ Balance: {balance_algos:.6f} Algo")
        print(f"   Microalgos: {account_info.get('amount')}")
        
        # Check if can fund 10 wallets (2 Algo each)
        needed = 10 * 2.0
        if balance_algos >= needed:
            print(f"✅ Can fund {int(balance_algos / 2.0)} wallets (need {needed} Algos for 10)")
        else:
            print(f"⚠️  Can only fund {int(balance_algos / 2.0)} wallets (need {needed} Algos for 10)")
            
    except Exception as e:
        print(f"❌ Error checking wallet: {e}")

if __name__ == "__main__":
    check_admin_wallet()
