#include <SPI.h>
#include <LoRa.h>

// Pin mapping for ESP8266
#define LORA_SS    15   // D8
#define LORA_RST   16   // D0
#define LORA_DIO0  5    // D1

void setup() {
  Serial.begin(115200);
  delay(1000);
  Serial.println("LoRa Receiver Initializing...");

  SPI.begin();  
  LoRa.setPins(LORA_SS, LORA_RST, LORA_DIO0);

  if (!LoRa.begin(433E6)) {  // Same frequency as transmitter
    Serial.println("LoRa init failed. Check wiring.");
    while (true);
  }

  Serial.println("LoRa Receiver Ready.");
  Serial.println("Waiting for messages...");
}

void loop() {
  int packetSize = LoRa.parsePacket();

  if (packetSize) {
    Serial.println("----- PACKET RECEIVED -----");

    // Read packet
    String received = "";
    while (LoRa.available()) {
      received += (char)LoRa.read();
    }

    // Print received message
    Serial.print("Message: ");
    Serial.println(received);

    // Print signal strength
    Serial.print("RSSI: ");
    Serial.println(LoRa.packetRssi());

    Serial.println("---------------------------");
  }
}