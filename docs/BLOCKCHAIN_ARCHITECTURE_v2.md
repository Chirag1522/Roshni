## ROSHNI v2: Custodial-Wallet Blockchain Architecture

### Complete Implementation Guide

---

## 1. ARCHITECTURE OVERVIEW

### Problem Fixed

- ✅ **NO MORE**: SUN tokens minted but never sent
- ✅ **NOW**: Each house has a custodial wallet managed by backend
- ✅ **NOW**: SUN tokens actually transferred between prosumers
- ✅ **NOW**: Blockchain is source-of-truth for renewable allocations

### System Model

```
┌──────────────────────────────────────────────────────┐
│                    ROSHNI v2                          │
├──────────────────────────────────────────────────────┤
│                                                       │
│  PROSUMERS (with custodial wallets)                  │
│  ├─ House A: generates 5 kWh → surplus 3 kWh        │
│  ├─ House B: generates 2 kWh → surplus 0 kWh        │
│  └─ House C: consumes 4 kWh → deficit 4 kWh         │
│                ↓                                      │
│  POOL ENGINE (Feeder-level matching)                 │
│  ├─ Supply: 3 kWh from House A                       │
│  ├─ Demand: 4 kWh from House C                       │
│  ├─ Allocation: 3 kWh pool, 1 kWh grid              │
│  └─ BlockchainTX: Transfer SUN_A → SUN_C            │
│                ↓                                      │
│  BLOCKCHAIN (Algorand TestNet)                       │
│  ├─ SUN ASA mints 3 tokens to House A               │
│  ├─ Transfer 3 SUN from A → C via atomic tx         │
│  └─ Bill hash recorded on chain (immutable)         │
│                ↓                                      │
│  DISCOM BILLING (INR financial authority)            │
│  ├─ House A earns: ₹27 (3 kWh × ₹9/kWh)            │
│  ├─ House C pays: ₹39 (3×₹9 + 1×₹12)                │
│  └─ Net = Blockchain-backed renewable allocation    │
│                                                       │
└──────────────────────────────────────────────────────┘
```

---

## 2. KEY ENTITIES

### House Model (Updated)

```python
class House:
    house_id: str                      # HOUSE_FDR12_001
    algorand_address: str              # Custodial wallet Algo testnet
    algorand_private_key: str          # BASE64 (demo only - encrypted in prod)
    opt_in_sun_asa: bool              # Has opted into SUN ASA
    wallet_created_at: datetime

    # Monthly tracking
    current_month_generation_kwh: float
    current_month_sun_minted: float    # SUN tokens earned (1 = 1 kWh)
    current_month_sun_received: float  # SUN tokens from pool
    current_month_sun_transferred: float
```

### SUN ASA Token

```
Name:      Solar Utility Note
Symbol:    SUN
Supply:    1 billion tokens
Decimals:  0 (whole tokens only)
Network:   Algorand TestNet
Asset ID:  756341116
Formula:   1 SUN = 1 kWh renewable energy
```

---

## 3. TRANSACTION FLOWS

### FLOW 1: House Initialization & Wallet Setup

```
User registers new house
        ↓
POST /api/wallet/initialize/{house_id}
        ↓
Backend creates custodial wallet
├─ Generate Algorand account via SDK
├─ algorand_address = generated public key
├─ algorand_private_key = BASE64(private key)
├─ Store in database
└─ Return address + explorer URL
        ↓
POST /api/wallet/opt-in-sun/{house_id}
        ↓
Backend signs opt-in transaction
├─ Transaction: zero-amount asset transfer (opt-in)
├─ Signed with house's private key
├─ Submitted to Algorand TestNet
└─ House.opt_in_sun_asa = True
        ↓
SUCCESS: House ready to receive SUN tokens
```

### FLOW 2: Daily Surplus Detection & SUN Minting

