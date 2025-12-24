#include <SPI.h>
#include <LoRa.h>

// Pin mapping for ESP8266
#define LORA_SS    15   // D8
#define LORA_RST   16   // D0
#define LORA_DIO0  5    // D1

void setup() {
  Serial.begin(115200);
  while(!Serial); // Wait for serial port
  delay(1000);
  
  Serial.println();
  Serial.println("LoRa Transmitter Initializing...");

  // Initialize SPI
  SPI.begin();
  
  // Set LoRa pins
  LoRa.setPins(LORA_SS, LORA_RST, LORA_DIO0);

  // Try to initialize LoRa
  Serial.println("Starting LoRa...");
  if (!LoRa.begin(433E6)) {
    Serial.println("LoRa init FAILED!");
    Serial.println("Check wiring:");
    Serial.println("  NSS  -> D8 (GPIO15)");
    Serial.println("  RST  -> D0 (GPIO16)");
    Serial.println("  DIO0 -> D1 (GPIO5)");
    while (true) {
      delay(1000);
    }
  }

  Serial.println("LoRa OK!");
  
  // Configure LoRa
  LoRa.setTxPower(20);
  LoRa.setSpreadingFactor(7);
  LoRa.setSignalBandwidth(125E3);
  LoRa.setSyncWord(0xF3);
  
  Serial.println("Ready to send messages!");
  Serial.println("Type your message and press Enter:");
}

void loop() { 
  // Check if data available on serial
  if (Serial.available() > 0) {
    String message = Serial.readStringUntil('\n');
    message.trim(); // Remove whitespace
    
    if (message.length() > 0) {
      Serial.println("---");
      Serial.print("TX: ");
      Serial.println(message);
      
      // Send via LoRa
      LoRa.beginPacket();
      LoRa.print(message);
      LoRa.endPacket();
      
      Serial.println("Sent!");
      Serial.println("---");
    }
  }
}