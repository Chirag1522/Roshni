# Frontend Integration Checklist - Quick Setup

## Prerequisites

- Backend running with wallet_service.py and pool_sun_service.py
- Database updated with House model fields (algorand_address, opt_in_sun_asa, etc)
- Admin endpoints available: /api/admin/dashboard/feeder/\*, /api/admin/dashboard/all-feeders
- Algorand testnet wallet with some ALGO for transactions

## Frontend Components - Already Integrated

### ✅ New Components Created

1. **WalletDisplay.jsx** - Shows SUN balance & monthly metrics
   - Location: `/frontend/src/components/WalletDisplay.jsx`
   - Props: `houseId` (string)
   - Displays: Address, balance, opt-in status, monthly breakdown
   - Features: Sync balance button, Algoexplorer link

2. **WalletInitialization.jsx** - Creates blockchain wallet
   - Location: `/frontend/src/components/WalletInitialization.jsx`
   - Props: `houseId`, `onSuccess` (callback)
   - Shows: Wallet address, explorer link, next steps
   - One-time flow (can be used in signup)

3. **WalletOptIn.jsx** - Opts into SUN ASA
   - Location: `/frontend/src/components/WalletOptIn.jsx`
   - Props: `houseId`, `onSuccess` (callback)
   - Shows: Transaction ID, explorer link, confirmation
   - Triggered automatically on first transaction

4. **AdminPanel.jsx** - Enhanced with blockchain metrics
   - Location: `/frontend/src/pages/AdminPanel.jsx`
   - Props: `feederCode` (string)
   - Shows: Daily metrics, monthly performance, all feeders overview
   - Features: Load buttons, colorized percentages, revenue tracking

### ✅ Updated Dashboard Pages

1. **SellerDashboard.jsx**
   - Added: `import WalletDisplay from '../components/WalletDisplay'`
   - Displays: WalletDisplay after "Generation Details" section
   - Shows: SUN minted from solar surplus

2. **BuyerDashboard.jsx**
   - Added: `import WalletDisplay from '../components/WalletDisplay'`
   - Displays: WalletDisplay after "Allocation Result" section
   - Shows: SUN received from pool purchases

3. **BillingPage.jsx**
   - Enhanced: Blockchain Verification section
   - Shows: Full bill hash (SHA256)
   - Link: Direct to Algoexplorer transaction

---

## Testing the Integration

### Test 1: Wallet Display Renders (No Backend Needed)

```
1. npm start (from frontend directory)
2. Navigate to Seller Dashboard
3. Look for "🌐 Blockchain Wallet" card
✅ Should show loading spinner, then wallet info
```

### Test 2: Wallet Initialization

```
1. Make sure backend is running
2. Seller Dashboard → WalletDisplay → Initialize Wallet
3. Should return: wallet address, Algoexplorer link
✅ Wallet displays with 58-char Algorand address
```

### Test 3: Admin Dashboard Load Metrics

```
1. Navigate to Admin Panel
2. Click "Load Daily Metrics"
3. Should populate: generation, demand, grid fallback, wallet deployment %
✅ Shows colorized boxes with feeder metrics
```

### Test 4: Blockchain Hash on Billing

```
1. Create a bill in Billing Page
2. View bill details
3. Scroll to "Blockchain Verification" section
4. Should show: Full SHA256 hash, Algoexplorer link
✅ Hash and transaction link visible
```

### Test 5: Voice Narration with Wallet

```
1. SellerDashboard: Submit generation (if IoT available)
2. Should hear voice in Hindi: "आपने आज सौर ऊर्जा से ₹X कमाए।"
3. WalletDisplay SUN Minted should increase
✅ Voice plays, wallet updates
```

---

## API Contracts (What Backend Must Return)

### GET /api/wallet/{house_id}

**Response** (200 OK):

```json
{
  "status": "initialized|not_initialized",
  "algorand_address": "PXXXXXX...",
  "opt_in_sun_asa": true,
  "sun_balance_on_chain": 6.5,
  "explorer_url": "https://testnet.algoexplorer.io/address/PXXXXX",
  "sun_minted_this_month": 6.5,
  "sun_received_this_month": 0.0,
  "sun_transferred_this_month": 0.0
}
```

### POST /api/wallet/initialize/{house_id}

**Response** (201):

```json
{
  "algorand_address": "PXXXXX...",
  "explorer_url": "https://testnet.algoexplorer.io/address/PXXXXX"
}
```

### POST /api/wallet/opt-in-sun/{house_id}

**Response** (200):

```json
{
  "opt_in_tx_id": "ABC123...",
  "explorer_url": "https://testnet.algoexplorer.io/tx/ABC123",
  "status": "submitted"
}
```

### GET /api/admin/dashboard/feeder/{code}/daily

**Response** (200):