```
IoT sends generation data
        ↓
Pool engine calculates daily surplus
├─ today_generation = SUM(all generation records for day)
├─ today_consumption = SUM(all fulfilled demand for day)
├─ surplus = max(0, generation - consumption)
└─ if surplus > 0: eligible for minting
        ↓
Mint SUN tokens for surplus
├─ Admin account transfers SUN to house wallet
├─ Amount = surplus_kwh (1:1 with kWh)
├─ Atomic transaction on Algorand
├─ House.current_month_sun_minted += surplus
└─ BlockchainTX recorded in Allocation table
        ↓
House A wallet: 3 SUN tokens (renewable certificates)
```

### FLOW 3: Pool Allocation & SUN Transfer

```
House C submits demand: 4 kWh
        ↓
AI Matching Engine runs
├─ Check available SUN in pool (House A has 3 SUN)
├─ Decision: allocate 3 SUN to C, 1 kWh grid
└─ Return allocation with reasoning
        ↓
Transfer SUN: House A → House C
├─ Sender: House A (algorand_address_A)
├─ Receiver: House C (algorand_address_C)
├─ Amount: 3 SUN tokens
├─ Signed by House A's private key
├─ Atomic transaction on Algorand
├─ House A.current_month_sun_transferred += 3
├─ House C.current_month_sun_received += 3
└─ Allocation.transaction_hash = blockchain_txid
        ↓
RESULT:
├─ House C receives 3 SUN (renewable allocation proof)
├─ House C pays: ₹27 (pool) + ₹12 (grid) = ₹39
├─ House A earns: ₹27 (from C) + DISCOM export credit
└─ All recorded on immutable Algorand
```

### FLOW 4: Monthly Bill Generation & Blockchain Recording

```
Month end (28/29/30/31)
        ↓
GET /api/billing/generate/{house_id}/{month_year}
        ↓
Backend aggregates month's data
├─ solar_generated_kwh = SUM(all generation)
├─ sun_minted = SUM(current_month_sun_minted)
├─ sun_received = SUM(current_month_sun_received)
├─ pool_bought_kwh = SUM(pool allocations received)
├─ pool_sold_kwh = SUM(pool allocations sent)
├─ grid_bought_kwh = SUM(grid fallback)
└─ Calculate credits/charges (INR)
        ↓
Create bill JSON with complete data
├─ house_id, month_year, all metrics
├─ all credits and charges
└─ net_payable (negative = credit)
        ↓
Hash bill on blockchain
├─ SHA256(bill_JSON)
├─ Record via zero-ALGO self-payment transaction
├─ Note field: "ROSHNI|HOUSE_FDR12_001|2024-03|hash"
└─ Bill.blockchain_txn = Algorand txid
        ↓
RESULT:
├─ Bill immutable proof on public Algorand
├─ User can verify via GET /api/blockchain/bill-hash/verify/{txid}
└─ DISCOM has complete audit trail
```

---

## 4. API ENDPOINTS (Wallet Lifecycle)

### Initialize Wallet

```
POST /api/wallet/initialize/{house_id}

Response:
{
  "status": "success",
  "house_id": "HOUSE_FDR12_001",
  "algorand_address": "PLJXQBK77XQJDKBK7BTZBL2C4SWVWMUZRM5PKYJNLJFVYPVMVVTPQGTVJI",
  "explorer_url": "https://testnet.algoexplorer.io/address/PLJ..."
}
```

### Opt-in to SUN ASA

```
POST /api/wallet/opt-in-sun/{house_id}

Response:
{
  "status": "success",
  "house_id": "HOUSE_FDR12_001",
  "txid": "ABC123...",
  "round": 34567890,
  "message": "Successfully opted into SUN ASA"
}
```

### Check Wallet Status

