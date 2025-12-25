/*
 * Central Hub ESP8266 Receiver
 * 
 * Receives alert packets via LoRa (433 MHz)
 * Forwards packets to dashboard laptop via Serial (115200 baud)
 * 
 * Outputs format to Serial:
 * EVT:GUNSHOT;CONF:0.91;LAT:27.70;LON:85.33;TS:1735119862;RSSI:-45
 * 
 * Hardware:
 * - ESP8266 (NodeMCU, Wemos D1 Mini, etc.)
 * - LoRa RA-02 (433 MHz)
 * 
 * Pin Connections:
 * LoRa NSS  -> D8 (GPIO15)
 * LoRa RST  -> D0 (GPIO16)
 * LoRa DIO0 -> D2 (GPIO4)
 * LoRa SCK  -> D5 (GPIO14)
 * LoRa MISO -> D6 (GPIO12)
 * LoRa MOSI -> D7 (GPIO13)
 */

#include <Arduino.h>
#include <SPI.h>
#include <LoRa.h>

// -------- LoRa Configuration --------
#define LORA_SS   D8    // NSS pin
#define LORA_RST  D0    // Reset pin
#define LORA_DIO0 D2    // DIO0 pin
#define LORA_FREQ 433E6 // 433 MHz (Must match transmitter)

// -------- LoRa Parameters --------
#define SPREADING_FACTOR 7    // Must match transmitter
#define SIGNAL_BANDWIDTH 125E3 // Must match transmitter

// -------- Serial Configuration --------
#define SERIAL_BAUD 115200

// -------- Status LED (built-in) --------
#define LED_PIN LED_BUILTIN

// -------- Variables --------
unsigned long packetsReceived = 0;
unsigned long lastPacketTime = 0;
unsigned long startTime = 0;

void setup() {
  // Initialize Serial
  Serial.begin(SERIAL_BAUD);
  while (!Serial) {
    delay(10);
  }
  
  // Initialize LED
  pinMode(LED_PIN, OUTPUT);
  digitalWrite(LED_PIN, HIGH); // LED OFF (active low)
  
  Serial.println();
  Serial.println("=================================");
  Serial.println("Central Hub - LoRa Receiver");
  Serial.println("=================================");
  
  // Initialize LoRa
  SPI.begin();
  LoRa.setPins(LORA_SS, LORA_RST, LORA_DIO0);
  
  Serial.print("Initializing LoRa at ");
  Serial.print(LORA_FREQ / 1E6);
  Serial.println(" MHz...");
  
  if (!LoRa.begin(LORA_FREQ)) {
    Serial.println("[ERROR] LoRa initialization failed!");
    Serial.println("Check wiring and module.");
    while (1) {
      // Blink LED rapidly to indicate error
      digitalWrite(LED_PIN, LOW);
      delay(100);
      digitalWrite(LED_PIN, HIGH);
      delay(100);
    }
  }
  
  // Configure LoRa parameters
  LoRa.setSpreadingFactor(SPREADING_FACTOR);
  LoRa.setSignalBandwidth(SIGNAL_BANDWIDTH);
  LoRa.enableCrc(); // Enable CRC for error detection
  
  Serial.println("[OK] LoRa initialized successfully!");
  Serial.print("Spreading Factor: SF");
  Serial.println(SPREADING_FACTOR);
  Serial.print("Bandwidth: ");
  Serial.print(SIGNAL_BANDWIDTH / 1E3);
  Serial.println(" kHz");
  Serial.println();
  Serial.println("Listening for incoming packets...");
  Serial.println("=================================");
  
  // Blink LED to indicate ready
  for (int i = 0; i < 3; i++) {
    digitalWrite(LED_PIN, LOW);
    delay(200);
    digitalWrite(LED_PIN, HIGH);
    delay(200);
  }
  
  startTime = millis();
}

void loop() {
  // Check for incoming LoRa packets
  int packetSize = LoRa.parsePacket();
  
  if (packetSize) {
    // Packet received!
    digitalWrite(LED_PIN, LOW); // LED ON
    
    // Read packet data
    String receivedData = "";
    while (LoRa.available()) {
      receivedData += (char)LoRa.read();
    }
    
    // Get RSSI and SNR
    int rssi = LoRa.packetRssi();
    float snr = LoRa.packetSnr();
    
    // Process and forward packet
    processPacket(receivedData, rssi, snr);
    
    digitalWrite(LED_PIN, HIGH); // LED OFF
    
    // Update stats
    packetsReceived++;
    lastPacketTime = millis();
  }
  
  // Optional: Print stats every 60 seconds
  static unsigned long lastStatsTime = 0;
  if (millis() - lastStatsTime > 60000) {
    printStats();
    lastStatsTime = millis();
  }
}

void processPacket(String payload, int rssi, float snr) {
  Serial.println();
  Serial.println("--- Packet Received ---");
  Serial.print("Data: ");
  Serial.println(payload);
  Serial.print("Size: ");
  Serial.print(payload.length());
  Serial.println(" bytes");
  Serial.print("RSSI: ");
  Serial.print(rssi);
  Serial.println(" dBm");
  Serial.print("SNR: ");
  Serial.print(snr);
  Serial.println(" dB");
  
  // Add RSSI and SNR metadata to payload
  String enrichedPayload = payload + ";RSSI:" + String(rssi) + ";SNR:" + String(snr, 1);
  
  // Forward to dashboard via Serial
  // Using a special prefix so dashboard can identify LoRa data vs debug logs
  Serial.print("DATA:");
  Serial.println(enrichedPayload);
  
  Serial.println("-----------------------");
}

void printStats() {
  unsigned long uptime = (millis() - startTime) / 1000;
  
  Serial.println();
  Serial.println("===== Statistics =====");
  Serial.print("Uptime: ");
  Serial.print(uptime);
  Serial.println(" seconds");
  Serial.print("Packets received: ");
  Serial.println(packetsReceived);
  
  if (packetsReceived > 0) {
    Serial.print("Last packet: ");
    Serial.print((millis() - lastPacketTime) / 1000);
    Serial.println(" seconds ago");
  }
  
  Serial.println("======================");
  Serial.println();
}
