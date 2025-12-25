/*
 * Node 1 ESP8266 Transmitter (IMPROVED VERSION)
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
 * Pin Connections (DEFAULT):
 * LoRa NSS  -> D4 (GPIO2)   [Changed from D8 to avoid GPIO15 boot issues]
 * LoRa RST  -> D0 (GPIO16)
 * LoRa DIO0 -> D2 (GPIO4)
 * LoRa SCK  -> D5 (GPIO14)  [Hardware SPI]
 * LoRa MISO -> D6 (GPIO12)  [Hardware SPI]
 * LoRa MOSI -> D7 (GPIO13)  [Hardware SPI]
 * 
 * IMPORTANT: Use 3.3V for LoRa module, NOT 5V!
 */

#include <Arduino.h>
#include <SPI.h>
#include <LoRa.h>

// -------- LoRa Configuration --------
// Changed NSS from D8 (GPIO15) to D4 (GPIO2) to avoid boot issues
// GPIO15 must be LOW during boot, which can interfere with LoRa
#define LORA_SS   D4    // NSS pin (was D8)
#define LORA_RST  D0    // Reset pin
#define LORA_DIO0 D2    // DIO0 pin
#define LORA_FREQ 433E6 // 433 MHz (Change to 915E6 for 915 MHz)

// -------- LoRa Parameters --------
#define SPREADING_FACTOR 7    // SF7-SF9 (lower = faster, less range)
#define SIGNAL_BANDWIDTH 125E3 // 125 kHz
#define TX_POWER 17           // 2-20 dBm

// -------- Serial Configuration --------
#define SERIAL_BAUD 115200
#define MAX_PACKET_SIZE 255

// -------- Status LED (built-in) --------
#define LED_PIN LED_BUILTIN

// -------- Variables --------
String incomingData = "";
unsigned long lastPacketTime = 0;
unsigned long packetCount = 0;

void setup() {
  // Initialize Serial
  Serial.begin(SERIAL_BAUD);
  delay(2000); // Give time for serial to stabilize
  
  // Initialize LED
  pinMode(LED_PIN, OUTPUT);
  digitalWrite(LED_PIN, HIGH); // LED OFF (active low on most ESP8266)
  
  Serial.println();
  Serial.println("=================================");
  Serial.println("Node 1 - LoRa Transmitter");
  Serial.println("=================================");
  Serial.println();
  Serial.println("Pin Configuration:");
  Serial.print("  NSS/CS: D4 (GPIO");
  Serial.print(LORA_SS);
  Serial.println(")");
  Serial.print("  RST:    D0 (GPIO");
  Serial.print(LORA_RST);
  Serial.println(")");
  Serial.print("  DIO0:   D2 (GPIO");
  Serial.print(LORA_DIO0);
  Serial.println(")");
  Serial.println("  MOSI:   D7 (GPIO13)");
  Serial.println("  MISO:   D6 (GPIO12)");
  Serial.println("  SCK:    D5 (GPIO14)");
  Serial.println();
  
  // Initialize LoRa with improved error handling
  SPI.begin();
  Serial.println("[OK] SPI initialized");
  
  // Manual reset sequence for better reliability
  pinMode(LORA_RST, OUTPUT);
  digitalWrite(LORA_RST, LOW);
  delay(10);
  digitalWrite(LORA_RST, HIGH);
  delay(10);
  Serial.println("[OK] LoRa reset complete");
  
  LoRa.setPins(LORA_SS, LORA_RST, LORA_DIO0);
  
  Serial.print("Initializing LoRa at ");
  Serial.print(LORA_FREQ / 1E6);
  Serial.println(" MHz...");
  
  // Try initialization with retry logic
  int retries = 0;
  const int MAX_RETRIES = 5;
  bool loraInitialized = false;
  
  while (retries < MAX_RETRIES && !loraInitialized) {
    if (LoRa.begin(LORA_FREQ)) {
      loraInitialized = true;
      break;
    }
    retries++;
    Serial.print("Retry ");
    Serial.print(retries);
    Serial.print("/");
    Serial.println(MAX_RETRIES);
    delay(500);
    yield(); // Feed watchdog timer
  }
  
  if (!loraInitialized) {
    Serial.println();
    Serial.println("[ERROR] LoRa initialization failed after all retries!");
    Serial.println();
    Serial.println("Troubleshooting steps:");
    Serial.println("1. Check wiring (especially NSS -> D4, not D8)");
    Serial.println("2. Verify 3.3V power (NOT 5V!)");
    Serial.println("3. Ensure LoRa module is not damaged");
    Serial.println("4. Check that antenna is connected");
    Serial.println("5. Verify correct frequency module (433 MHz)");
    Serial.println("6. Try running lora_diagnostic.ino for detailed testing");
    Serial.println();
    Serial.println("See TROUBLESHOOTING.md for more help");
    Serial.println();
    while (1) {
      // Blink LED rapidly to indicate error
      digitalWrite(LED_PIN, LOW);
      delay(100);
      digitalWrite(LED_PIN, HIGH);
      delay(100);
      yield(); // Feed watchdog timer
    }
  }
  
  Serial.println("[OK] LoRa initialized successfully!");
  Serial.println();
  
  // Configure LoRa parameters
  LoRa.setSpreadingFactor(SPREADING_FACTOR);
  LoRa.setSignalBandwidth(SIGNAL_BANDWIDTH);
  LoRa.setTxPower(TX_POWER);
  LoRa.enableCrc(); // Enable CRC for error detection
  
  Serial.println("LoRa Configuration:");
  Serial.print("  Spreading Factor: SF");
  Serial.println(SPREADING_FACTOR);
  Serial.print("  Bandwidth: ");
  Serial.print(SIGNAL_BANDWIDTH / 1E3);
  Serial.println(" kHz");
  Serial.print("  TX Power: ");
  Serial.print(TX_POWER);
  Serial.println(" dBm");
  Serial.println("  CRC: Enabled");
  Serial.println();
  Serial.println("Waiting for alert data from laptop...");
  Serial.println("Expected format: EVT:TYPE;CONF:0.XX;LAT:XX.XX;LON:XX.XX;TS:XXXXXXX");
  Serial.println("=================================");
  Serial.println();
  
  // Blink LED to indicate ready
  for (int i = 0; i < 3; i++) {
    digitalWrite(LED_PIN, LOW);
    delay(200);
    digitalWrite(LED_PIN, HIGH);
    delay(200);
  }
  
  Serial.println("[READY] System initialized. Listening for serial data...");
}

