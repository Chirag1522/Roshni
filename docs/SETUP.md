# ROSHNI - Complete Setup Guide (From Scratch)

This guide will take you from zero to running ROSHNI locally on Pop!\_OS/Ubuntu Linux.

**Total Time: ~1-2 hours (depending on downloads)**

---

## 📋 Table of Contents


1. [API Keys & Accounts Setup](#api-keys--accounts-setup)
2. [Backend Setup](#backend-setup)
3. [Frontend Setup](#frontend-setup)
4. [IoT Setup (Optional)](#iot-setup-optional)
5. [Blockchain Setup](#blockchain-setup)
6. [Verification & Testing](#verification--testing)
7. [Troubleshooting](#troubleshooting)

---

## API Keys & Accounts Setup

### 1. Get Gemini API Key (⭐ IMPORTANT for AI features)

**What is it?** Google's AI API for intelligent energy allocation optimization.

---

### 2. Get Algorand Testnet Account (⭐ IMPORTANT for blockchain)

**What is it?** You need testnet ALGO coins to deploy the SUN ASA token and record bills on blockchain.

**Steps:**

1. **Create Account**:

   ```bash
   cd blockchain
   python3 << 'EOF'
   from algosdk import account
   from algosdk.mnemonic import from_private_key

   pk, addr = account.generate_account()
   print(f"Address: {addr}")
   print(f"\nMnemonic (25 words - SAVE THIS!):")
   print(from_private_key(pk))
   EOF
   ```

2. **Save Output Somewhere Safe**:

   ```
   Address: 7X3U7........
   Mnemonic: abandon ability ability... (25 words)
   ```

3. **Get Free Testnet ALGO**:
   - Go to: https://bank.testnet.algorand.org/
   - Paste your **Address** (not mnemonic!)
   - Click "Dispense"
   - Wait ~1 minute
   - You'll receive 4x 100 ALGO (400 total)

4. **Verify Balance**:

   ```bash
   python3 << 'EOF'
   from algorand_config import AlgorandConfig
   config = AlgorandConfig("testnet")
   info = config.get_account_info("YOUR_ADDRESS_HERE")
   print(f"Balance: {info.get('amount', 0) / 1_000_000} ALGO")
   EOF
   ```

   Should show: `Balance: 400.0 ALGO`

5. ✅ **Save These**:
   - Address
   - 25-word Mnemonic (keep VERY private!)
   - You'll need them for `ALGORAND_ADMIN_MNEMONIC` in `.env`

---


## Backend Setup

### Step 1: Clone Repository

```bash
# Navigate to your projects folder
cd ~/projects  # or any location

# Clone ROSHNI
git clone https://github.com/Khushi-Chaudhary04/roshni.git
cd roshni
```

### Step 2: Create Python Virtual Environment

```bash
cd backend

# Create venv
python3 -m venv venv

# Activate venv
source venv/bin/activate

```

### Step 3: Install Python Dependencies

```bash
# Ensure pip is latest
pip install --upgrade pip

# Install all dependencies
pip install -r requirements.txt

# Verify installation (should see no errors)
pip list | grep -E "fastapi|sqlalchemy|pydantic"
```

### Step 4: Create & Configure .env File

```bash
# Copy example file
cp .env.example .env

# Edit with your text editor
nano .env
# OR
gedit .env
# OR any other editor
```

**Fill in the .env file with your values:**

```bash
# ============ SYSTEM CONFIGURATION ============
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=DEBUG

# ============ URLS ============
BACKEND_URL=http://localhost:8000
FRONTEND_URL=http://localhost:5173
ALLOWED_HOSTS=localhost,127.0.0.1

# ============ DATABASE ============
DATABASE_URL=sqlite:///./roshni.db
# For production PostgreSQL, use:
# DATABASE_URL=postgresql://user:password@localhost:5432/roshni_db

# ============ ALGORAND BLOCKCHAIN ============
ALGORAND_NETWORK=testnet
ALGORAND_NODE_URL=https://testnet-api.algonode.cloud
ALGORAND_INDEXER_URL=https://testnet-idx.algonode.cloud

# PASTE YOUR MNEMONIC HERE (25 words you saved earlier)
# ⚠️ KEEP THIS SECRET! Never commit to Git!
ALGORAND_ADMIN_MNEMONIC=abandon ability ability abandon ability ability... (your 25 words)

# Leave as 0 for now, will update after SUN ASA deployment
SUN_ASA_ID=0

# ============ GEMINI AI (Optional) ============
# PASTE YOUR GEMINI API KEY HERE
# Get from: https://makersuite.google.com/app/apikeys
# If empty, app uses fallback rule-based matching
GEMINI_API_KEY=your_gemini_api_key_here

# ============ DISCOM CONFIGURATION ============
DISCOM_FIXED_CHARGE=100.0          # Monthly fixed charge in ₹
DISCOM_ADMIN_FEE_PERCENT=2.0       # % of transactions
DISCOM_EXPORT_RATE=8.0             # ₹/kWh solar export to grid
DISCOM_GRID_RATE=12.0              # ₹/kWh purchase from grid

# ============ SOLAR POOL RATES ============
SOLAR_EXPORT_RATE=10.0             # ₹/kWh (for local pool)
SOLAR_POOL_RATE=9.0                # ₹/kWh (consumer purchase)

# ============ IoT AUTHENTICATION ============
# Change this to a random string for security
IOT_AUTH_TOKEN=iot_secret_token_12345
```

**⚠️ IMPORTANT SECURITY NOTES:**

- Never commit `.env` to Git (it's in `.gitignore`)
- Keep mnemonic & API keys private
- Use different keys for production

### Step 5: Initialize Database

```bash
# This creates SQLite database automatically
python main.py
```

You should see output like:

```
🌞 ROSHNI Backend Starting...
Environment: development
Debug mode: true
INFO:     Uvicorn running on http://0.0.0.0:8000
```

Press `Ctrl+C` to stop (this was just to initialize).

### Step 6: Run Backend

```bash
# Make sure venv is still activated (see (venv) prefix)
python main.py
```

**Expected Output:**

```
🌞 ROSHNI Backend Starting...
INFO:     Uvicorn running on http://0.0.0.0:8000
```

✅ **Backend is running!** Leave this terminal open.

### Step 7: Verify Backend

Open **new terminal/tab** and test:

```bash
# Health check
curl http://localhost:8000/health

# Should return JSON:
# {"status":"healthy","service":"ROSHNI Backend",...}

# API Swagger UI
# Visit in browser: http://localhost:8000/docs
```

---

## Frontend Setup

### Step 1: Install Dependencies

Open **new terminal** (keep backend running):

```bash
cd ~/roshni/frontend  # Adjust path if different

# Install Node packages
npm install

# This will create node_modules/ folder (~500MB)
```

### Step 2: Create & Configure .env

```bash
# Copy example
cp .env.example .env

# Edit the file
nano .env
```

**Fill in values:**

```bash
# Backend API URL (must match backend BACKEND_URL)
VITE_BACKEND_URL=http://localhost:8000

# Algorand Network (testnet for demo)
VITE_ALGORAND_NETWORK=testnet
VITE_ALGORAND_NODE_URL=https://testnet-api.algonode.cloud
VITE_ALGORAND_INDEXER_URL=https://testnet-idx.algonode.cloud

# Will update after SUN ASA deployment
VITE_SUN_ASA_ID=0

# Optional: ElevenLabs API for voice features (skip for now)
VITE_ELEVENLABS_API_KEY=
```

### Step 3: Run Frontend

```bash
npm run dev
```

**Expected Output:**

```
VITE v5.0.0  ready in 234 ms

➜  Local:   http://localhost:5173/
➜  press h to show help
```

✅ **Frontend is running!**

### Step 4: Access Frontend

Open browser to: **http://localhost:5173**

You should see:

- 🌞 ROSHNI header
- Feeder selector (FDR_12, FDR_15, etc.)
- Navigation tabs (Seller, Buyer, Bills, Blockchain, Admin)
- Dark mode toggle (☀️/🌙)

---

## IoT Setup (Optional)

### Prerequisites

- NodeMCU ESP8266 development board (~₹300)
- USB Micro cable
- Arduino IDE installed
- Patience! 😊

### Step 1: Install Arduino IDE & Board Support

```bash
# If not installed:
sudo apt install -y arduino-ide

# OR download from: https://www.arduino.cc/en/software
```

### Step 2: Add ESP8266 Board Support

1. Open Arduino IDE
2. **File** → **Preferences**
3. In **"Additional Board Manager URLs"** field, paste:
   ```
   http://arduino.esp8266.com/stable/package_esp8266com_index.json
   ```
4. Click **OK**
5. **Tools** → **Board** → **Board Manager**
6. Search for **"ESP8266"**
7. Click **Install** (wait ~2 minutes)

### Step 3: Configure Arduino IDE

```
Tools → Board → NodeMCU 1.0 (ESP-12E Module)
Tools → Upload Speed → 115200
Tools → Flash Size → 4MB (FS: 2MB OTA:~1019KB)
Tools → Port → /dev/ttyUSB0 (or COM3 on Windows)
```

### Step 4: Edit & Upload Firmware

1. Open `iot/solar_prosumer.ino` in Arduino IDE
2. **Edit WiFi Credentials** (lines 14-15):
   ```cpp
   const char* ssid = "YOUR_WIFI_SSID";            // Change this!
   const char* password = "YOUR_WIFI_PASSWORD";    // Change this!
   ```
3. **Optional**: Change houseId (line 29):
   ```cpp
   const String houseId = "HOUSE_FDR12_001";  // Or any house
   ```
4. **Verify** (Ctrl+R):
   - Should compile without errors
   - Watch the output
5. **Upload** (Ctrl+U):
   - You'll see progress bar
   - Should finish with: "SHA1: ..." message

### Step 5: Monitor IoT Device

```bash
# Open Serial Monitor in Arduino IDE
# Tools → Serial Monitor
# Set baud rate to: 115200

# You should see:
# 🌞 ROSHNI IoT Startup
# ✓ Setup complete
# Connecting to WiFi: YOUR_SSID
# ✓ WiFi Connected
# IP: 192.168.x.xxx
# [HTTP] Sending generation update...
# ✓ Update successful
```

✅ **IoT is working!**

---

## Blockchain Setup

### Step 1: Create Admin Account

```bash
cd blockchain

python3 << 'EOF'
from algosdk import account
from algosdk.mnemonic import from_private_key

# Generate new account
pk, addr = account.generate_account()
mnem = from_private_key(pk)

print("=" * 60)
print("ALGORAND ACCOUNT CREATED")
print("=" * 60)
print(f"\nAddress: {addr}")
print(f"\nMnemonic (SAVE THIS SECURELY):")
print(mnem)
print(f"\nPrivate Key (KEEP PRIVATE):")
print(pk)
print("=" * 60)
EOF
```

**Save the output! You'll need the mnemonic.**

### Step 2: Get Testnet ALGO Coins

1. Go to: https://bank.testnet.algorand.org/
2. Paste your **Address** (from above)
3. Click **"Dispense"**
4. Wait 1 minute
5. Check balance with script above

### Step 3: Deploy SUN ASA Token

```bash
# Make sure you have testnet ALGO first!

python3 deploy.py "your 25 word mnemonic here"

# Example:
# python3 deploy.py "abandon ability ability ... (25 words)"
```

**Expected Output:**

```
🌞 Deploying SUN ASA on TESTNET...
Admin: 7X3U7...
Balance: 400.00 ALGO
Waiting for confirmation...
✅ SUN ASA deployed!
ASA ID: 12345678
Explorer: https://testnet.algoexplorer.io/asset/12345678
```

### Step 4: Update Backend with ASA ID

When you see "ASA ID: 12345678", update backend `.env`:

```bash
# Edit backend/.env
nano ../backend/.env

# Change this line:
SUN_ASA_ID=12345678  # Put your ASA ID
```

### Step 5: Verify Blockchain Setup

```bash
# Test network connection
python3 << 'EOF'
from algosdk.v2client import algod

client = algod.AlgodClient("", "https://testnet-api.algonode.cloud")
status = client.status()
print(f"Latest Round: {status.get('last-round')}")
print("✓ Connected to Algorand testnet")
EOF
```

---

## Verification & Testing

### 1. Health Check

**Backend:**

```bash
curl http://localhost:8000/health
# Returns: {"status":"healthy",...}
```

**Frontend:**

```bash
# Should load at http://localhost:5173
# Should show all navigation tabs and feeder selector
```

### 2. Test API Endpoints

**Create generation data:**

```bash
curl -X POST http://localhost:8000/api/iot/update \
  -H "Content-Type: application/json" \
  -d '{
    "house_id": "HOUSE_FDR12_001",
    "generation_kwh": 2.5,
    "device_id": "NodeMCU_001",
    "signal_strength": -65.0,
    "auth_token": "iot_secret_token_12345"
  }'

# Should return:
# {"status":"recorded","allocation_status":"sufficient",...}
```

**Submit consumer demand:**

```bash
curl -X POST http://localhost:8000/api/demand/submit \
  -H "Content-Type: application/json" \
  -d '{
    "house_id": "HOUSE_FDR12_002",
    "demand_kwh": 5.0,
    "priority_level": 7,
    "duration_hours": 1.0
  }'

# Should return:
# {"demand_id":1,"allocation_status":"matched",...}
```

**Get dashboard:**

```bash
curl http://localhost:8000/api/dashboard/HOUSE_FDR12_001

# Should return complete dashboard data with pool state
```

### 3. Frontend Testing

1. Open http://localhost:5173
2. Select feeder: **FDR_12**
3. Select house: **HOUSE_FDR12_001**
4. Go to **Seller** tab → See "Live Generation" (should be 0 initially)
5. Go to **Buyer** tab → Submit demand for 5 kWh
6. See allocation result
7. Go to **Bills** → Generate bill for current month
8. Go to **Blockchain** → Verify network params

### 4. Import Postman Collection

1. Download [Postman](https://www.postman.com/downloads/)
2. Create free account
3. **File** → **Import**
4. Select `postman/ROSHNI_Collection.json`
5. Set variable: `backend_url = http://localhost:8000`
6. Test all 25 endpoints!

---

## Troubleshooting

### Backend Won't Start

**Problem:** "Port 8000 already in use"

```bash
# Kill process using port 8000
lsof -i :8000
kill -9 <PID>
# Then try again: python main.py
```

**Problem:** "ModuleNotFoundError: No module named 'fastapi'"

```bash
# Forgot to activate venv?
source venv/bin/activate  # Linux/Mac
# OR
venv\Scripts\activate     # Windows

# Then reinstall:
pip install -r requirements.txt
```

**Problem:** "SQLAlchemy: operational error"

```bash
# Database file corrupted?
rm roshni.db
python main.py  # Creates fresh database
```

### Frontend Won't Connect to Backend

**Problem:** CORS error in browser console

```
Access to XMLHttpRequest blocked by CORS policy
```

**Solution:**

1. Check backend `.env`: `FRONTEND_URL=http://localhost:5173`
2. Check backend is running: `curl http://localhost:8000/health`
3. Restart backend if you changed .env

**Problem:** Cannot connect to "localhost:8000"

```bash
# Frontend might be on different IP, edit .env:
VITE_BACKEND_URL=http://YOUR_LOCAL_IP:8000
# Find IP: hostname -I
```

### IoT Won't Upload

**Problem:** "java.io.IOException: Error opening serial port"

```bash
# Port doesn't exist, check:
ls /dev/ttyUSB*  # Linux
# Should show: /dev/ttyUSB0

# If nothing, NodeMCU not connected or driver missing
# Install CH340 driver: https://sparks.gogo.co.nz/ch340.html
```

**Problem:** "Sketch too large"

```bash
# Sketch is bigger than flash memory
# Reduce flash size: Tools → Flash Size → 4MB
# Or use different board
```

**Problem:** "Fatal exception: Stack smashing detected"

```bash
# Stack overflow, likely WiFi issue
# Check SSID/password in code
# Reduce other variables
```

### Blockchain Issues

**Problem:** "Invalid mnemonic"

```bash
# Make sure it's exactly 25 words
# No extra spaces, commas, or periods
echo "your mnemonic text" | wc -w  # Should be 25
```

**Problem:** "Insufficient balance" (deploying SUN ASA)

```bash
# Need at least 1 ALGO
# Go to https://bank.testnet.algorand.org/
# Paste your address and dispense again
```

**Problem:** "Network error: Connection refused"

```bash
# Algorand node might be down
# Try different node URL:
ALGORAND_NODE_URL=https://mainnet-api.algonode.cloud
```

### Database Issues

**Problem:** "database is locked"

```bash
# Multiple processes accessing SQLite
# For development, only run one instance:
pkill -f "python main.py"
# Wait 5 seconds
python main.py
```

**Problem:** "no such table: houses"

```bash
# Database not initialized
# Delete old database and restart:
rm roshni.db
python main.py
```

---

## Common Configuration Issues

### Issue: Gemini API not working

**Problem:** AI responses are not improving allocation

```
Solution:
1. Verify API key at: https://makersuite.google.com/app/apikeys
2. Check if key is valid (copy again if needed)
3. Update backend/.env: GEMINI_API_KEY=your_new_key
4. Restart backend: Ctrl+C then python main.py
```

### Issue: Pool state always empty

**Problem:** Demand submitted but no allocation happens

```
Solution:
1. First send generation data: curl ... /iot/update
2. Wait 5 seconds
3. Then submit demand: curl ... /demand/submit
4. Order matters: Supply must exist before demand!

Or check:
- Backend logs for errors
- curl http://localhost:8000/api/dashboard/HOUSE_FDR12_001
- Should show current_supply > 0
```

### Issue: Bills showing ₹0

**Problem:** No charges or credits calculated

```
Solution:
1. Generate generation & demand records first
2. Let them accumulate for a day (or manually seed):
   - Use Postman to create records
   - Or wait and keep app running
3. Generate bill for current month:
   curl -X POST http://localhost:8000/api/billing/generate/HOUSE_FDR12_001/2024-03
```

---

## Quick Start Checklist

- [ ] Python 3.10+ installed
- [ ] Node.js 18+ installed
- [ ] Cloned ROSHNI repo
- [ ] Created backend venv
- [ ] Installed backend dependencies
- [ ] Got Gemini API key
- [ ] Got Algorand testnet account & ALGO coins
- [ ] Created backend .env with all keys
- [ ] Backend running on http://localhost:8000
- [ ] Created frontend .env
- [ ] Frontend running on http://localhost:5173
- [ ] Tested API endpoints with cURL
- [ ] Imported Postman collection
- [ ] (Optional) Uploaded IoT firmware

---

## Next Steps

Once everything is running:

1. **Explore Dashboards**: http://localhost:5173
2. **Read DEMO.md**: Understand the system with real scenarios
3. **Read API.md**: Learn all endpoints in detail
4. **Read ARCHITECTURE.md**: Understand design patterns
5. **Deploy to Production**: Follow DEPLOYMENT.md for Vultr

---

## Support

If you get stuck:

1. **Check logs**:

   ```bash
   # Backend logs appear in same terminal
   # Look for [ERROR] or exceptions
   ```

2. **Check database**:

   ```bash
   # View SQLite database
   sqlite3 backend/roshni.db
   > .tables   # Shows all tables
   > SELECT count(*) FROM houses;  # Check data
   > .quit
   ```

3. **Check API**:

   ```bash
   # Use Postman or curl to test endpoints
   # Check backend/logs/ folder for debug logs
   ```

4. **Restart Everything**:

   ```bash
   # Kill backend
   Ctrl+C (in backend terminal)

   # Kill frontend
   Ctrl+C (in frontend terminal)

   # Start fresh
   python main.py  # backend
   npm run dev      # frontend
   ```

---

**🎉 You're all set! ROSHNI is ready to use.**

Start with the frontend at http://localhost:5173 and explore!
