"""
Algorand configuration and initialization for ROSHNI.
Handles SUN ASA and blockchain operations.
"""
from algosdk import account, mnemonic
from algosdk.v2client import algod, indexer
from algosdk.transaction import ApplicationCreateTxn, PaymentTxn
import os

class AlgorandConfig:
    """Algorand network and account configuration."""
    
    def __init__(self, network="testnet"):
        self.network = network
        
        if network == "testnet":
            self.node_url = "https://testnet-api.algonode.cloud"
            self.indexer_url = "https://testnet-idx.algonode.cloud"
            self.network_name = "Algorand Testnet"
        elif network == "mainnet":
            self.node_url = "https://mainnet-api.algonode.cloud"
            self.indexer_url = "https://mainnet-idx.algonode.cloud"
            self.network_name = "Algorand Mainnet"
        else:
            raise ValueError(f"Unknown network: {network}")
        
        # Initialize clients
        self.algod_client = algod.AlgodClient("", self.node_url)
        self.indexer_client = indexer.IndexerClient("", self.indexer_url)
    
    def create_admin_account(self):
        """Generate new Algorand account for admin."""
        private_key, address = account.generate_account()
        mnem = mnemonic.from_private_key(private_key)
        
        return {
            "address": address,
            "private_key": private_key,
            "mnemonic": mnem,
        }
    
    def get_account_from_mnemonic(self, mnem):
        """Recover account from 25-word mnemonic."""
        private_key = mnemonic.to_private_key(mnem)
        address = account.address_from_private_key(private_key)
        
        return {
            "address": address,
            "private_key": private_key,
        }
    
    def get_account_info(self, address):
        """Get account balance and asset holdings."""
        try:
            account_info = self.algod_client.account_info(address)
            return {
                "amount": account_info.get("amount"),  # microAlgos
                "assets": account_info.get("assets", []),
                "created_assets": account_info.get("created-assets", []),
                "status": "active",
            }
        except Exception as e:
            return {
                "status": "error",
                "message": str(e),
            }
    
    def suggest_params(self):
        """Get current network suggested parameters."""
        return self.algod_client.suggested_params()