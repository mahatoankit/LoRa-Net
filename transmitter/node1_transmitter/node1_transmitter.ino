/*
 * Node 1 ESP8266 Transmitter - Production Version
 * 
 * Reads alert data from laptop via Serial (115200 baud)
 * Transmits alert packets via LoRa (433 MHz)
 * 
 * Expected Serial input format:
 * EVT:GUNSHOT;CONF:0.91;LAT:27.70;LON:85.33;TS:1735119862\n
 * 
 * Hardware:
 * - ESP8266 (NodeMCU, Wemos D1 Mini, etc.)
 * - LoRa RA-02 (433 MHz)
 * 
 * Pin Connections:
 * LoRa NSS  -> D4 (GPIO2)
 * LoRa RST  -> D0 (GPIO16)
 * LoRa DIO0 -> D2 (GPIO4)
 * LoRa SCK  -> D5 (GPIO14)
 * LoRa MISO -> D6 (GPIO12)
 * LoRa MOSI -> D7 (GPIO13)
 * 
 * IMPORTANT: Use 3.3V for LoRa module, NOT 5V!
 */

#include <Arduino.h>
#include <SPI.h>
#include <LoRa.h>

// -------- LoRa Configuration --------
#define LORA_SS   D4    // NSS pin
#define LORA_RST  D0    // Reset pin
#define LORA_DIO0 D2    // DIO0 pin
#define LORA_FREQ 433E6 // 433 MHz

// -------- LoRa Parameters --------
#define SPREADING_FACTOR 7
#define SIGNAL_BANDWIDTH 125E3
#define TX_POWER 17

// -------- Serial Configuration --------
#define SERIAL_BAUD 115200
#define MAX_PACKET_SIZE 255

// -------- Status LED --------
#define LED_PIN LED_BUILTIN

// -------- Variables --------
String incomingData = "";
unsigned long packetCount = 0;

void setup() {
  // Initialize Serial
  Serial.begin(SERIAL_BAUD);
  delay(2000);
  
  // Initialize LED
  pinMode(LED_PIN, OUTPUT);
  digitalWrite(LED_PIN, HIGH); // LED OFF (active low)
  
  Serial.println();
  Serial.println("=================================");
  Serial.println("Node 1 - LoRa Transmitter");
  Serial.println("=================================");
  Serial.println();
  
  // Initialize LoRa
  SPI.begin();
  
  pinMode(LORA_RST, OUTPUT);
  digitalWrite(LORA_RST, LOW);
  delay(10);
  digitalWrite(LORA_RST, HIGH);
  delay(10);
  
  LoRa.setPins(LORA_SS, LORA_RST, LORA_DIO0);
  
  Serial.print("Initializing LoRa at ");
  Serial.print(LORA_FREQ / 1E6);
  Serial.println(" MHz...");
  
  // Retry logic
  int retries = 0;
  bool loraInitialized = false;
  
  while (retries < 5 && !loraInitialized) {
    if (LoRa.begin(LORA_FREQ)) {
      loraInitialized = true;
      break;
    }
    retries++;
    Serial.print("Retry ");
    Serial.print(retries);
    Serial.println("/5");
    delay(500);
    yield();
  }
  
  if (!loraInitialized) {
    Serial.println("[ERROR] LoRa initialization failed!");
    while (1) {
      digitalWrite(LED_PIN, LOW);
      delay(100);
      digitalWrite(LED_PIN, HIGH);
      delay(100);
      yield();
    }
  }
  
  // Configure LoRa
  LoRa.setSpreadingFactor(SPREADING_FACTOR);
  LoRa.setSignalBandwidth(SIGNAL_BANDWIDTH);
  LoRa.setTxPower(TX_POWER);
  LoRa.enableCrc();
  
  Serial.println("[OK] LoRa initialized successfully!");
  Serial.println();
  Serial.println("Waiting for alert data from laptop...");
  Serial.println("Expected format: EVT:TYPE;CONF:0.XX;LAT:XX.XX;LON:XX.XX;TS:XXXXXXX");
  Serial.println("=================================");
  Serial.println();
  
  // Ready blink
  for (int i = 0; i < 3; i++) {
    digitalWrite(LED_PIN, LOW);
    delay(200);
    digitalWrite(LED_PIN, HIGH);
    delay(200);
  }
  
  Serial.println("[READY] Listening for serial data...");
}

void loop() {
  yield();
  
  // Read data from Serial (laptop)
  while (Serial.available() > 0) {
    char c = Serial.read();
    
    if (c == '\n' || c == '\r') {
      // End of line - process the data
      if (incomingData.length() > 0) {
        processAndTransmit(incomingData);
        incomingData = "";
      }
    } else {
      // Add character to buffer
      incomingData += c;
      
      // Prevent buffer overflow
      if (incomingData.length() > MAX_PACKET_SIZE) {
        Serial.println("[WARN] Packet too large, truncating");
        incomingData = incomingData.substring(0, MAX_PACKET_SIZE);
      }
    }
  }
  
  delay(10);
}

void processAndTransmit(String payload) {
  Serial.println();
  Serial.println("--- Alert Received from Python ---");
  Serial.print("Payload: ");
  Serial.println(payload);
  Serial.print("Length: ");
  Serial.print(payload.length());
  Serial.println(" bytes");
  
  // Validate payload
  if (payload.indexOf("EVT:") == -1) {
    Serial.println("[ERROR] Invalid payload format!");
    return;
  }
  
  // Transmit via LoRa
  digitalWrite(LED_PIN, LOW); // LED ON
  
  Serial.print("Transmitting via LoRa... ");
  unsigned long txStart = millis();
  
  LoRa.beginPacket();
  LoRa.print(payload);
  LoRa.endPacket();
  
  unsigned long txDuration = millis() - txStart;
  
  digitalWrite(LED_PIN, HIGH); // LED OFF
  
  Serial.print("[OK] Sent in ");
  Serial.print(txDuration);
  Serial.println(" ms");
  
  packetCount++;
  Serial.print("Total packets sent: ");
  Serial.println(packetCount);
  Serial.println("----------------------------------");
  Serial.println();
}