```json
{
  "total_generation_kwh": 245.5,
  "total_demand_kwh": 210.3,
  "grid_fallback_kwh": 15.2,
  "allocations_matched": 12,
  "wallets_deployed_count": 18,
  "total_houses": 20,
  "wallet_deployment_percentage": 90.0
}
```

### GET /api/admin/dashboard/feeder/{code}/monthly

**Response** (200):

```json
{
  "monthly_revenue": 8450.0,
  "monthly_costs": 7200.0,
  "net_profit": 1250.0,
  "sun_issued_count": 245.5,
  "bills_on_blockchain_count": 20
}
```

### GET /api/admin/dashboard/all-feeders

**Response** (200):

```json
{
  "feeders": [
    {
      "feeder_code": "FDR_12",
      "total_houses": 20,
      "wallets_deployed": 18,
      "wallet_deployment_percentage": 90.0,
      "monthly_revenue": 8450.0
    }
  ]
}
```

---

## Common Issues & Fixes

| Issue                            | Cause                           | Fix                                           |
| -------------------------------- | ------------------------------- | --------------------------------------------- |
| WalletDisplay shows "Error"      | Wallet endpoint not found       | Check backend /api/wallet/{house_id}          |
| Wallet Address shows "undefined" | Incomplete response             | Verify wallet_address in response             |
| Algoexplorer link broken         | testnet vs mainnet URL          | Ensure using https://testnet.algoexplorer.io/ |
| Admin metrics don't load         | Dashboard endpoints missing     | Implement /api/admin/dashboard/\* endpoints   |
| Bill hash not showing            | Bill not finalized              | Check bill billing_service finalize_bill()    |
| Voice doesn't play               | allocation_status not 'matched' | Ensure allocation successful before voice     |

---

## Component Usage Examples

### Using WalletDisplay in New Pages

```jsx
import WalletDisplay from "../components/WalletDisplay";

export default function MyPage({ houseId }) {
  return (
    <div>
      <h1>My Page</h1>
      <WalletDisplay houseId={houseId} /> // Will auto-fetch wallet info
    </div>
  );
}
```

### Using WalletInitialization in Signup

```jsx
import WalletInitialization from "../components/WalletInitialization";

export default function SignupFlow({ houseId }) {
  const handleWalletSuccess = (walletData) => {
    console.log("Wallet created:", walletData.algorand_address);
    // Redirect to dashboard
  };

  return (
    <WalletInitialization houseId={houseId} onSuccess={handleWalletSuccess} />
  );
}
```

---

## Performance Notes

- WalletDisplay fetches data on mount, auto-refresh every 10s
- Admin dashboard metrics loaded on-demand (click buttons)
- All components use standard React hooks (useState, useEffect)
- No additional packages needed (uses existing api service)

---

## Deployment Checklist

Before going to production:

- [ ] Backend wallet endpoints implemented and tested
- [ ] Admin dashboard endpoints returning correct data
- [ ] Billing finalization recording bills to blockchain
- [ ] Voice service using correct Rachel voice ID (21m00Tcm4TlvDq8ikWAM)
- [ ] Algoexplorer links use mainnet URL (not testnet)
- [ ] Algorand mainnet wallet with sufficient balance
- [ ] Database fields added to House model
- [ ] All environment variables set (ALGO_MNEMONIC, ASSET_ID, etc)
- [ ] Rate limiting on wallet/admin endpoints
- [ ] Error logging in place for blockchain failures

---

## Files Status Summary

```
✅ CREATED
  frontend/src/components/WalletDisplay.jsx           (192 lines)
  frontend/src/components/WalletInitialization.jsx    (115 lines)
  frontend/src/components/WalletOptIn.jsx             (125 lines)
  frontend/src/pages/AdminPanel.jsx                   (Enhanced, 340 lines)
  docs/FRONTEND_DEMO_GUIDE.md                         (Comprehensive guide)

✅ UPDATED
  frontend/src/pages/SellerDashboard.jsx              (Added WalletDisplay)
  frontend/src/pages/BuyerDashboard.jsx               (Added WalletDisplay)
  frontend/src/pages/BillingPage.jsx                  (Enhanced Blockchain verification)

✅ READY FOR TEST
  All components integrated and documented
  All API contracts defined
  Demo guide available
```

---

## Next Steps for User

1. **Verify Backend**: Ensure all wallet_service.py methods working
2. **Test APIs**: Use curl/Postman to test endpoints
3. **Run Frontend**: `npm start` and verify components render
4. **End-to-End Test**: Follow FRONTEND_DEMO_GUIDE.md scenario
5. **Customization**: Adjust colors, text, layout as needed
6. **Deployment**: Use deployment checklist before going live

---

For detailed architecture and backend setup, see: `BLOCKCHAIN_ARCHITECTURE_v2.md`
For demo walkthrough, see: `FRONTEND_DEMO_GUIDE.md`
For API reference, see: `BLOCKCHAIN_API_QUICK_REFERENCE.md`
