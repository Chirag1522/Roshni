#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>
#include <Wire.h>
#include <U8g2lib.h>

// -------- OLED (SSD1306 I2C) --------
U8G2_SH1106_128X64_NONAME_F_HW_I2C u8g2(U8G2_R0, U8X8_PIN_NONE);

// -------- WIFI --------
const char* ssid = "test1";
const char* password = "12345678";

// -------- BACKEND --------
const char* backendUrl = "https://roshni-backend-o7al.onrender.com/api/iot/demand";

// -------- DEVICE --------
const char* house_id = "HOUSE_FDR12_002";
const char* device_id = "NodeMCU_002_Buyer";

// -------- PINS --------
const int POT_PIN = A0;   // Analog pin for potentiometer (generates demand)

// -------- TIMER --------
unsigned long lastUpdate = 0;
int updateInterval = 5000;   // Send every 5 seconds

// -------- AUTH --------
const char* auth_token = "iot_secret_token_12345";


// -------- WIFI CONNECTION --------
void connectWiFi()
{
  Serial.println("[*] Connecting to WiFi...");
  WiFi.begin(ssid, password);

  int attempts = 0;
  while (WiFi.status() != WL_CONNECTED && attempts < 20)
  {
    delay(500);
    Serial.print(".");
    attempts++;
  }

  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("\n[OK] WiFi Connected!");
    Serial.print("    IP: ");
    Serial.println(WiFi.localIP());
  } else {
    Serial.println("\n[ERROR] Failed to connect to WiFi!");
  }
}


// -------- OLED DISPLAY --------
void updateDisplay(String source, float demand_kwh, float pool_kwh, float grid_kwh)
{
  u8g2.clearBuffer();

  u8g2.setFont(u8g2_font_6x10_tr);
  u8g2.drawStr(0, 10, "ROSHNI BUYER");
  u8g2.drawLine(0, 12, 128, 12);

  // Current demand from potentiometer
  u8g2.setCursor(0, 25);
  u8g2.print("Demand:");
  u8g2.print(demand_kwh, 2);
  u8g2.print(" kWh");

  // Allocation source
  u8g2.setCursor(0, 38);
  u8g2.print("Source:");
  u8g2.print(source);

  // Pool and Grid breakdown
  u8g2.setCursor(0, 52);
  u8g2.print("[Pool]");
  u8g2.print(pool_kwh, 1);
  u8g2.print(" ");

  u8g2.setCursor(70, 52);
  u8g2.print("[Grid]");
  u8g2.print(grid_kwh, 1);

  u8g2.sendBuffer();
}


// -------- SETUP --------
void setup()
{
  Serial.begin(115200);
  delay(1000);

  Serial.println("\n========================================");
  Serial.println("ROSHNI BUYER IoT (Demand Generation)");
  Serial.println("========================================");

  // Initialize I2C and OLED
  Wire.begin(21, 22);  // SDA=21, SCL=22 for NodeMCU-32S
  u8g2.begin();

  // Initialize ADC
  analogReadResolution(12);
  analogSetAttenuation(ADC_11db);

  pinMode(POT_PIN, INPUT);

  Serial.print("[*] Device ID: ");
  Serial.println(device_id);
  Serial.print("[*] House ID: ");
  Serial.println(house_id);
  Serial.print("[*] Backend URL: ");
  Serial.println(backendUrl);

  connectWiFi();
  
  // Initial display
  updateDisplay("ADJUST", 0, 0, 0);
}


// -------- LOOP --------
void loop()
{
  // ✅ READ POTENTIOMETER WITH MULTIPLE SAMPLES FOR STABILITY
  int total = 0;
  for (int i = 0; i < 10; i++)
  {
    total += analogRead(POT_PIN);
    delay(5);
  }
  int potValue = total / 10;

  // Convert to demand in kWh (0-5.0 kWh map from 0-4095)
  float demand_kwh = (potValue / 4095.0) * 5.0;

  Serial.print("[*] Pot: ");
  Serial.print(potValue);
  Serial.print(" -> Demand: ");
  Serial.print(demand_kwh, 2);
  Serial.println(" kWh");

  // Update OLED with current reading
  updateDisplay("SENDING", demand_kwh, 0, 0);

  delay(200);

  // -------- SEND TO BACKEND EVERY 5 SECONDS --------
  if (WiFi.status() != WL_CONNECTED) {
    connectWiFi();
  }

  if (millis() - lastUpdate > updateInterval)
  {
    lastUpdate = millis();

    Serial.println("\n==== SENDING DEMAND TO BACKEND ====");

    WiFiClient client;
    HTTPClient http;

    http.begin(client, backendUrl);
    http.addHeader("Content-Type", "application/json");

    // Create JSON payload
    StaticJsonDocument<200> doc;
    doc["auth_token"] = auth_token;
    doc["house_id"] = house_id;
    doc["device_id"] = device_id;
    doc["demand_kwh"] = demand_kwh;

    String payload;
    serializeJson(doc, payload);

    Serial.print("[*] Payload: ");
    Serial.println(payload);

    int httpCode = http.POST(payload);

    if (httpCode > 0)
    {
      String response = http.getString();
      Serial.print("[OK] Response Code: ");
      Serial.println(httpCode);
      Serial.print("[*] Body: ");
      Serial.println(response);

      // Parse response
      StaticJsonDocument<300> resDoc;
      DeserializationError error = deserializeJson(resDoc, response);

      if (!error && resDoc["status"] == "matched")
      {
        float pool = resDoc["allocated_kwh"] | 0;
        float grid = resDoc["grid_required_kwh"] | 0;

        String source;
        if (grid == 0 && pool > 0)
          source = "POOL";
        else if (pool > 0 && grid > 0)
          source = "HYBRID";
        else
          source = "GRID";

        Serial.print("[OK] Allocation: Pool=");
        Serial.print(pool, 2);
        Serial.print(" Grid=");
        Serial.print(grid, 2);
        Serial.print(" Source=");
        Serial.println(source);

        updateDisplay(source, demand_kwh, pool, grid);
      }
      else
      {
        Serial.println("[ERROR] Failed to parse response!");
        updateDisplay("ERROR", demand_kwh, 0, 0);
      }
    }
    else
    {
      Serial.print("[ERROR] HTTP Error: ");
      Serial.println(httpCode);
      updateDisplay("ERROR", demand_kwh, 0, 0);
    }

    http.end();
  }
}
