## ROSHNI v2: Wallet & Blockchain API Quick Reference

---

## SETUP (5 minutes)

### 1. Start Backend

```bash
cd /home/khushi/roshni/backend
source venv/bin/activate
uvicorn main:app --reload --port 8000
```

### 2. Create Houses in Database

```bash
# Access: http://localhost:8000/docs (auto-generated Swagger UI)
# Or use CLI:
python << 'EOF'
from app.database import get_db
from app.models import Feeder, House

# Ensure feeder exists
db = next(get_db())
feeder = db.query(Feeder).filter(Feeder.feeder_code == "FDR_12").first()
if not feeder:
    feeder = Feeder(feeder_code="FDR_12", location="Test District")
    db.add(feeder)
    db.commit()

# Create two houses
house_a = House(
    house_id="HOUSE_FDR12_001",
    feeder_id=feeder.id,
    owner_name="Seller (Solar)",
    prosumer_type="generator",
    solar_capacity_kw=10.0
)
house_b = House(
    house_id="HOUSE_FDR12_002",
    feeder_id=feeder.id,
    owner_name="Buyer (Consumer)",
    prosumer_type="consumer",
    solar_capacity_kw=0.0
)
db.add_all([house_a, house_b])
db.commit()
print("Houses created!")
EOF
```

---

## WALLET LIFECYCLE ENDPOINTS

### Initialize Custodial Wallet

**Request**

```bash
POST /api/wallet/initialize/{house_id}

curl -X POST http://localhost:8000/api/wallet/initialize/HOUSE_FDR12_001
```

**Response** (201)

```json
{
  "status": "success",
  "house_id": "HOUSE_FDR12_001",
  "algorand_address": "PLJXQBK77XQJDKBK7BTZBL2C4SWVWMUZRM5PKYJNLJFVYPVMVVTPQGTVJI",
  "explorer_url": "https://testnet.algoexplorer.io/address/PLJ...",
  "message": "Wallet created. Next: opt-in to SUN ASA."
}
```

---

### Opt-in to SUN ASA

**Request**

```bash
POST /api/wallet/opt-in-sun/{house_id}

curl -X POST http://localhost:8000/api/wallet/opt-in-sun/HOUSE_FDR12_001
```

**Response** (200)

```json
{
  "status": "success",
  "house_id": "HOUSE_FDR12_001",
  "txid": "3A2F1E5D4B6C7A9F2E8D1C3B5A7F9D1E2C4B6A8F",
  "round": 34567890,
  "message": "Successfully opted into SUN ASA"
}
```

---

### Get Wallet Status

**Request**

```bash
GET /api/wallet/{house_id}

curl http://localhost:8000/api/wallet/HOUSE_FDR12_001
```

**Response** (200)

```json
{
  "status": "success",
  "house_id": "HOUSE_FDR12_001",
  "algorand_address": "PLJ...",
  "opt_in_sun_asa": true,
  "sun_balance_on_chain": 3.5,
  "sun_minted_this_month": 3.5,
  "sun_received_this_month": 0.0,
  "sun_transferred_this_month": 0.0,
  "explorer_url": "https://testnet.algoexplorer.io/address/PLJ..."
}
```

---

### Check On-Chain SUN Balance

**Request**

```bash
POST /api/wallet/check-balance/{house_id}

curl -X POST http://localhost:8000/api/wallet/check-balance/HOUSE_FDR12_001
```

**Response** (200)

```json
{
  "status": "success",
  "house_id": "HOUSE_FDR12_001",
  "address": "PLJ...",
  "sun_balance": 3.5,
  "algo_balance": 0.5
}
```

---

## TRANSACTION FLOW ENDPOINTS

### Submit Generation (IoT)

**Request**

```bash
POST /api/iot/generation

curl -X POST http://localhost:8000/api/iot/generation \
  -H "Content-Type: application/json" \
  -d '{
    "house_id": "HOUSE_FDR12_001",
    "generation_kwh": 5.0,
    "device_id": "NodeMCU_001",
    "auth_token": "iot_secret_token"
  }'
```

**Response** (200)

```json
{
  "status": "success",
  "house_id": "HOUSE_FDR12_001",
  "generation_kwh": 5.0,
  "surplus_detected": true,
  "surplus_kwh": 4.8,
  "sun_minted": 4.8,
  "message": "Generation recorded. 4.8 SUN minted."
}
```

---

### Submit Demand (Consumer Request)

**Request**

```bash
POST /api/demand/submit

curl -X POST http://localhost:8000/api/demand/submit \
  -H "Content-Type: application/json" \
  -d '{
    "house_id": "HOUSE_FDR12_002",
    "demand_kwh": 4.0,
    "priority_level": 7,
    "duration_hours": 2.0
  }'
```

