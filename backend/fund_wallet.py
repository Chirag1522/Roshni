#!/usr/bin/env python3
"""Fund an existing house wallet from admin wallet."""

import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models import House
from app.services.wallet_service import wallet_service
from config import settings

def fund_house_wallet(house_id: str):
    """Fund a specific house wallet with 2 Algos."""

    # Connect to database
    engine = create_engine(settings.database_url)
    Session = sessionmaker(bind=engine)
    db = Session()

    try:
        # Get the house
        house = db.query(House).filter(House.house_id == house_id).first()

        if not house:
            print(f"❌ House {house_id} not found")
            return False

        if not house.algorand_address:
            print(f"❌ House {house_id} has no wallet address")
            return False

        print(f"📍 Found house: {house.house_id}")
        print(f"📍 Wallet address: {house.algorand_address}")

        # Check current balance
        wallet_info = wallet_service.get_wallet_info(house.algorand_address)
        current_balance = wallet_info.get("amount", 0) if wallet_info.get("status") == "success" else 0
        print(f"💰 Current balance: {current_balance} Algo")

        # Fund the wallet
        print(f"\n🔄 Funding wallet with 2.0 Algo...")
        fund_result = wallet_service.fund_wallet(house.algorand_address, amount_algos=2.0)

        if fund_result.get("status") == "success":
            print(f"✅ Funding succeeded!")
            print(f"   Transaction ID: {fund_result.get('txid')}")
            print(f"   Amount: {fund_result.get('amount_algos')} Algo")

            # Check new balance
            import time
            time.sleep(2)
            wallet_info = wallet_service.get_wallet_info(house.algorand_address)
            new_balance = wallet_info.get("amount", 0) if wallet_info.get("status") == "success" else 0
            print(f"💰 New balance: {new_balance} Algo")

            return True
        else:
            print(f"❌ Funding failed: {fund_result.get('message')}")
            return False

    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    finally:
        db.close()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python fund_wallet.py <HOUSE_ID>")
        print("Example: python fund_wallet.py HOUSE_FDR12_001")
        sys.exit(1)

    house_id = sys.argv[1]
    success = fund_house_wallet(house_id)
    sys.exit(0 if success else 1)
