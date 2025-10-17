def blink():
    print("""
void setup(){
pinMode(13,OUTPUT);

}
void loop(){
digitalWrite(13,HIGH);
delay(1000);
digitalWrite(13,low);
delay(1000);
}
          """)

def zigbee():
    print("""
Node A
          int Led = 13;          // define LED Interface
int buttonpin = 7;     // define Metal Touch Sensor Interface
int val;               // define numeric variable

void setup() {
  Serial.begin(9600);
  pinMode(Led, OUTPUT);        // define LED as output interface
  pinMode(buttonpin, INPUT);   // define metal touch sensor as input interface
}

void loop() {
  val = digitalRead(buttonpin); // read sensor value
  // Serial.println(val);        // uncomment for debugging

  if (val == 1) {  // When the metal touch sensor detects a signal, LED flashes
    digitalWrite(Led, HIGH);
    Serial.println(val);
    delay(1000);  // keep LED ON for 1 sec
  } else {
    digitalWrite(Led, LOW);
    Serial.println(val);
    delay(1000);  // check every 1 sec
  }
}

Node B
/* ZigbeeSerialBridge.ino
   Bidirectional bridge: USB Serial <-> CC2530 (SoftwareSerial)
   Use pins 10 (RX) and 11 (TX) for SoftwareSerial
*/

#include <SoftwareSerial.h>

const uint8_t ZB_RX_PIN = 10; // Arduino reads here (connected to CC2530 TX)
const uint8_t ZB_TX_PIN = 11; // Arduino writes here (connected to CC2530 RX)

SoftwareSerial zbSerial(ZB_RX_PIN, ZB_TX_PIN); // (rx, tx)

void setup() {
  Serial.begin(9600);     // USB -> laptop
  zbSerial.begin(9600);   // UART to CC2530; match module baud
  Serial.println("Zigbee bridge ready");
}

void loop() {
  // forward from laptop -> CC2530
  while (Serial.available()) {
    uint8_t b = Serial.read();
    zbSerial.write(b);
  }

  // forward from CC2530 -> laptop
  while (zbSerial.available()) {
    uint8_t b = zbSerial.read();
    Serial.write(b);
  }
}
          """)
    
def zigbee1():
    print("""
#include <SoftwareSerial.h>

SoftwareSerial zigbee(10, 11); // RX, TX

void setup() {
  Serial.begin(9600);
  zigbee.begin(9600);
  Serial.println("Zigbee Sender Ready");
}

void loop() {
  zigbee.println("Hello from Sender!");
  Serial.println("Sent: Hello from Sender!");
  delay(2000); // send every 2 seconds
}
          

#include <SoftwareSerial.h>

SoftwareSerial zigbee(10, 11); // RX, TX

void setup() {
  Serial.begin(9600);
  zigbee.begin(9600);
  Serial.println("Zigbee Receiver Ready");
}

void loop() {
  if (zigbee.available()) {
    String data = zigbee.readStringUntil('\n');
    Serial.print("Received: ");
    Serial.println(data);
  }
}
          """)

def gsm(): 
    print("""

#include <SoftwareSerial.h>

SoftwareSerial sim(10, 11); // RX, TX

String number = "+6289668072234"; // Replace with your phone number

void setup() {
  delay(7000); // Wait for the GSM module to initialize
  Serial.begin(9600);
  sim.begin(9600);

  Serial.println("GSM Module Ready...");
  sendMessage(); // Send SMS once when powered up
}

void loop() {
  // Nothing here — SMS sent in setup()
}

void sendMessage() {
  Serial.println("Sending SMS...");
  sim.println("AT+CMGF=1");    // Set SMS to text mode
  delay(1000);
  sim.print("AT+CMGS=\"");
  sim.print(number);
  sim.println("\"");
  delay(1000);
  sim.print("Hello Commander, this is a test message from Arduino GSM module."); // Your message
  delay(1000);
  sim.write(26); // ASCII code for Ctrl+Z (to send)
  delay(1000);
  Serial.println("SMS Sent Successfully!");
}
          """)

