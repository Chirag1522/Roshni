/*
  ROSHNI Solar Prosumer IoT Firmware
  NodeMCU ESP8266 - Real-time Solar Generation Monitor
  
  Features:
  - Auto solar fluctuation with sine wave + cloud noise
  - Night mode support
  - RGB LED status indicators
  - WiFi HTTP POST every 5 seconds
  - Trade status reception
*/

#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>

// -------- WIFI --------
const char* ssid = "test";
const char* password = "9876543210";

// -------- BACKEND URL --------
const char* backendUrl = "http://localhost:8000/api/iot/update";

// -------- AUTH --------
const char* auth_token = "iot_secret_token_12345";
const char* device_id = "NodeMCU_001";
const char* house_id = "HOUSE_FDR12_001";

// -------- PINS --------
const int POT_PIN = 34;

// RGB LED PINS
const int RED_PIN = 25;
const int GREEN_PIN = 26;
const int BLUE_PIN = 27;

// -------- TIMER --------
unsigned long lastUpdate = 0;
int updateInterval = 5000;


// -------- WIFI CONNECT FUNCTION --------
void connectWiFi()
{
  Serial.println();
  Serial.println("Connecting to WiFi...");

  WiFi.begin(ssid, password);

  while (WiFi.status() != WL_CONNECTED)
  {
    delay(500);
    Serial.print(".");
  }

  Serial.println();
  Serial.println("WiFi CONNECTED ✓");

  Serial.print("ESP32 IP Address: ");
  Serial.println(WiFi.localIP());
}


// -------- LED CONTROL FUNCTION --------
void setLED(float generation)
{
  digitalWrite(RED_PIN, LOW);
  digitalWrite(GREEN_PIN, LOW);
  digitalWrite(BLUE_PIN, LOW);

  if (generation < 1)
  {
    digitalWrite(RED_PIN, HIGH);
    Serial.println("LED STATUS: RED (LOW GENERATION)");
  }
  else if (generation >= 1 && generation <= 3)
  {
    digitalWrite(GREEN_PIN, HIGH);
    Serial.println("LED STATUS: GREEN (NORMAL GENERATION)");
  }
  else
  {
    digitalWrite(BLUE_PIN, HIGH);
    Serial.println("LED STATUS: BLUE (HIGH GENERATION)");
  }
}


// -------- SETUP --------
void setup()
{
  Serial.begin(115200);
  delay(1000);

  Serial.println("=================================");
  Serial.println("SOLAR IOT DEVICE STARTED");
  Serial.println("=================================");

  pinMode(RED_PIN, OUTPUT);
  pinMode(GREEN_PIN, OUTPUT);
  pinMode(BLUE_PIN, OUTPUT);

  connectWiFi();
}


// -------- LOOP --------
void loop()
{
  if (WiFi.status() != WL_CONNECTED)
  {
    Serial.println("WiFi LOST. Reconnecting...");
    connectWiFi();
  }

  if (millis() - lastUpdate > updateInterval)
  {
    lastUpdate = millis();

    Serial.println();
    Serial.println("=========== NEW UPDATE ===========");

    // -------- READ POTENTIOMETER --------
    int potValue = analogRead(POT_PIN);

    Serial.print("Raw Potentiometer Value: ");
    Serial.println(potValue);

    float generation_kwh = (potValue / 4095.0) * 5.0;

    Serial.print("Generated Energy (kWh): ");
    Serial.println(generation_kwh, 3);

    // -------- CONTROL LED --------
    setLED(generation_kwh);


    // -------- WIFI SIGNAL --------
    int signal_strength = WiFi.RSSI();

    Serial.print("WiFi Signal Strength (RSSI): ");
    Serial.println(signal_strength);

    Serial.println();
    Serial.println("===== BACKEND CONNECTION CHECK =====");

    if (WiFi.status() == WL_CONNECTED)
    {
      Serial.println("WiFi Status: CONNECTED");

      Serial.print("Target Backend: ");
      Serial.println(backendUrl);

      WiFiClient client;
      HTTPClient http;

      http.setTimeout(10000);

      Serial.println("Opening HTTP connection...");

      bool connected = http.begin(client, backendUrl);

      if (!connected)
      {
        Serial.println("❌ HTTP begin() failed");
        client.stop();
        return;
      }

      Serial.println("✅ HTTP connection opened");

      http.addHeader("Connection", "close");
      http.addHeader("Content-Type", "application/json");

      // -------- CREATE JSON --------
      StaticJsonDocument<200> doc;

      doc["auth_token"] = auth_token;
      doc["device_id"] = device_id;
      doc["generation_kwh"] = round(generation_kwh * 1000.0) / 1000.0;
      doc["house_id"] = house_id;
      doc["signal_strength"] = signal_strength;

      String payload;
      serializeJson(doc, payload);

      Serial.println("Preparing JSON payload...");
      Serial.print("Payload: ");
      Serial.println(payload);

      Serial.println("Sending POST request now...");

      int httpCode = http.POST(payload);

      Serial.println("POST request finished");

      Serial.print("HTTP Response Code: ");
      Serial.println(httpCode);

      if (httpCode > 0)
      {
        Serial.println("✅ Backend connection SUCCESS");

        String response = http.getString();

        Serial.println("Server Response:");
        Serial.println(response);
      }
      else
      {
        Serial.println("❌ Backend connection FAILED");
        Serial.println("Check:");
        Serial.println("• FastAPI running?");
        Serial.println("• Correct IP address?");
        Serial.println("• Firewall blocking port 8000?");
        Serial.println("• Same WiFi network?");
      }

      http.end();
      client.stop();
    }
    else
    {
      Serial.println("WiFi NOT connected. Cannot reach backend.");
    }
  }
}
