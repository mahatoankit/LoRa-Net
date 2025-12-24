#include <Arduino.h>
#include <SPI.h>
#include <LoRa.h>

// LoRa pins
#define LORA_SS   D8
#define LORA_RST  D0
#define LORA_DIO0 D2
#define LORA_FREQ 915E6

void setup() {
  Serial.begin(115200);

  LoRa.setPins(LORA_SS, LORA_RST, LORA_DIO0);
  if (!LoRa.begin(LORA_FREQ)) {
    Serial.println("LoRa failed");
    while (1);
  }

  Serial.println("Receiver ready");
}

void loop() {
  int packetSize = LoRa.parsePacket();
  if (packetSize) {
    while (LoRa.available()) {
      Serial.print((char)LoRa.read());
    }
    Serial.println();
  }
}
