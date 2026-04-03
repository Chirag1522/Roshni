# Roshni Frontend Demo Guide - Complete Blockchain Integration

## Overview

This guide demonstrates the complete end-to-end flow of the Roshni renewable energy pooling platform with blockchain integration. The frontend now displays wallet information, SUN token balances, and blockchain verification for all transactions.

## System Architecture

```
House (Prosumer) → Seller/Buyer Dashboard → Wallet Display
                                              ↓
                                        Pool Matching
                                              ↓
                                        Allocation Result
                                              ↓
                                        SUN Transfer (On-Chain)
                                              ↓
                                        Voice Narration (Hindi)
                                              ↓
                                        Monthly Bill
                                              ↓
                                        Blockchain Verification
                                              ↓
                                        Admin Dashboard (Feeder Metrics)
```

## Demo Scenario: House-to-House Energy Trading

### Scenario Setup

- **Feeder Code**: FDR_12
- **House A** (HOUSE_FDR12_001): Solar Seller - 10 kW panel, generates 8 kWh/day
- **House B** (HOUSE_FDR12_002): Consumer - Buys from pool when available
- **House C** (HOUSE_FDR12_003): Admin - Manages feeder metrics

---

## Step 1: Initialize Blockchain Wallet

### Where: SellerDashboard / BuyerDashboard

Starting from the frontend, each house needs a custodial wallet. This happens automatically the first time they interact with the blockchain.

**What you'll see:**

- 🌐 Blockchain Wallet card appears on both dashboards
- **Status**: "Wallet Not Available" → Need initialization
- Click **Initialize Wallet** to create Algorand account

### Process Flow:

1. User clicks "Initialize Wallet"
2. Backend creates new Algorand account (keypair)
3. Returns:
   - Algorand Address (58 chars, starts with `P`)
   - Algoexplorer link to view wallet
4. Private key securely stored in DB (custodial model)

### Expected Output:

```
✅ Wallet Created Successfully!

Your Algorand Address:
PLJDSUI7PFKLJSDFLKJSDF... (58 chars)

🔗 View on Algoexplorer →

Next Step: Your wallet is now created. On your next activity,
your wallet will automatically opt into the SUN ASA token.
```

---

## Step 2: Sales/Purchasing Flow Triggers Wallet Opt-in

### Where: SellerDashboard (Generate Solar) → BuyerDashboard (Submit Demand)

### House A (Seller): Submit Solar Generation

**Path**: Seller Dashboard → (existing IOT generation flow)

```
1. Solar generation detected: 8 kWh generated today
2. Surplus calculated: 8 kWh - 2 kWh (consumption) = 6 kWh surplus
3. Backend detects surplus → Mints 6 SUN tokens to House A wallet
4. Voice narration: "आपने आज सौर ऊर्जा से ₹X कमाए।"
   (Translation: "You earned ₹X from solar today.")
```

### House B (Buyer): Request Demand

**Path**: Buyer Dashboard → Submit Demand → 5 kWh requested

```
1. House B requests 5 kWh from pool @ ₹9/kWh
2. House A has 6 SUN (6 kWh available)
3. Pool matching allocates 5 kWh from House A to B
4. On-chain transfer: 5 SUN transferred from House A → House B wallet (Algorand)
5. Voice narration: "बिल स्वीकृत। आपने पूल से खरीदकर ₹45 की बचत की।"
   (Translation: "Bill approved. You saved ₹45 buying from pool.")
```

### Result in Wallet Display:

**House A (Seller)** - After generation:

```
🌐 Blockchain Wallet

SUN Balance (On-Chain): 6.00
📊 This Month:
  SUN Minted: 6.00       [generated surplus]
  SUN Received: 0.00     [from pool purchases]
  SUN Transferred: 5.00  [sold to House B]
```

**House B (Buyer)** - After allocation:

```
🌐 Blockchain Wallet

SUN Balance (On-Chain): 5.00
📊 This Month:
  SUN Minted: 0.00       [no generation]
  SUN Received: 5.00     [from House A via pool]
  SUN Transferred: 0.00  [didn't sell]
```

---

## Step 3: Monthly Bill Generation & Blockchain Recording