```
GET /api/wallet/{house_id}

Response:
{
  "status": "success",
  "house_id": "HOUSE_FDR12_001",
  "algorand_address": "PLJ...",
  "opt_in_sun_asa": true,
  "sun_balance_on_chain": 3.0,
  "sun_minted_this_month": 3.0,
  "sun_received_this_month": 1.5,
  "sun_transferred_this_month": 2.0,
  "explorer_url": "https://testnet.algoexplorer.io/address/PLJ..."
}
```

### Check On-Chain Balance

```
POST /api/wallet/check-balance/{house_id}

Response:
{
  "status": "success",
  "house_id": "HOUSE_FDR12_001",
  "address": "PLJ...",
  "sun_balance": 3.0,
  "algo_balance": 0.5  (microAlgos for fees)
}
```

---

## 5. ADMIN DASHBOARD ENDPOINTS

### Feeder Daily Summary

```
GET /api/admin/dashboard/feeder/FDR_12/daily

Response:
{
  "feeder_code": "FDR_12",
  "date": "2024-03-15",
  "metrics": {
    "total_generation_kwh": 125.5,
    "total_demand_kwh": 98.3,
    "pool_allocated_kwh": 85.2,
    "grid_fallback_kwh": 13.1,
    "surplus_kwh": 27.2
  },
  "houses": {
    "total": 50,
    "active": 48,
    "with_wallet": 45,
    "opted_in_sun": 42
  }
}
```

### Feeder Monthly Summary

```
GET /api/admin/dashboard/feeder/FDR_12/monthly

Response:
{
  "feeder_code": "FDR_12",
  "month_year": "2024-03",
  "energy_metrics": {...},
  "financial": {
    "revenue": {
      "solar_export_credit_inr": 1250.00,
      "pool_sales_credit_inr": 3870.00,
      "total_revenue_inr": 5120.00
    },
    "costs": {
      "pool_purchase_charge_inr": 450.00,
      "grid_purchase_charge_inr": 1575.00,
      "discom_fixed_and_admin_fee_inr": 280.00,
      "total_costs_inr": 2305.00
    },
    "net_revenue_inr": 2815.00
  },
  "blockchain": {
    "sun_tokens_minted": 850,
    "bills_recorded_on_chain": 42
  }
}
```

### All Feeders Summary

```
GET /api/admin/dashboard/all-feeders

Response:
{
  "total_feeders": 12,
  "feeders": [
    {
      "feeder_code": "FDR_12",
      "location": "North District",
      "total_capacity_kw": 1000.0,
      "houses": {
        "total": 50,
        "active": 48,
        "with_wallet": 45,
        "opted_in_sun": 42,
        "deployment_percent": 84.0
      }
    },
    ...
  ]
}
```

---

## 6. LOCAL INSTALLATION & RUN

### Prerequisites

```bash
Python 3.10+
PostgreSQL 13+
Algorand TestNet access (infra: algonode.com)
```

### Step 1: Setup Backend

```bash
cd /home/khushi/roshni/backend

# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create .env file
cat > .env << 'EOF'
# Environment
ENVIRONMENT=development
DEBUG=True

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/roshni

# Algorand
ALGORAND_NETWORK=testnet
ALGORAND_NODE_URL=https://testnet-api.algonode.cloud
ALGORAND_INDEXER_URL=https://testnet-idx.algonode.cloud

# Admin Account (get from creating wallet below)
ALGORAND_ADMIN_PRIVATE_KEY=ev2HdnJROUQ5NrhFBKmomyR+9FZ2GyU7VdxmlLvXW1l7L2WYh2YjGJavV8zhU7M1SXoF+Fz3cHEuCIYeZHST9g==
SUN_ASA_ID=756341116

# Gemini API
GEMINI_API_KEY=your_gemini_api_key

# Settings
SOLAR_POOL_RATE_INR=9.0
DISCOM_GRID_RATE_INR=12.0
DISCOM_EXPORT_RATE_INR=8.0
DISCOM_FIXED_CHARGE_INR=100.0
DISCOM_ADMIN_FEE_PERCENT=2.0

# CORS
CORS_ORIGINS=["http://localhost:5173","http://localhost:3000"]
EOF

# Initialize database
python -c "from app.database import init_db; init_db()"

# Run backend
uvicorn main:app --reload --port 8000
```