def bluetooth():
    print("""
👇👇 4th - Bluetooth


char inputByte;
void setup() {
 Serial.begin(9600);
 pinMode(13,OUTPUT);

}

void loop() {
while(Serial.available()>0){
  inputByte= Serial.read();
  Serial.println(inputByte);
  if (inputByte=='Z'){
  digitalWrite(13,HIGH);
  }
  else if (inputByte=='z'){
  digitalWrite(13,LOW);
  } 
  }
}
          """)

def wifi():
    print("""
          
sudo raspi-config
*Interfacing Options → Serial*.
   * Disable login shell over serial.
   * Enable the *serial hardware port*.
sudo reboot
sudo apt-get update
sudo apt-get install minicom python3-serial -y
minicom -b 115200 -o -D /dev/serial0
* Type AT and press Enter.
* You should receive OK from ESP8266.
* Press Ctrl+A, then X to exit minicom. 
nano esp_serial.py


          
python
import serial
import time

# Open serial port
ser = serial.Serial('/dev/serial0', 115200, timeout=1)
time.sleep(1)  # Wait for ESP8266 to initialize

# Send AT command
ser.write(b'AT\r\n')
time.sleep(1)  # Give ESP8266 time to respond

# Read response
response = ser.readlines()
for line in response:
    print(line.decode('utf-8').strip())

# Close serial port
ser.close()
          

chmod +x esp_serial.py
python3 esp_serial.py
          """)
    
def irsensor():
    print("""
sudo apt update
sudo apt install -y python3-rpi.gpio

          
import RPi.GPIO as GPIO
import time

# Pin configuration
IR_PIN = 18  # GPIO18 (Physical pin 12)
ACTIVE_LOW = True  # Most IR modules output LOW when object detected

# Setup
GPIO.setmode(GPIO.BCM)
GPIO.setup(IR_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)

print("IR Sensor running... Press Ctrl+C to stop.\n")

try:
    last_state = None
    while True:
        value = GPIO.input(IR_PIN)
        detected = (value == 0) if ACTIVE_LOW else (value == 1)

        if detected and last_state != True:
            print("✅ Object Detected")
        elif not detected and last_state != False:
            print("❌ No Object Detected")

        last_state = detected
        time.sleep(0.1)

except KeyboardInterrupt:
    print("\nProgram stopped by user.")

finally:
    GPIO.cleanup()


Save and exit:
Ctrl + O → Enter → Ctrl + X
python3 ir_sensor.py
""")

def ardras():
    print("""
sudo apt-get update
sudo apt-get install arduino

import serial
import time

# Use Arduino USB port
ser = serial.Serial('/dev/ttyUSB0', 9600)  # baud rate must match Arduino
time.sleep(2)  # wait for connection to establish

while True:
    if ser.in_waiting > 0:
        data = ser.readline().decode().rstrip()
        print("Received from Arduino:", data)
""")

def cloud():
    print("""
👇👇 9th - Cloud

File → Preferences
Additional Boards Manager URLs

http://arduino.esp8266.com/stable/package_esp8266com_index.json


Tools → Board → Boards Manager
Search ESP8266
Install it

Tools → Board → NodeMCU 1.0 (ESP-12E Module)

Port under Tools → Port


#include <ESP8266WiFi.h>
#include <WiFiClient.h>
#include <ThingSpeak.h>

#define WIFI_SSID "your_wifi_ssid"
#define WIFI_PASSWORD "your_wifi_password"
#define CHANNEL_ID your_channel_id   // Replace with your ThingSpeak Channel ID
#define API_KEY "your_thingspeak_api_key"

const int sensorPin = D2; // IR Sensor connected to D2

WiFiClient client;

void setup() {
  Serial.begin(115200);
  pinMode(sensorPin, INPUT);

  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  Serial.println("Connecting to WiFi...");
  while (WiFi.status() != WL_CONNECTED) {
    delay(1000);
    Serial.print(".");
  }
  Serial.println("\nConnected to WiFi!");
  ThingSpeak.begin(client);
}

void loop() {
  int sensorValue = digitalRead(sensorPin);
  
  if (sensorValue == HIGH) {
    Serial.println("Object Detected");
    ThingSpeak.writeField(CHANNEL_ID, 1, 1, API_KEY);
  } else {
    Serial.println("No Object Detected");
    ThingSpeak.writeField(CHANNEL_ID, 1, 0, API_KEY);
  }

  delay(2000); // Send every 2 seconds
}
          """)
    
    

