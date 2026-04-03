# ESP32 IoT Setup - Cloud Backend (Render)

## Status: ✅ READY TO CONNECT

Your ESP32 devices will connect to the **cloud backend** on Render.com

---

## 🔧 Setup Steps

### 1. **Upload to ESP32**

**Seller Device:**
- File: [`seller_esp32_final.ino`](iot/seller_esp32_final.ino)
- device_id: `NodeMCU_001`
- house_id: `HOUSE_FDR12_001`
- Generates solar power (POT_PIN = 32)
- Sends to: `https://roshni-backend-o7al.onrender.com/api/iot/update`

**Buyer Device:**
- File: [`buyer_esp32_final.ino`](iot/buyer_esp32_final.ino)
- device_id: `NodeMCU_002`
- house_id: `HOUSE_FDR12_002`
- Consumes energy (POT_PIN = 35)
- Sends to: `https://roshni-backend-o7al.onrender.com/api/iot/update`

### 2. **WiFi Credentials**

Update WiFi SSID and password in both files:

**Seller:**
```cpp
const char* ssid = "test1";
const char* password = "12345678";
```

**Buyer:**
```cpp
const char* ssid = "Khushi";
const char* password = "9876543210";
```

---

## 📡 Expected Behavior

### Seller Device (Solar Generation)
- Reads potentiometer on **pin 32**
- Sends every 5 seconds to backend
- Shows: `Gen: X.XX kWh` on OLED
- RGB LED: 🔴 RED (low) → 🟢 GREEN (normal) → 🔵 BLUE (high)

### Buyer Device (Demand)
- Reads potentiometer on **pin 35**
- Samples 10 times + smoothing
- Sends every 5 seconds to backend
- Shows: `Demand: X.XX kW | Pool: X.X | Grid: X.X`
- Possible statuses: `POOL`, `HYBRID`, `GRID`, `READING`, `NET_FAIL`

---

## 🔌 Database Houses

Both houses exist on the cloud Render database:

| House ID | Type | Device | Purpose |
|----------|------|--------|---------|
| `HOUSE_FDR12_001` | Seller | NodeMCU_001 | Solar Generation |
| `HOUSE_FDR12_002` | Buyer | NodeMCU_002 | Energy Demand |

**Auth Token (all devices):** `iot_secret_token_12345`

---

## 🧪 Testing Without ESP32

Test endpoints manually using the Postman collection:

File: `postman/ROSHNI_Collection.json`

Or manually POST:

### Test Seller Generation
```bash
POST https://roshni-backend-o7al.onrender.com/api/iot/update

{
  "auth_token": "iot_secret_token_12345",
  "device_id": "NodeMCU_001",
  "generation_kwh": 2.5,
  "house_id": "HOUSE_FDR12_001",
  "signal_strength": -50
}
```

### Test Buyer Demand
```bash
POST https://roshni-backend-o7al.onrender.com/api/iot/update

{
  "auth_token": "iot_secret_token_12345",
  "device_id": "NodeMCU_002",
  "demand_kwh": 1.8,
  "house_id": "HOUSE_FDR12_002",
  "signal_strength": -55
}
```

---

## ✅ Troubleshooting

| Problem | Solution |
|---------|----------|
| ESP32 can't connect to WiFi | Check SSID & password match your network |
| `NET_FAIL` on OLED | Check internet connectivity, backend might be sleeping|
| `ERR_400` | Check JSON payload format |
| `ERR_401` | Invalid auth token |
| `ERR_404` | House doesn't exist in database |
| `ERR_503` | Render backend is waking up (first request takes time)|

---

## 🌐 Backend Status

Backend: `https://roshni-backend-o7al.onrender.com`

API Docs: `https://roshni-backend-o7al.onrender.com/docs`

**Note:** Free tier Render will sleep after inactivity. First request may take 30-60 seconds as it wakes up.