### Step 2: Create Admin Algorand Wallet

```bash
# Generate new admin wallet
python << 'EOF'
from algosdk import account, mnemonic
import base64

# Generate account
private_key, address = account.generate_account()

print(f"Public Address: {address}")
print(f"Private Key (BASE64):")
print(base64.b64encode(base64.b64decode(private_key)).decode())
print(f"Mnemonic:")
print(mnemonic.from_private_key(private_key))
EOF

# Fund admin wallet from testnet faucet
# Go to: https://bank.testnet.algorand.org/
# Paste the public address and request 10 Algos
```

### Step 3: Create SUN ASA Token

```bash
# Deploy SUN ASA (one-time)
python blockchain/deploy.py 'BASE64_ENCODED_ADMIN_PRIVATE_KEY'

# Note the ASA ID returned
# Update .env: SUN_ASA_ID=123456789
```

### Step 4: Setup Frontend

```bash
cd /home/khushi/roshni/frontend

# Create .env
cat > .env.local << 'EOF'
VITE_BACKEND_URL=http://localhost:8000
VITE_ELEVENLABS_API_KEY=your_key
EOF

# Install and run
npm install
npm run dev

# Access: http://localhost:5173
```

---

## 7. LOCAL DEMO SCENARIO

### Scenario: 2-House Pool (Seller + Buyer)

#### House A (Seller):

- Prosumer type: generator
- Installed solar: 10 kW
- Monthly consumption: 150 kWh

#### House B (Buyer):

- Prosumer type: consumer
- Monthly consumption: 500 kWh

### Demo Steps

#### 1. Initialize Wallets

```bash
curl -X POST http://localhost:8000/api/wallet/initialize/HOUSE_FDR12_001
curl -X POST http://localhost:8000/api/wallet/initialize/HOUSE_FDR12_002

# Copy returned addresses
```

#### 2. Opt-in to SUN ASA

```bash
curl -X POST http://localhost:8000/api/wallet/opt-in-sun/HOUSE_FDR12_001
curl -X POST http://localhost:8000/api/wallet/opt-in-sun/HOUSE_FDR12_002
```

#### 3. Submit Generation (IoT Simulation)

```bash
# House A generates 5 kWh during 3pm-4pm
curl -X POST http://localhost:8000/api/iot/generation \
  -H "Content-Type: application/json" \
  -d '{
    "house_id": "HOUSE_FDR12_001",
    "generation_kwh": 5.0,
    "device_id": "NodeMCU_001",
    "auth_token": "iot_secret_token"
  }'

# Surplus = 5 - 0.2 (avg hourly consumption) = 4.8 kWh
# → 4.8 SUN minted to House A
```

#### 4. Submit Demand (Consumer Request)

```bash
# House B needs 4 kWh
curl -X POST http://localhost:8000/api/demand/submit \
  -H "Content-Type: application/json" \
  -d '{
    "house_id": "HOUSE_FDR12_002",
    "demand_kwh": 4.0,
    "priority_level": 7,
    "duration_hours": 2.0
  }'

# AI matcher runs:
# - Supply available: 4.8 SUN in House A
# - Allocation: 4.0 kWh from pool, 0 grid
# - Transfer: 4 SUN from A → B
# - Cost: ₹36 (4 × ₹9)
```

#### 5. Verify SUN Balances

```bash
curl http://localhost:8000/api/wallet/HOUSE_FDR12_001
# Result: sun_balance = 0.8 (4.8 - 4 transferred)

curl http://localhost:8000/api/wallet/HOUSE_FDR12_002
# Result: sun_balance = 4.0 (received from A)
```

#### 6. Generate Monthly Bill

