#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>
#include <Wire.h>
#include <U8g2lib.h>

// -------- OLED --------
U8G2_SH1106_128X64_NONAME_F_HW_I2C u8g2(U8G2_R0, U8X8_PIN_NONE);

// -------- WIFI --------
const char* ssid = "Khushi";
const char* password = "9876543210";

// -------- BACKEND (CLOUD - Render) --------
// This connects to the ROSHNI backend running on Render.com
const char* backendUrl = "https://roshni-backend-o7al.onrender.com/api/iot/update";

// -------- AUTH --------
const char* auth_token = "iot_secret_token_12345";
const char* device_id = "NodeMCU_002";
const char* house_id = "HOUSE_FDR12_002";

// -------- PINS --------
const int POT_PIN = 35;    // ESP32 ADC pin (must be ADC1 for WiFi to work)

// -------- TIMER --------
unsigned long lastUpdate = 0;
int updateInterval = 5000;

// -------- SMOOTHING --------
float smoothDemand = 0;
int readCount = 0;


// -------- WIFI --------
void connectWiFi()
{
  Serial.println("Connecting WiFi...");
  WiFi.begin(ssid, password);

  int attempts = 0;
  while (WiFi.status() != WL_CONNECTED && attempts < 20)
  {
    delay(500);
    Serial.print(".");
    attempts++;
  }

  if (WiFi.status() == WL_CONNECTED)
  {
    Serial.println("\n✓ WiFi Connected");
    Serial.print("IP: ");
    Serial.println(WiFi.localIP());
  }
  else
  {
    Serial.println("\n✗ WiFi Failed");
  }
}


// -------- OLED DISPLAY --------
void updateDisplay(String status, float demand, float pool, float grid)
{
  u8g2.clearBuffer();

  u8g2.setFont(u8g2_font_6x10_tr);
  u8g2.drawStr(0, 10, "ROSHNI BUYER");
  u8g2.drawLine(0, 12, 128, 12);

  u8g2.setCursor(0, 25);
  u8g2.print("Demand: ");
  u8g2.print(demand, 2);
  u8g2.print(" kW");

  u8g2.setCursor(0, 38);
  u8g2.print("Status: ");
  u8g2.print(status);

  u8g2.setCursor(0, 52);
  u8g2.print("P:");
  u8g2.print(pool, 1);
  u8g2.print(" G:");
  u8g2.print(grid, 1);

  u8g2.sendBuffer();
}


// -------- SETUP --------
void setup()
{
  Serial.begin(115200);
  delay(1000);

  Serial.println("=================================");
  Serial.println("BUYER IoT DEVICE STARTED");
  Serial.println("=================================");

  Wire.begin(21, 22);
  u8g2.begin();

  // ADC Configuration
  analogReadResolution(12);
  analogSetPinAttenuation(POT_PIN, ADC_11db);

  // Test potentiometer immediately
  Serial.println("Testing potentiometer on pin 35...");
  for (int i = 0; i < 5; i++) {
    int testVal = analogRead(POT_PIN);
    Serial.print("POT Read ");
    Serial.print(i);
    Serial.print(": ");
    Serial.println(testVal);
    delay(500);
  }

  connectWiFi();
}


// -------- LOOP --------
void loop()
{
  // WiFi check
  if (WiFi.status() != WL_CONNECTED)
  {
    connectWiFi();
  }

  // -------- POT READ (MULTIPLE SAMPLES) --------
  int total = 0;
  for (int i = 0; i < 10; i++)
  {
    int raw = analogRead(POT_PIN);
    total += raw;
    delay(2);
  }
  int potValue = total / 10;

  // APPLY SMOOTHING
  float rawDemand = (float)potValue / 4095.0 * 5.0;
  smoothDemand = (0.8 * smoothDemand) + (0.2 * rawDemand);  // More smoothing
  float demand_kwh = smoothDemand;

  // Debug every 10 reads
  readCount++;
  if (readCount % 10 == 0) {
    Serial.print("[");
    Serial.print(readCount);
    Serial.print("] Pot: ");
    Serial.print(potValue);
    Serial.print(" | Demand: ");
    Serial.print(demand_kwh, 3);
    Serial.print(" kWh | WiFi: ");
    Serial.println(WiFi.RSSI());
  }

  // SHOW OLED WHILE READING
  updateDisplay("READING", demand_kwh, 0, 0);

  // -------- PERIODIC BACKEND SEND (Every 5 seconds) --------
  if (millis() - lastUpdate > updateInterval)
  {
    lastUpdate = millis();

    Serial.println("\n===== ATTEMPT TO SEND TO BACKEND =====");
    Serial.print("Demand: ");
    Serial.print(demand_kwh);
    Serial.print(" kWh | WiFi RSSI: ");
    Serial.println(WiFi.RSSI());

    // ========== CREATE JSON PAYLOAD ==========
    StaticJsonDocument<250> doc;
    doc["auth_token"] = auth_token;
    doc["device_id"] = device_id;
    doc["generation_kwh"] = 0;  // This is a buyer
    doc["demand_kwh"] = demand_kwh;  // Focus on demand
    doc["house_id"] = house_id;
    doc["signal_strength"] = WiFi.RSSI();

    String payload;
    serializeJson(doc, payload);
    Serial.println(payload);

    // ========== SEND HTTP REQUEST ==========
    HTTPClient http;
    http.setTimeout(15000);  // LONGER TIMEOUT

    Serial.print("Connecting to: ");
    Serial.println(backendUrl);

    // HTTPS client with certificate validation disabled
    WiFiClientSecure client;
    client.setInsecure();  // Skip SSL verification for Render testing

    if (!http.begin(client, backendUrl))
    http.addHeader("Content-Type", "application/json");

    int httpCode = http.POST(payload);

    Serial.print("HTTP Response Code: ");
    Serial.println(httpCode);

    if (httpCode > 0)
    {
      Serial.println("✓ RESPONSE RECEIVED");

      String response = http.getString();
      Serial.print("Response: ");
      Serial.println(response);

      // Parse response
      StaticJsonDocument<500> resDoc;
      DeserializationError error = deserializeJson(resDoc, response);

      if (!error)
      {
        String status = resDoc["status"] | "unknown";
        float pool = resDoc["allocated_kwh"] | 0;
        float grid = resDoc["grid_required_kwh"] | 0;

        Serial.print("Status: ");
        Serial.println(status);

        String source = "?";
        if (grid == 0 && pool > 0)
          source = "POOL";
        else if (pool > 0 && grid > 0)
          source = "HYBRID";
        else
          source = "GRID";

        updateDisplay(source, demand_kwh, pool, grid);
      }
      else
      {
        Serial.println("ERROR: JSON parse failed");
        updateDisplay("JSON_ERR", demand_kwh, 0, 0);
      }
    }
    else
    {
      Serial.print("ERROR: HTTP Code ");
      Serial.println(httpCode);

      // Show error code on OLED
      String errMsg = "ERR_";
      errMsg += String(httpCode);
      updateDisplay(errMsg, demand_kwh, 0, 0);
    }

    http.end();
    
    Serial.println("===== END SEND =====\n");
  }

  delay(200);
}
