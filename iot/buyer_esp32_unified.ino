#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>
#include <Wire.h>
#include <U8g2lib.h>
#include <WiFiClientSecure.h>

// -------- OLED --------
U8G2_SH1106_128X64_NONAME_F_HW_I2C u8g2(U8G2_R0, U8X8_PIN_NONE);

// -------- WIFI --------
const char* ssid = "test1";
const char* password = "12345678";

// -------- BACKEND --------
// ✅ SAME ENDPOINT AS SELLER
const char* backendUrl = "https://roshni-backend-o7al.onrender.com/api/iot/update";

// -------- AUTH --------
const char* auth_token = "iot_secret_token_12345";
const char* device_id = "NodeMCU_002";
const char* house_id = "HOUSE_FDR12_002";

// -------- PINS --------
const int POT_PIN = 35;

// -------- TIMER --------
unsigned long lastUpdate = 0;
int updateInterval = 5000;

// -------- SMOOTHING --------
float smoothDemand = 0;


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
    Serial.println("\n✅ WiFi Connected");
    Serial.println(WiFi.localIP());
  }
  else
  {
    Serial.println("\n❌ WiFi Failed");
  }
}


// -------- OLED DISPLAY --------
void updateDisplay(String source, float demand, float pool, float grid)
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
  u8g2.print("Source: ");
  u8g2.print(source);

  u8g2.setCursor(0, 52);
  u8g2.print("Pool: ");
  u8g2.print(pool, 1);

  u8g2.setCursor(64, 52);
  u8g2.print("Grid: ");
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

  // ✅ EXACT SAME ADC SETTINGS AS SELLER
  analogReadResolution(12);
  analogSetPinAttenuation(POT_PIN, ADC_11db);

  pinMode(POT_PIN, INPUT);

  connectWiFi();
}


// -------- LOOP --------
void loop()
{
  // WiFi check
  if (WiFi.status() != WL_CONNECTED)
  {
    Serial.println("WiFi lost, reconnecting...");
    connectWiFi();
  }

  // -------- POT READ (with smoothing) --------
  int potValue = analogRead(POT_PIN);

  float rawDemand = (float)potValue / 4095.0 * 5.0;
  smoothDemand = (0.7 * smoothDemand) + (0.3 * rawDemand);
  float demand_kwh = smoothDemand;

  Serial.print("Pot: ");
  Serial.print(potValue);
  Serial.print(" | Demand: ");
  Serial.println(demand_kwh, 3);

  // OLED live update
  updateDisplay("ADJUST", demand_kwh, 0, 0);

  // -------- PERIODIC BACKEND SEND --------
  if (millis() - lastUpdate > updateInterval)
  {
    lastUpdate = millis();

    Serial.println("\n===== SENDING TO BACKEND =====");

    // ✅ USE EXACT SAME CONNECTION LOGIC AS SELLER
    WiFiClientSecure client;
    client.setInsecure();

    HTTPClient http;
    http.setTimeout(10000);

    if (!http.begin(client, backendUrl))
    {
      Serial.println("❌ HTTP begin failed");
      updateDisplay("NO NET", demand_kwh, 0, 0);
      return;
    }

    // ✅ EXACT SAME HEADERS AS SELLER
    http.addHeader("Connection", "close");
    http.addHeader("Content-Type", "application/json");

    // ✅ JSON WITH GENERATION_KWH=0 AND DEMAND_KWH POPULATED
    // The backend determines device type based on which field is > 0
    StaticJsonDocument<250> doc;
    doc["auth_token"] = auth_token;
    doc["device_id"] = device_id;
    doc["generation_kwh"] = 0;  // ✅ Seller field = 0 (not a seller)
    doc["demand_kwh"] = demand_kwh;  // ✅ FOCUS ON DEMAND
    doc["house_id"] = house_id;
    doc["signal_strength"] = WiFi.RSSI();

    String payload;
    serializeJson(doc, payload);

    Serial.print("Payload: ");
    Serial.println(payload);

    int httpCode = http.POST(payload);

    Serial.print("HTTP Code: ");
    Serial.println(httpCode);

    String source = "ERROR";

    if (httpCode > 0)
    {
      Serial.println("✅ Backend SUCCESS");

      String response = http.getString();
      Serial.println(response);

      StaticJsonDocument<300> resDoc;
      DeserializationError error = deserializeJson(resDoc, response);

      if (!error)
      {
        String status = resDoc["status"] | "unknown";
        float pool = resDoc["allocated_kwh"] | 0;
        float grid = resDoc["grid_required_kwh"] | 0;

        Serial.print("Response Status: ");
        Serial.println(status);

        if (grid == 0)
          source = "POOL";
        else if (pool > 0)
          source = "HYBRID";
        else
          source = "GRID";

        updateDisplay(source, demand_kwh, pool, grid);
      }
      else
      {
        Serial.println("JSON Parse Error");
        updateDisplay("PARSE_ERR", demand_kwh, 0, 0);
      }
    }
    else
    {
      Serial.print("❌ Backend FAILED: ");
      Serial.println(httpCode);
      updateDisplay("FAILED", demand_kwh, 0, 0);
    }

    http.end();
    client.stop();
  }
}