```bash
curl -X POST http://localhost:8000/api/billing/generate/HOUSE_FDR12_001/2024-03

# Bill generated:
# - solar_generated = 155 kWh
# - pool_sold = 120 kWh (to others that month)
# - earnings = ₹1080 (120 × ₹9)
# - sun_asa_minted = 155 (renewable certificates)
# - blockchain_hash = SHA256(bill_json)
```

#### 7. View Admin Dashboard

```bash
curl http://localhost:8000/api/admin/dashboard/feeder/FDR_12/monthly
# Shows:
# - Total generation: 310 kWh
# - Sun tokens minted: 310
# - Pool allocations: 240 kWh
# - Revenue (pool): ₹2160
# - Grid fallback: 70 kWh
# - Bills on blockchain: 2
```

---

## 8. SECURITY CONSIDERATIONS

### Current Demo Limitations

⚠️ **NOT FOR PRODUCTION**:

- Private keys stored in database (plaintext)
- No encryption at rest
- Admin key in .env file
- No key rotation

### Production Hardening

✅ **Recommended**:

- AWS KMS or HashiCorp Vault for key management
- Encrypt private keys at rest with master key
- HSM for transaction signing
- Multi-sig for admin operations
- Audit logging for all blockchain transactions
- Rate limiting on wallet operations
- IP whitelisting for sensitive endpoints

---

## 9. BLOCKCHAIN VERIFICATION

### Verify SUN Transfer on Algoexplorer

```
Transaction URL:
https://testnet.algoexplorer.io/tx/{transaction_hash}

Example for SUN transfer:
- Sender: House A address
- Receiver: House B address
- Asset: SUN (ID 756341116)
- Amount: 4
- Status: Confirmed
- Block: 34,567,890
- Timestamp: 2024-03-15 15:30:45 UTC
```

### Verify Bill Hash on Blockchain

```
Transaction URL:
https://testnet.algoexplorer.io/tx/{bill_blockchain_txn}

Example for bill hash recording:
- Type: Payment (0 ALGO)
- Note: "ROSHNI|HOUSE_FDR12_001|2024-03|a3f5b2c1d8e9..."
- Status: Confirmed
- Round: 34,567,900
- Immutable proof of bill
```

---

## 10. MONITORING & LOGGING

### Key Logs to Monitor

```
# Wallet creation
"Wallet created: PLJ..." (INFO)

# SUN minting
"SUN minted: 4.8 to HOUSE_FDR12_001" (INFO)

# SUN transfer
"SUN transferred: 4.0 from HOUSE_FDR12_001 to HOUSE_FDR12_002 TX: ABC123..." (INFO)

# Bill hash recording
"Bill hash recorded on blockchain: ABC123..." (INFO)

# Errors
"Opt-in error for HOUSE_FDR12_001: insufficient balance" (ERROR)
"SUN transfer failed for HOUSE_FDR12_001: account not opted in" (ERROR)
```

### Health Checks

```bash
# Backend health
curl http://localhost:8000/health

# Algorand network status
curl https://testnet-api.algonode.cloud/health

# Admin account balance
curl https://testnet-idx.algonode.cloud/v2/accounts/{admin_address}
```

---

## 11. SUMMARY: What's Now Working

✅ **Fixed Issues**:

- No more silent token creation
- Users get actual wallets
- SUN tokens actually transfer
- Blockchain is real source of truth
- Admins see true feeder metrics
- Bills recorded immutably

✅ **New Capabilities**:

- Custodial wallet lifecycle
- Atomic SUN transfers
- Monthly bill hashing
- Feeder-level admin dashboards
- Wallet opt-in management
- Complete blockchain audit trail

✅ **Architecture Improvements**:

- Database tracks SUN flows
- Billing triggers blockchain
- Admin has aggregate visibility
- DISCOM remains financial authority
- All renewable allocation on-chain

---

## Questions?

Run demo scenario in order → you'll see complete flow!

**Next:** Integrate frontend wallet UI with these endpoints.
