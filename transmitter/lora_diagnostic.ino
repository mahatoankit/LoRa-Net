/*
 * LoRa Module Diagnostic Tool
 * 
 * This sketch performs comprehensive diagnostics on your LoRa module
 * to help identify initialization issues.
 * 
 * Hardware:
 * - ESP8266 (NodeMCU, Wemos D1 Mini, etc.)
 * - LoRa RA-02 or compatible module
 * 
 * Upload this sketch and open Serial Monitor at 115200 baud
 */

#include <Arduino.h>
#include <SPI.h>
#include <LoRa.h>

// -------- Pin Configurations to Test --------
// Configuration 1 (Default - your current setup)
#define LORA_SS_1   D8    // GPIO15
#define LORA_RST_1  D0    // GPIO16
#define LORA_DIO0_1 D2    // GPIO4

// Configuration 2 (Alternative - avoids GPIO15 boot issues)
#define LORA_SS_2   D4    // GPIO2
#define LORA_RST_2  D3    // GPIO0
#define LORA_DIO0_2 D2    // GPIO4

// Configuration 3 (Another alternative)
#define LORA_SS_3   D1    // GPIO5
#define LORA_RST_3  D0    // GPIO16
#define LORA_DIO0_3 D2    // GPIO4

// -------- Frequencies to Test --------
const long frequencies[] = {433E6, 868E6, 915E6};
const char* freqNames[] = {"433 MHz", "868 MHz", "915 MHz"};

void setup() {
  Serial.begin(115200);
  delay(1000);
  
  Serial.println();
  Serial.println("========================================");
  Serial.println("   LoRa Module Diagnostic Tool");
  Serial.println("========================================");
  Serial.println();
  
  // Print ESP8266 info
  printESP8266Info();
  
  // Test SPI bus
  testSPIBus();
  
  // Test different pin configurations
  Serial.println("========================================");
  Serial.println("Testing Different Pin Configurations");
  Serial.println("========================================");
  
  Serial.println("\n--- Configuration 1 (Current Setup) ---");
  Serial.println("NSS: D8 (GPIO15), RST: D0 (GPIO16), DIO0: D2 (GPIO4)");
  testLoRaConfiguration(LORA_SS_1, LORA_RST_1, LORA_DIO0_1);
  
  Serial.println("\n--- Configuration 2 (Alternative) ---");
  Serial.println("NSS: D4 (GPIO2), RST: D3 (GPIO0), DIO0: D2 (GPIO4)");
  testLoRaConfiguration(LORA_SS_2, LORA_RST_2, LORA_DIO0_2);
  
  Serial.println("\n--- Configuration 3 (Alternative) ---");
  Serial.println("NSS: D1 (GPIO5), RST: D0 (GPIO16), DIO0: D2 (GPIO4)");
  testLoRaConfiguration(LORA_SS_3, LORA_RST_3, LORA_DIO0_3);
  
  Serial.println("\n========================================");
  Serial.println("Diagnostic Complete");
  Serial.println("========================================");
  Serial.println("\nIf all tests failed, check:");
  Serial.println("1. Wiring connections");
  Serial.println("2. Power supply (3.3V, sufficient current)");
  Serial.println("3. LoRa module is not damaged");
  Serial.println("4. Antenna is connected");
  Serial.println("5. Correct frequency module for your region");
}

void loop() {
  // Nothing in loop
  delay(1000);
}

void printESP8266Info() {
  Serial.println("ESP8266 Information:");
  Serial.println("--------------------");
  Serial.print("Chip ID: ");
  Serial.println(ESP.getChipId(), HEX);
  Serial.print("CPU Frequency: ");
  Serial.print(ESP.getCpuFreqMHz());
  Serial.println(" MHz");
  Serial.print("Flash Size: ");
  Serial.print(ESP.getFlashChipSize() / 1024 / 1024);
  Serial.println(" MB");
  Serial.print("Free Heap: ");
  Serial.print(ESP.getFreeHeap());
  Serial.println(" bytes");
  Serial.println();
}

void testSPIBus() {
  Serial.println("SPI Bus Test:");
  Serial.println("-------------");
  
  SPI.begin();
  Serial.println("[OK] SPI.begin() successful");
  
  Serial.println("Hardware SPI Pins:");
  Serial.println("  MOSI: D7 (GPIO13)");
  Serial.println("  MISO: D6 (GPIO12)");
  Serial.println("  SCK:  D5 (GPIO14)");
  Serial.println();
}

void testLoRaConfiguration(int ss, int rst, int dio0) {
  // Set pins as output/input
  pinMode(ss, OUTPUT);
  pinMode(rst, OUTPUT);
  pinMode(dio0, INPUT);
  
  // Manual reset sequence
  Serial.println("Performing manual reset...");
  digitalWrite(rst, LOW);
  delay(10);
  digitalWrite(rst, HIGH);
  delay(10);
  
  // Configure LoRa pins
  LoRa.setPins(ss, rst, dio0);
  
  // Try each frequency
  bool success = false;
  for (int i = 0; i < 3; i++) {
    Serial.print("Trying frequency: ");
    Serial.print(freqNames[i]);
    Serial.print(" (");
    Serial.print(frequencies[i] / 1E6);
    Serial.println(" MHz)");
    
    if (LoRa.begin(frequencies[i])) {
      Serial.print("[SUCCESS] LoRa module detected at ");
      Serial.println(freqNames[i]);
      
      // Read version register to verify communication
      Serial.print("Module version: 0x");
      Serial.println(LoRa.readRegister(0x42), HEX);
      
      // Test basic settings
      LoRa.setSpreadingFactor(7);
      LoRa.setSignalBandwidth(125E3);
      Serial.println("[OK] Basic configuration successful");
      
      LoRa.end();
      success = true;
      break;
    } else {
      Serial.println("[FAIL] Could not initialize LoRa");
    }
    delay(100);
  }
  
  if (!success) {
    Serial.println("[ERROR] All frequencies failed");
    
    // Additional diagnostics
    Serial.println("\nDiagnostic checks:");
    
    // Check if NSS pin can be controlled
    digitalWrite(ss, LOW);
    delay(1);
    Serial.print("NSS LOW test: ");
    Serial.println(digitalRead(ss) == LOW ? "OK" : "FAIL");
    
    digitalWrite(ss, HIGH);
    delay(1);
    Serial.print("NSS HIGH test: ");
    Serial.println(digitalRead(ss) == HIGH ? "OK" : "FAIL");
    
    // Check reset pin
    digitalWrite(rst, LOW);
    delay(1);
    Serial.print("RST LOW test: ");
    Serial.println(digitalRead(rst) == LOW ? "OK" : "FAIL");
    
    digitalWrite(rst, HIGH);
    delay(1);
    Serial.print("RST HIGH test: ");
    Serial.println(digitalRead(rst) == HIGH ? "OK" : "FAIL");
  }
}