**Response** (200)

```json
{
  "status": "success",
  "demand_id": 15,
  "house_id": "HOUSE_FDR12_002",
  "demand_kwh": 4.0,
  "allocation_status": "matched",
  "allocated_kwh": 4.0,
  "grid_required_kwh": 0.0,
  "ai_reasoning": "Full surplus available from House A. Zero grid fallback.",
  "estimated_cost_inr": 36.0,
  "sun_transferred_from": "HOUSE_FDR12_001",
  "blockchain_txid": "ABC123DEF456..."
}
```

---

## BILLING & BLOCKCHAIN ENDPOINTS

### Generate Monthly Bill

**Request**

```bash
POST /api/billing/generate/{house_id}/{month_year}

curl -X POST http://localhost:8000/api/billing/generate/HOUSE_FDR12_001/2024-03
```

**Response** (200)

```json
{
  "status": "success",
  "bill_id": 42,
  "house_id": "HOUSE_FDR12_001",
  "month_year": "2024-03",
  "solar_generated_kwh": 155.0,
  "pool_sold_kwh": 120.0,
  "solar_export_credit": 1240.0,
  "pool_sale_credit": 1080.0,
  "net_payable": -120.0,
  "sun_asa_minted": 155,
  "message": "Bill generated. Ready to finalize."
}
```

---

### Finalize Bill (Record on Blockchain)

**Request**

```bash
POST /api/billing/finalize/{bill_id}

curl -X POST http://localhost:8000/api/billing/finalize/42
```

**Response** (200)

```json
{
  "status": "success",
  "bill_id": 42,
  "month_year": "2024-03",
  "bill_hash": "a3f5b2c1d8e9f0a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f",
  "blockchain_txid": "3A2F1E5D4B6C7A9F2E8D1C3B5A7F9D1E",
  "blockchain_round": 34567890,
  "explorer_url": "https://testnet.algoexplorer.io/tx/3A2F...",
  "message": "Bill finalized and recorded on blockchain."
}
```

---

### Verify Bill on Blockchain

**Request**

```bash
GET /api/blockchain/bill-hash/verify/{txn_id}

curl http://localhost:8000/api/blockchain/bill-hash/verify/3A2F1E5D4B6C7A9F2E8D1C3B5A7F9D1E
```

**Response** (200)

```json
{
  "status": "verified",
  "txid": "3A2F1E5D4B6C7A9F2E8D1C3B5A7F9D1E",
  "bill_note": "ROSHNI|HOUSE_FDR12_001|2024-03|a3f5b2c...",
  "house_id": "HOUSE_FDR12_001",
  "month_year": "2024-03",
  "bill_hash": "a3f5b2c...",
  "confirmed_round": 34567890,
  "timestamp": "2024-03-15T15:30:45Z",
  "explorer_link": "https://testnet.algoexplorer.io/tx/3A2F...",
  "message": "Bill authenticity verified on Algorand blockchain"
}
```

---

## ADMIN DASHBOARD ENDPOINTS

### Daily Feeder Summary

**Request**

```bash
GET /api/admin/dashboard/feeder/{feeder_code}/daily

curl http://localhost:8000/api/admin/dashboard/feeder/FDR_12/daily
```

**Response** (200)

```json
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

---

### Monthly Feeder Summary

**Request**

```bash
GET /api/admin/dashboard/feeder/{feeder_code}/monthly

curl http://localhost:8000/api/admin/dashboard/feeder/FDR_12/monthly
```

**Response** (200)

```json
{
  "feeder_code": "FDR_12",
  "month_year": "2024-03",
  "energy_metrics": {
    "total_generation_kwh": 3850.0,
    "total_exported_kwh": 3200.0,
    "pool_bought_kwh": 2100.0,
    "pool_sold_kwh": 2500.0,
    "grid_bought_kwh": 1850.0
  },
  "financial": {
    "revenue": {
      "solar_export_credit_inr": 25600.0,
      "pool_sales_credit_inr": 22500.0,
      "total_revenue_inr": 48100.0
    },
    "costs": {
      "pool_purchase_charge_inr": 18900.0,
      "grid_purchase_charge_inr": 22200.0,
      "discom_fixed_and_admin_fee_inr": 3500.0,
      "total_costs_inr": 44600.0
    },
    "net_revenue_inr": 3500.0
  },
  "blockchain": {
    "sun_tokens_minted": 3200,
    "bills_recorded_on_chain": 42
  }
}
```

---

### All Feeders Summary (DISCOM View)

**Request**

```bash
GET /api/admin/dashboard/all-feeders