void loop() {
  // Feed watchdog timer
  yield();
  
  // Read data from Serial (laptop)
  while (Serial.available() > 0) {
    char c = Serial.read();
    
    if (c == '\n' || c == '\r') {
      // End of line - process the data
      if (incomingData.length() > 0) {
        processAndTransmit(incomingData);
        incomingData = ""; // Clear buffer
      }
    } else {
      // Add character to buffer
      incomingData += c;
      
      // Prevent buffer overflow
      if (incomingData.length() > MAX_PACKET_SIZE) {
        Serial.println("[WARN] Packet too large, truncating...");
        incomingData = incomingData.substring(0, MAX_PACKET_SIZE);
      }
    }
  }
  
  // Small delay to prevent tight loop
  delay(10);
}

void processAndTransmit(String payload) {
  Serial.println();
  Serial.println("--- New Alert Received ---");
  Serial.print("Payload: ");
  Serial.println(payload);
  Serial.print("Length: ");
  Serial.print(payload.length());
  Serial.println(" bytes");
  
  // Validate payload (basic check)
  if (!validatePayload(payload)) {
    Serial.println("[ERROR] Invalid payload format! Skipping transmission.");
    return;
  }
  
  // Transmit via LoRa
  digitalWrite(LED_PIN, LOW); // LED ON during transmission
  
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
  
  // Update stats
  packetCount++;
  lastPacketTime = millis();
  
  Serial.print("Total packets sent: ");
  Serial.println(packetCount);
  Serial.println("--------------------------");
  Serial.println();
}

bool validatePayload(String payload) {
  // Basic validation - check if payload contains expected fields
  if (payload.length() < 10) {
    return false;
  }
  
  // Check for key identifiers
  if (payload.indexOf("EVT:") == -1) {
    Serial.println("[WARN] Missing EVT field");
    return false;
  }
  
  if (payload.indexOf("CONF:") == -1) {
    Serial.println("[WARN] Missing CONF field");
    return false;
  }
  
  // Payload seems valid
  return true;
}
