#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>
#include <Wire.h>
#include <U8g2lib.h>
#include <WiFiClientSecure.h>  // HTTPS support

// -------- OLED --------
U8G2_SH1106_128X64_NONAME_F_HW_I2C u8g2(U8G2_R0, U8X8_PIN_NONE);

// -------- WIFI --------
const char* ssid = "test1";
const char* password = "12345678";

// -------- BACKEND (CLOUD - Render) --------
// This connects to the ROSHNI backend running on Render.com
const char* backendUrl = "https://roshni-backend-o7al.onrender.com/api/iot/update";

// -------- AUTH --------
const char* auth_token = "iot_secret_token_12345";
const char* device_id = "NodeMCU_001";
const char* house_id = "HOUSE_FDR12_001";

// -------- PINS --------
const int POT_PIN = 32;

// RGB LED
const int RED_PIN = 25;
const int GREEN_PIN = 26;
const int BLUE_PIN = 27;

// -------- TIMER --------
unsigned long lastUpdate = 0;
int updateInterval = 5000;

// -------- SMOOTHING --------
float smoothGen = 0;


// -------- WIFI --------
void connectWiFi()
{
  Serial.println("\nConnecting to WiFi...");

  WiFi.begin(ssid, password);

  while (WiFi.status() != WL_CONNECTED)
  {
    delay(500);
    Serial.print(".");
  }

  Serial.println("\nWiFi CONNECTED");
  Serial.println(WiFi.localIP());
}


// -------- LED --------
void setLED(float generation)
{
  digitalWrite(RED_PIN, LOW);
  digitalWrite(GREEN_PIN, LOW);
  digitalWrite(BLUE_PIN, LOW);

  if (generation < 1)
  {
    digitalWrite(RED_PIN, HIGH);
    Serial.println("LED: RED (LOW)");
  }
  else if (generation <= 3)
  {
    digitalWrite(GREEN_PIN, HIGH);
    Serial.println("LED: GREEN (NORMAL)");
  }
  else
  {
    digitalWrite(BLUE_PIN, HIGH);
    Serial.println("LED: BLUE (HIGH)");
  }
}


// -------- OLED --------
void updateDisplay(float generation, String tradeStatus)
{
  u8g2.clearBuffer();

  u8g2.setFont(u8g2_font_6x10_tr);

  u8g2.drawStr(0, 10, "ROSHNI SOLAR");
  u8g2.drawLine(0, 12, 128, 12);

  u8g2.setCursor(0, 28);
  u8g2.print("Gen: ");
  u8g2.print(generation, 2);
  u8g2.print(" kWh");

  u8g2.setCursor(0, 42);
  u8g2.print("Selling: ");
  if (generation > 0.5)
    u8g2.print("YES");
  else
    u8g2.print("NO");

  u8g2.setCursor(0, 56);
  u8g2.print("Trade: ");
  u8g2.print(tradeStatus);

  u8g2.sendBuffer();
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

  // OLED
  Wire.begin(21, 22);
  u8g2.begin();

  // ADC
  analogReadResolution(12);
  analogSetPinAttenuation(POT_PIN, ADC_11db);

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

    Serial.println("\n=========== NEW UPDATE ===========");

    // -------- POT READ --------
    int potValue = analogRead(POT_PIN);

    Serial.print("Raw Value: ");
    Serial.println(potValue);

    // Smooth generation
    float rawGen = (float)potValue / 4095.0 * 5.0;
    smoothGen = (0.7 * smoothGen) + (0.3 * rawGen);
    float generation_kwh = smoothGen;

    Serial.print("Generated Energy: ");
    Serial.println(generation_kwh, 3);

    // LED
    setLED(generation_kwh);

    // WiFi signal
    int signal_strength = WiFi.RSSI();

    Serial.print("WiFi RSSI: ");
    Serial.println(signal_strength);

    Serial.println("===== BACKEND CONNECTION =====");

    // HTTPS client with certificate validation disabled (for Render)
    WiFiClientSecure client;
    client.setInsecure();  // Skip SSL verification for Render testing

    HTTPClient http;
    http.setTimeout(10000);

    if (!http.begin(client, backendUrl))
    {
      Serial.println("ERROR: HTTP begin failed");
      updateDisplay(generation_kwh, "NO_NET");
      return;
    }

    http.addHeader("Connection", "close");
    http.addHeader("Content-Type", "application/json");

    // JSON
    StaticJsonDocument<200> doc;

    doc["auth_token"] = auth_token;
    doc["device_id"] = device_id;
    doc["generation_kwh"] = generation_kwh;
    doc["house_id"] = house_id;
    doc["signal_strength"] = signal_strength;

    String payload;
    serializeJson(doc, payload);

    Serial.print("Payload: ");
    Serial.println(payload);

    int httpCode = http.POST(payload);

    Serial.print("HTTP Code: ");
    Serial.println(httpCode);

    String tradeStatus = "NONE";

    if (httpCode > 0)
    {
      Serial.println("OK: Backend SUCCESS");

      String response = http.getString();
      Serial.println(response);

      StaticJsonDocument<300> resDoc;
      DeserializationError error = deserializeJson(resDoc, response);

      if (!error)
        tradeStatus = resDoc["status"] | "OK";
      else
        tradeStatus = "PARSE_ERR";
    }
    else
    {
      Serial.println("ERROR: Backend FAILED");
      tradeStatus = "FAILED";
    }

    // OLED update
    updateDisplay(generation_kwh, tradeStatus);

    http.end();
  }
}