### Where: BillingPage → View Details → Blockchain Verification

**Path**: Billing Page → Generate Bill → View Bill → See Blockchain Hash

### Process:

1. Bill finalized for month (e.g., 2025-03-01)
2. Complete bill JSON created containing all metrics:
   - Generation metrics
   - Pool transactions
   - Grid purchases
   - Financial calculations
   - SUN minting
3. Bill JSON hashed with SHA256
4. Bill hash recorded on Algorand testnet via zero-ALGO transaction
5. Transaction ID stored in bill record

### Display on BillingPage:

```
Bill Details - 2025-03-01

💰 NET PAYABLE: ₹-450.00 (Refund/Credit)

🌞 SUN ASA Minted: 6.00 SUN tokens
(renewable allocation certificates) recorded on Algorand blockchain.

⛓️ Blockchain Verification:

Bill Hash (SHA256):
ca7f2e3a8b9c1d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d

🔗 View on Algoexplorer →
https://testnet.algoexplorer.io/tx/EXAMPLEHASH123456789

Immutable proof of bill recorded on Algorand testnet.
```

### What the Hash Proves:

- Complete bill as it was when finalized
- No retroactive changes possible
- Immutable audit trail for DISCOM settlement
- Transparent proof for consumers

---

## Step 4: Admin Dashboard - Feeder-Level Metrics

### Where: Admin Panel → All viewable by feeder code

**Path**: Navigation → Admin → View All Metrics

### Daily Metrics (Business View):

```
📈 Daily Feeder Metrics

Generation:      45.30 kWh   [Total solar output]
Demand:          38.50 kWh   [Total consumer requests]
Grid Fallback:    6.80 kWh   [Grid purchases needed]

Allocations Matched: 12        [Successful pool matches]
Wallets Deployed:    18/20     [90% blockchain ready]
```

### Monthly Metrics (Performance View):

```
💰 Monthly Feeder Performance

Revenue (Pool Sales):    ₹8,450.00    [From prosumers selling]
Costs (Grid Purchase):   ₹7,200.00    [From grid fallback]
Net Profit:              ₹1,250.00    [Positive!]

SUN Issued:              245.50 tokens [Renewable certificates)
Bills on Blockchain:     20 bills      [Immutably recorded]
```

### All Feeders Overview (DISCOM View):

```
🌐 All Feeders - DISCOM Overview

Feeder Code  | Houses | Wallets | Deploy% | Monthly Revenue
FDR_12       | 20     | 18      | 90%     | ₹8,450.00
FDR_11       | 15     | 12      | 80%     | ₹5,200.00
FDR_10       | 22     | 15      | 68%     | ₹3,100.00
```

---

## Component Breakdown

### New Frontend Components Created

#### 1. **WalletDisplay.jsx** (192 lines)

- Shows SUN balance (on-chain sync)
- Displays wallet address and Algoexplorer link
- Opt-in status indicator
- Monthly metrics (SUN minted/received/transferred)
- Sync Balance button for real-time updates
- Integrated into: SellerDashboard, BuyerDashboard

#### 2. **WalletInitialization.jsx** (115 lines)

- One-time wallet creation flow
- Displays created address
- Explains custodial model
- Links to Algoexplorer
- Shows next steps guidance

#### 3. **WalletOptIn.jsx** (125 lines)

- SUN ASA opt-in transaction submission
- Shows transaction ID and link
- Explains ASA concept
- Confirmation after opt-in

#### 4. **AdminPanel.jsx** (Enhanced)

- Daily metrics endpoint integration
- Monthly metrics with revenue/profit
- All feeders DISCOM overview
- Wallet deployment status
- Bills on blockchain counter

### Updated Pages

#### **SellerDashboard.jsx**

```
+ Import WalletDisplay component
+ Display after "Generation Details" section
+ Shows SUN minted from surplus
```

#### **BuyerDashboard.jsx**

```
+ Import WalletDisplay component
+ Display after "Allocation Result" section
+ Shows SUN received from pool purchases
```

#### **BillingPage.jsx**

```
+ Enhanced blockchain verification section
+ Full bill hash display (SHA256)
+ Algoexplorer link to transaction
+ SUN minting indicator
```

