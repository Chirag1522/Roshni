# IoT Libraries Required

Install via Arduino IDE:

1. **ESP8266 Board Support**
   - Go to File → Preferences → Add board manager URL:
   - `http://arduino.esp8266.com/stable/package_esp8266com_index.json`
   - Boards → Search "ESP8266" → Install latest

2. **Libraries** (Sketch → Include Library → Manage Libraries)
   - `ArduinoJson` by Benoit Blanchon (v6.21.0+)
   - Built-in: `ESP8266WiFi`, `ESP8266HTTPClient`

3. **Board Settings**
   - Board: NodeMCU 1.0 (ESP-12E Module)
   - Flash Size: 4MB
   - Upload Speed: 115200 baud
   - Flash Mode: DIO

4. **Dependencies Installation**


## Pin Configuration

- **LED_RED**: D1 (GPIO 5)
- **LED_GREEN**: D2 (GPIO 4)
- **LED_BLUE**: D3 (GPIO 0)

## Compilation & Upload

1. Select correct COM port (Tools → Port)
2. Click Upload button
3. Monitor Serial output at 115200 baud