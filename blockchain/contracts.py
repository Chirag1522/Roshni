"""
ROSHNI Smart Contracts (Algorand Application Smart Contracts).
For production, implement more complex contracts with TEAL.
"""

class RoshniContracts:
    """ROSHNI smart contracts on Algorand."""

    # ================= SUN ASA CREATION =================

    @staticmethod
    def get_sun_asa_init_txn(creator_address, suggested_params):
        """
        Create SUN ASA initialization transaction.

        SUN ASA:
        - 1 token = 1 kWh renewable allocation certificate
        - Total supply: 1 billion tokens
        - Decimals: 0 (whole tokens only)
        """

        from algosdk.transaction import AssetConfigTxn

        txn = AssetConfigTxn(
            sender=creator_address,
            sp=suggested_params,
            total=1_000_000_000,  # 1 billion supply
            decimals=0,
            default_frozen=False,
            unit_name="SUN",
            asset_name="Solar Utility Note",
            manager=creator_address,
            reserve=creator_address,
            freeze=creator_address,
            clawback=creator_address,
            url="https://roshni.renewable.local/sun",
            metadata_hash=None,
        )

        return txn

    # ================= BILL HASH RECORDING =================

    @staticmethod
    def get_bill_hash_note_txn(creator_address, bill_data, suggested_params):
        """
        Create bill hash recording transaction.
        Uses the note field to store immutable bill data.
        """

        from algosdk.transaction import PaymentTxn

        # Format:
        # ROSHNI_BILL|house_id|month_year|bill_hash
        note = (
            f"ROSHNI_BILL|"
            f"{bill_data['house_id']}|"
            f"{bill_data['month_year']}|"
            f"{bill_data['bill_hash']}"
        ).encode()

        txn = PaymentTxn(
            sender=creator_address,
            sp=suggested_params,
            receiver=creator_address,  # self-payment
            amt=0,  # zero ALGO transfer
            note=note,
        )

        return txn

    # ================= ASA TRANSFER =================

    @staticmethod
    def get_asa_transfer_txn(sender, receiver, asa_id, amount, suggested_params):
        """
        Create SUN ASA transfer transaction.
        1 SUN = 1 kWh renewable certificate.
        """

        from algosdk.transaction import AssetTransferTxn

        txn = AssetTransferTxn(
            sender=sender,
            sp=suggested_params,
            index=asa_id,
            amt=int(amount),
            receiver=receiver,
        )

        return txn

    # ================= ASA OPT-IN =================

    @staticmethod
    def get_asa_optin_txn(address, asa_id, suggested_params):
        """
        Create ASA opt-in transaction.
        Required before receiving SUN tokens.
        """

        from algosdk.transaction import AssetTransferTxn

        txn = AssetTransferTxn(
            sender=address,
            sp=suggested_params,
            index=asa_id,
            amt=0,
            receiver=address,
        )

        return txn