---

## Demo Testing Checklist

### Phase 1: Wallet Setup

- [ ] Navigate to Seller Dashboard
- [ ] Scroll to "Blockchain Wallet" card
- [ ] Click "Initialize Wallet"
- [ ] Verify address displayed
- [ ] Click Algoexplorer link (opens testnet explorer)
- [ ] Verify same for Buyer Dashboard

### Phase 2: Energy Transactions

- [ ] Go to Seller Dashboard
- [ ] Submit generation (if IoT available) or use test data
- [ ] Check Wallet Display for "SUN Minted" increase
- [ ] Refresh balance with "Sync Balance" button
- [ ] Go to Buyer Dashboard
- [ ] Submit demand for same feeder
- [ ] Verify allocation successful
- [ ] Check Wallet Display for "SUN Received"
- [ ] Listen to voice narration (if enabled)

### Phase 3: Billing & Verification

- [ ] Go to Billing Page
- [ ] Generate bill for current month
- [ ] Click "View" on generated bill
- [ ] Scroll to "Blockchain Verification" section
- [ ] Verify bill hash displayed
- [ ] Click "View on Algoexplorer" link
- [ ] Confirm transaction visible on testnet

### Phase 4: Admin Dashboard

- [ ] Navigate to Admin Panel
- [ ] Load Feeder Details (FDR_12)
- [ ] Load Daily Metrics
- [ ] Verify generation/demand/grid fallback
- [ ] Load Monthly Metrics
- [ ] Check revenue, costs, profit
- [ ] Load All Feeders
- [ ] Verify wallet deployment percentages

---

## Voice Narration Integration

### When Voice Narrates (Hindi only):

1. **On Successful Generation**: "आपने आज सौर ऊर्जा से ₹X कमाए।"
   - English: "You earned ₹X from solar today."

2. **On Successful Allocation**: "बिल स्वीकृत। आपने पूल से खरीदकर ₹X की बचत की।"
   - English: "Bill approved. You saved ₹X buying from pool."

3. **On Bill View**: "आपके खाते में ₹X की वापसी है।" OR "सौर ऊर्जा से आपने ₹X कमाए।"
   - English: "You have ₹X credit." OR "You earned ₹X from solar."

### Voice Settings:

- **Voice**: Rachel (ElevenLabs ID: 21m00Tcm4TlvDq8ikWAM)
- **Language**: Hindi
- **Duration**: 1-2 lines max (short, informative)
- **Trigger**: Only on successful transactions (matched/submitted)

---

## Blockchain Details for Demo

### Algorand Testnet Configuration

- **Network**: Algorand Testnet
- **Asset ID (SUN)**: 756341116
- **Explorer**: https://testnet.algoexplorer.io/
- **Block Time**: ~4.5 seconds

### Transaction Types

1. **Wallet Creation**: Account creation (zero cost)
2. **ASA Opt-in**: Asset transfer with 0 amount
3. **SUN Transfer**: Standard asset transfer (1,000 microAlgo fee)
4. **Bill Recording**: Zero-ALGO payment with bill hash in memo

---

## Advanced Features

### Wallet Sync

- "Sync Balance" button fetches real-time on-chain balance
- Updates SUN balance from Algorand
- Shows confirmation after sync

### Explorer Links

All wallet addresses and transactions link directly to Algoexplorer:

- Wallet view: Shows all transactions
- Transaction view: Shows amount, parties, time
- Asset view: Shows all SUN token holders

### Monthly Aggregation

- Wallet Display shows monthly breakdown:
  - SUN Minted (from surplus)
  - SUN Received (from pool)
  - SUN Transferred (to others)
- Admin dashboard shows feeder-wide aggregation

---

## Troubleshooting

### Issue: Wallet Shows "Not Available"

**Solution**: Refresh page or navigate away and back. If persists, check backend wallet creation logs.

### Issue: Blockchain Hash Not Showing

**Solution**: Bill must be in "finalized" status. Check billing status in database.

### Issue: Algoexplorer Link Not Working

**Solution**: Verify it's using testnet URL. Check transaction ID is valid on-chain.

### Issue: Voice Not Playing

**Solution**:

1. Check localStorage: `localStorage.getItem('voiceEnabled')`
2. Grant audio permissions
3. Ensure allocation_status is 'matched' (voice only on success)

---

## Demo Script (5 Minute Walkthrough)

```
DEMO_TIME: 5 minutes | AUDIENCE: Stakeholders, DISCOM officials

[MINUTE 1] SETUP
1. Open Roshni app, show home page
2. Navigate to Seller Dashboard (House A)
3. Scroll to Blockchain Wallet section
4. Explain: "Each prosumer gets a custodial wallet"

[MINUTE 2] WALLET CREATION
1. Click "Initialize Wallet"
2. Show wallet created
3. Click Algoexplorer link
4. Show wallet on blockchain explorer (testnet)

[MINUTE 3] ENERGY FLOW & VOICE
1. Submit generation (8 kWh)
2. Wait for voice narration
3. Show Wallet Display: SUN minted = 8
4. Click Buyer Dashboard (House B)
5. Submit demand (5 kWh)
6. Show allocation matched
7. Voice plays for successful buy

[MINUTE 4] BILLING & VERIFICATION
1. Go to Billing → Generate Bill
2. View bill details
3. Scroll to Blockchain Verification
4. Show bill hash
5. Click Algoexplorer link
6. Show transaction on testnet explorer

[MINUTE 5] ADMIN DASHBOARD
1. Go to Admin Panel
2. Load Daily Metrics: Show generation vs demand
3. Load Monthly: Show revenue, profit, SUN issued
4. Show All Feeders: DISCOM overview
5. Highlight: "90% wallet deployment = Ready for scale"
```

---

## Key Messages for Demo Audience

### For DISCOM Officials:

- "Blockchain creates immutable audit trail of all bills"
- "Admin dashboard shows real-time feeder performance"
- "SUN tokens create transparent renewable certificate system"
- "No consumer has access to private keys (custodial model)"

### For Prosumers:

- "Your solar generation automatically earns SUN tokens"
- "Pool buying saves you money with shorter delivery"
- "Voice narration tells you earnings in Hindi"
- "Everything recorded permanently for your protection"

### For Developers:

- "All backend endpoints fully integrated"
- "Frontend components reusable across dashboards"
- "Algorand testnet provides immutability"
- "Architecture ready for production hardening"

---

## Files Modified/Created

### New Components (4 files)

- ✅ `/frontend/src/components/WalletDisplay.jsx` (192 lines)
- ✅ `/frontend/src/components/WalletInitialization.jsx` (115 lines)
- ✅ `/frontend/src/components/WalletOptIn.jsx` (125 lines)
- ✅ `/frontend/src/pages/AdminPanel.jsx` (Enhanced)

### Updated Pages (3 files)

- ✅ `/frontend/src/pages/SellerDashboard.jsx` (Added WalletDisplay)
- ✅ `/frontend/src/pages/BuyerDashboard.jsx` (Added WalletDisplay)
- ✅ `/frontend/src/pages/BillingPage.jsx` (Enhanced blockchain verification)

---

## API Endpoints Used

```
GET  /api/wallet/{house_id}
     Returns: wallet_address, opt_in_status, sun_balance, monthly_metrics

POST /api/wallet/initialize/{house_id}
     Returns: wallet_address, explorer_url

POST /api/wallet/opt-in-sun/{house_id}
     Returns: opt_in_tx_id, explorer_url

POST /api/wallet/check-balance/{house_id}
     Returns: sun_balance_on_chain (synced from blockchain)

GET  /api/admin/dashboard/feeder/{code}/daily
GET  /api/admin/dashboard/feeder/{code}/monthly
GET  /api/admin/dashboard/all-feeders
```

---

## Next Production Steps

1. **Key Management**: Migrate from plaintext to encrypted/HSM storage
2. **Mainnet Migration**: Move from Algorand testnet to mainnet
3. **Scaling**: Batch transactions for cost optimization
4. **Governance**: Add DAO features for community voting
5. **Analytics**: Advanced reporting for DISCOM settlement

---

**For questions or issues, check the main BLOCKCHAIN_ARCHITECTURE_v2.md for comprehensive system design.**
