# ROSHNI Buyer IoT Setup (HOUSE_FDR12_002)

## Overview
The buyer side uses an **ESP32 with a Potentiometer** to generate demand automatically. This removes manual form entry and makes demand submission fully automated based on real-time energy requirements.

## Hardware Requirements

### Components
- **ESP32 (NodeMCU-32S)** - Microcontroller
- **Potentiometer (10kOhm variable resistor)** - Simulates energy demand (0-5 kWh)
- **OLED Display (SH1106 128x64)** - Real-time status feedback
- **WiFi Network** - For backend connectivity
- **USB Cable** - For programming and power

### Wiring

```
POT_PIN (A0)     → GPIO 35 (ADC pin)
GND              → GND
+3.3V            → +3.3V

OLED:
- SDA            → GPIO 21 (I2C Data)
- SCL            → GPIO 22 (I2C Clock)
- GND            → GND
- +3.3V          → +3.3V
```

## Installation Steps

### 1. Arduino IDE Setup
```bash
# Install ESP32 board support via Arduino IDE:
# Preferences → Additional Boards Manager URLs:
# https://dl.espressif.com/dl/package_esp32_index.json

# Then install: ESP32 by Espressif Systems
```

### 2. Required Libraries
Install via Arduino IDE → Sketch → Include Library → Manage Libraries:
- **WiFi.h** (built-in)
- **HTTPClient.h** (built-in)
- **ArduinoJson** v6.x
- **Wire.h** (built-in)
- **U8g2lib** v2.34+

### 3. Configuration
Edit `buyer_esp32.ino` and update:
```cpp
const char* ssid = "your_wifi_name";
const char* password = "your_wifi_password";
const char* backendUrl = "https://your-backend-url/api/iot/demand";
const char* auth_token = "iot_secret_token_12345";
```

### 4. Upload Code
1. Connect ESP32 via USB
2. Select Board: Tools → Board → ESP32 → NodeMCU-32S
3. Select Port: Tools → Port → COM4 (or your USB port)
4. Sketch → Upload

## Operation

### How it Works

1. **Reads Potentiometer (every 200ms)**
   - Analog value 0-4095 maps to demand 0-5.0 kWh
   - Multiple samples (10x) for noise filtering

2. **Sends to Backend (every 5 seconds)**
   - POST to `/api/iot/demand` with JSON payload
   - Backend automatically triggers matching engine

3. **Receives Allocation**
   - Backend responds with pool/grid split
   - OLED displays: Source (POOL/HYBRID/GRID) and amounts

4. **Frontend Auto-Updates**
   - Buyer Dashboard polls `/api/iot/demand-status/HOUSE_FDR12_002`
   - Displays current demand and allocation in real-time

### OLED Display Layout

```
ROSHNI BUYER
========================
Demand: 2.35 kWh
Source: HYBRID
[Pool]2.1 [Grid]0.2
```

### Serial Monitor Output

```
[*] Pot: 2345 -> Demand: 2.35 kWh

==== SENDING DEMAND TO BACKEND ====
[*] Payload: {"auth_token":"...","house_id":"HOUSE_FDR12_002","device_id":"NodeMCU_002_Buyer","demand_kwh":2.35}
[OK] Response Code: 200
[OK] Allocation: Pool=2.10 Grid=0.25 Source=HYBRID
```

## Automatic Demand Generation

### No Manual Entry Required
- ~~Form input removed~~ ❌
- ~~Submit button~~  ❌
- Only potentiometer controls demand ✅

### Automatic Matching
- Every 5 seconds, demand sent to backend
- Backend calculates allocation instantly
- Source determined by pool energy level

### Frontend Integration
- **Old**: Manual form → Submit → Wait for response
- **New**: Potentiometer → Auto-send → Real-time allocation display

## Backend Endpoints

### Send Demand (ESP32 → Backend)
```http
POST /api/iot/demand

{
  "auth_token": "iot_secret_token_12345",
  "house_id": "HOUSE_FDR12_002",
  "device_id": "NodeMCU_002_Buyer",
  "demand_kwh": 2.35
}

Response:
{
  "status": "matched",
  "demand_kwh": 2.35,
  "allocated_kwh": 2.10,
  "grid_required_kwh": 0.25,
  "allocation_status": "partial",
  "ai_reasoning": "...",
  "sun_tokens_minted": 0.25
}
```

### Get Demand Status (Frontend → Backend)
```http
GET /api/iot/demand-status/HOUSE_FDR12_002

Response:
{
  "house_id": "HOUSE_FDR12_002",
  "current_demand_kwh": 2.35,
  "device_online": true,
  "allocation": {
    "allocated_kwh": 2.10,
    "grid_required_kwh": 0.25,
    "allocation_status": "partial"
  }
}
```

## Troubleshooting

### Serial Monitor Shows Nothing
- Check baud rate is 115200
- Verify USB cable is connected
- Reset board (press RST button)

### WiFi Fails to Connect
- Verify SSID and password in code
- Check if WiFi is 2.4GHz (ESP32 doesn't support 5GHz)
- Ensure router allows microcontroller connections

### Potentiometer Readings Erratic
- Add more averaging samples (increase loop count)
- Check potentiometer wiring
- Verify ADC calibration

### OLED Not Displaying
- Check I2C address (scan with I2C scanner sketch)
- Verify SDA/SCL pins (must be 21/22 for this board)
- Ensure pull-up resistors on I2C bus

### Backend Connection Error
- Verify backend URL is correct
- Check auth token matches environment variable
- Test endpoint with Postman first

## Testing

### Manual Test (Postman)
```bash
POST http://localhost:8000/api/iot/demand
Content-Type: application/json

{
  "auth_token": "iot_secret_token_12345",
  "house_id": "HOUSE_FDR12_002",
  "device_id": "NodeMCU_002_Buyer",
  "demand_kwh": 2.5
}
```

### Simulate Potentiometer
- Turn potentiometer dial slowly
- Watch OLED update in real-time
- Check Serial Monitor for demand values

### Verify Allocation
- Pool should decrease if demand increases
- Grid should increase if pool insufficient
- Allocation status changes based on availability

## Security Notes

⚠️ **Change auth token** from default in production:
```cpp
const char* auth_token = "your-secret-token-here";
```

Update matching `.env` file:
```
IOT_AUTH_TOKEN=your-secret-token-here
```

## Performance Specs

| Metric | Value |
|--------|-------|
| Demand Polling Interval | 5 seconds |
| ADC Sample Size | 10 samples |
| Potentiometer Range | 0-5.0 kWh |
| WiFi Reconnect Attempts | 20 |
| Minimum Demand Threshold | 0.1 kWh |
| OLED Refresh | Real-time |

## Future Enhancements

- [ ] Flow sensor for real demand instead of potentiometer
- [ ] Temperature compensation for accuracy
- [ ] Time-based demand prediction
- [ ] Multiple demand profiles (morning/evening/night)
- [ ] Offline caching of demand values
- [ ] Solar radiation sensor integration
- [ ] Wireless pairing with seller ESP32

## See Also
- [Seller IoT Setup](./solar_prosumer/solar_prosumer.ino)
- [Backend IoT Routes](../backend/app/routes/iot.py)
- [IoT Service](../backend/app/services/iot_service.py)
