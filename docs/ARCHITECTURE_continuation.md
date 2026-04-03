# ROSHNI Architecture Continuation

## Data Flow: Demand Matching

```
1. Consumer submits demand via frontend
   POST /demand/submit {house_id, demand_kwh, priority}
                    ↓
2. Backend Pool Engine calculates state
   - Gets last 5 min of generation records
   - Gets pending demand records
   - Calculates: supply, demand, shortage
                    ↓
3. Matching Engine receives demand
   - Queries pool state
   - Calls AI Pricing Service (Gemini)
   - Gets allocation recommendation
                    ↓
4. AI Decision
   - Compares: pool rate (₹9) vs grid rate (₹12)
   - Considers: priority level, pool utilization
   - Allocates: X from pool, Y from grid
                    ↓
5. Create Allocation Record
   - Source: "pool" or "grid"
   - Amount: X kWh
   - AI Reasoning: stored
                    ↓
6. Blockchain Actions (if pool allocation)
   - Mint SUN ASA: X tokens → consumer address
   - Record transaction
                    ↓
7. Return response to consumer
   - allocated_kwh, grid_required_kwh
   - estimated_cost_inr
   - allocation_status: "matched" or "partial"
```

## Feeder-Level Pool Model

```
Feeder = Virtual energy buffer for region
Example: FDR_12 (North District)

┌──────────────────────────────────────┐
│        Feeder FDR_12 Pool             │
│  (Virtual, not physical location)     │
├──────────────────────────────────────┤
│                                       │
│  Generators (Supply):                 │
│  HOUSE_001: 4.8 kW ───┐              │
│  HOUSE_003: 2.9 kW ───┤─→ [POOL] ←──┐
│  HOUSE_005: 1.2 kW ───┘              │
│                         ↑              │
│                   DEMAND FROM:        │
│                   HOUSE_002: 3kW ─────┤
│                   HOUSE_004: 2kW ─────┤
│                                       │
│  Pool Status:                         │
│  - Supply: 8.9 kW                    │
│  - Demand: 5.0 kW                    │
│  - Surplus: 3.9 kW (can sell to grid)│
│  - Shortage: 0 kW (no grid needed)   │
│                                       │
└──────────────────────────────────────┘

Daily Net:
- Generated: 250 kWh
- Consumed: 180 kWh
- Exported: 70 kWh → Grid @₹8/kWh = ₹560
- Purchased: 0 kWh from grid
```

## Billing Model

```
Consumer Monthly Bill Structure:

┌─ SOLAR EXPORT (Generator credits) ─┐
│ kWh_exported × ₹8 (DISCOM rate)    │
└────────────────────────────────────┘

┌─ POOL SALES (Generator credits) ──┐
│ kWh_sold_to_pool × ₹9              │
└────────────────────────────────────┘

┌─ POOL PURCHASES (Consumer charges)┐
│ kWh_bought_from_pool × ₹9          │
└────────────────────────────────────┘

┌─ GRID PURCHASES (Fallback charges)┐
│ kWh_from_grid × ₹12 (DISCOM rate) │
└────────────────────────────────────┘

┌─ FIXED CHARGES ────────────────────┐
│ ₹100/month (DISCOM fixed)          │
└────────────────────────────────────┘

┌─ ADMINISTRATION FEE ───────────────┐
│ (Pool + Grid charges) × 2% (DISCOM)│
└────────────────────────────────────┘

NET PAYABLE = (Charges) - (Credits)
Negative = Consumer credit/refund
```

## Security Model

1. **IoT Authentication**
   - Token-based (Bearer token in header)
   - Rate limiting per device
   - Device ID tracking

2. **API Security**
   - CORS restricted to frontend domain
   - Request logging for audit
   - Error responses don't expose internals

3. **Database**
   - SQLite for dev, PostgreSQL for prod
   - No plaintext passwords
   - Encrypted connections

4. **Blockchain**
   - Admin mnemonic in .env (not code)
   - Testnet for demo
   - Mainnet requires audit

## Scalability Considerations

**Current:** Single feeder, ~10 houses
**Target:** Multiple feeders, 1000+ houses

Optimizations:

- Aggregate generation/demand every 30s (not 5s)
- Cache pool state in Redis
- Use message queue (Celery) for billing
- Horizontal scaling: Load balancer → multiple API instances
- Database: Switch to PostgreSQL partitioned by feeder

## Fault Tolerance

```
No Grid Fallback → Outage Risk
        ↓
DISCOM Remains Authority
        ↓
Consumer always gets power
(Grid at ₹12/kWh if pool empty)
        ↓
System degrades gracefully
```

---