curl http://localhost:8000/api/admin/dashboard/all-feeders
```

**Response** (200)

```json
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
    {
      "feeder_code": "FDR_15",
      "location": "Central District",
      "total_capacity_kw": 1500.0,
      "houses": {
        "total": 75,
        "active": 72,
        "with_wallet": 68,
        "opted_in_sun": 65,
        "deployment_percent": 86.7
      }
    }
  ]
}
```

---

## ERROR RESPONSES

### Wallet Not Initialized

```json
{
  "status": "error",
  "message": "House has no Algorand wallet",
  "house_id": "HOUSE_FDR12_001"
}
```

### Not Opted Into SUN ASA

```json
{
  "status": "error",
  "message": "House not opted into SUN ASA",
  "house_id": "HOUSE_FDR12_001"
}
```

### Insufficient SUN Balance

```json
{
  "status": "error",
  "message": "HOUSE_FDR12_001 insufficient SUN balance",
  "required": 5.0,
  "available": 2.5
}
```

### Bill Not Found

```json
{
  "detail": "Bill not found",
  "bill_id": 999
}
```

---

## TEST SCENARIO (Copy-Paste Ready)

```bash
# 1. SETUP: Initialize Houses & Wallets
echo "Creating houses..."
# (Assume HOUSE_FDR12_001 + HOUSE_FDR12_002 exist in DB)

echo "Initializing wallets..."
ADDR_A=$(curl -s -X POST http://localhost:8000/api/wallet/initialize/HOUSE_FDR12_001 | jq -r '.algorand_address')
ADDR_B=$(curl -s -X POST http://localhost:8000/api/wallet/initialize/HOUSE_FDR12_002 | jq -r '.algorand_address')

echo "House A: $ADDR_A"
echo "House B: $ADDR_B"

# 2. OPT-IN
echo "Opting in..."
curl -s -X POST http://localhost:8000/api/wallet/opt-in-sun/HOUSE_FDR12_001 | jq
curl -s -X POST http://localhost:8000/api/wallet/opt-in-sun/HOUSE_FDR12_002 | jq

sleep 5

# 3. GENERATE (5 kWh surplus)
echo "Submitting generation..."
curl -s -X POST http://localhost:8000/api/iot/generation \
  -H "Content-Type: application/json" \
  -d '{
    "house_id": "HOUSE_FDR12_001",
    "generation_kwh": 5.0,
    "device_id": "NodeMCU_001",
    "auth_token": "iot_secret_token"
  }' | jq

sleep 2

# 4. DEMAND (4 kWh request)
echo "Submitting demand..."
curl -s -X POST http://localhost:8000/api/demand/submit \
  -H "Content-Type: application/json" \
  -d '{
    "house_id": "HOUSE_FDR12_002",
    "demand_kwh": 4.0,
    "priority_level": 7,
    "duration_hours": 2.0
  }' | jq

sleep 2

# 5. CHECK BALANCES
echo "House A balance:"
curl -s http://localhost:8000/api/wallet/HOUSE_FDR12_001 | jq '.sun_balance_on_chain'

echo "House B balance:"
curl -s http://localhost:8000/api/wallet/HOUSE_FDR12_002 | jq '.sun_balance_on_chain'

# 6. GENERATE BILLS
echo "Generating bills..."
curl -s -X POST http://localhost:8000/api/billing/generate/HOUSE_FDR12_001/2024-03 | jq '.bill_id'

# 7. ADMIN VIEW
echo "Admin dashboard:"
curl -s http://localhost:8000/api/admin/dashboard/all-feeders | jq
```

---

## POSTMAN COLLECTION

Postman collection available at: `postman/ROSHNI_Blockchain_v2.json`

Import into Postman:

1. File → Import → Select JSON
2. Add environment variables:
   - `backend_url`: http://localhost:8000
   - `house_a`: HOUSE_FDR12_001
   - `house_b`: HOUSE_FDR12_002

All endpoints pre-configured with request/response examples.

---

## Troubleshooting

| Error                  | Cause                               | Fix                                              |
| ---------------------- | ----------------------------------- | ------------------------------------------------ |
| "House not found"      | House doesn't exist in DB           | Create via Python/ORM                            |
| "Account not opted in" | Wallet exists but not opted in      | Call opt-in endpoint first                       |
| "Insufficient balance" | Not enough SUN to transfer          | Check on-chain balance first                     |
| "Invalid address"      | Address format wrong (not 58 chars) | Use returned address from init                   |
| "Network timeout"      | Algorand node unreachable           | Check: https://testnet-api.algonode.cloud/health |

---

## Next Steps

- [ ] Integrate wallet initialization into frontend signup
- [ ] Add SUN transfer UI during demand allocation
- [ ] Create wallet dashboard in frontend
- [ ] Add bill verification UI
- [ ] Build admin analytics dashboard
- [ ] Implement encryption for private keys

**You're ready to run the demo!**
