#include <SPI.h>
#include <LoRa.h>

// Pin mapping for ESP8266
#define LORA_SS    15   // D8
#define LORA_RST   16   // D0
#define LORA_DIO0  5    // D1

void setup() {
  Serial.begin(115200);
  delay(1000);
  Serial.println("LoRa Transmitter Initializing...");

  SPI.begin();  
  LoRa.setPins(LORA_SS, LORA_RST, LORA_DIO0);

  if (!LoRa.begin(433E6)) {  // RA-02 = 433 MHz
    Serial.println("LoRa init failed. Check wiring.");
    while (true);
  }

  Serial.println("LoRa Initialized Successfully.");
}

void loop() { 
  String payload = "Test Packet from ESP8266";

  Serial.print("Sending: ");
  Serial.println(payload);

  LoRa.beginPacket();
  LoRa.print(payload);
  LoRa.endPacket();

  delay(2000);
}
  