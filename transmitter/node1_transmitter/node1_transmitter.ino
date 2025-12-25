// =======================================
// ESP8266 LoRa TRANSMITTER (433 MHz) – FINAL
// =======================================

#include <Arduino.h>
#include <SPI.h>
#include <LoRa.h>

// -------- LoRa Pins --------
#define LORA_SS   D4
#define LORA_RST  D0
#define LORA_DIO0 D2

// -------- LoRa Config --------
#define LORA_FREQ 433E6
#define SPREADING_FACTOR 7
#define SIGNAL_BANDWIDTH 125E3
#define TX_POWER 17

#define SERIAL_BAUD 115200
#define LED_PIN LED_BUILTIN

unsigned long seq = 0;

void setup() {
  Serial.begin(SERIAL_BAUD);
  delay(200);

  pinMode(LED_PIN, OUTPUT);
  digitalWrite(LED_PIN, HIGH);

  Serial.println("\n[TX] Booting Node Transmitter");

  // ESP8266 SPI → NO PIN ARGUMENTS
  SPI.begin();

  // Manual LoRa reset
  pinMode(LORA_RST, OUTPUT);
  digitalWrite(LORA_RST, LOW);
  delay(10);
  digitalWrite(LORA_RST, HIGH);
  delay(10);

  LoRa.setPins(LORA_SS, LORA_RST, LORA_DIO0);

  if (!LoRa.begin(LORA_FREQ)) {
    Serial.println("[TX] LoRa init FAILED");
    while (1) {
      digitalWrite(LED_PIN, LOW);
      delay(100);
      digitalWrite(LED_PIN, HIGH);
      delay(100);
    }
  }

  LoRa.setSpreadingFactor(SPREADING_FACTOR);
  LoRa.setSignalBandwidth(SIGNAL_BANDWIDTH);
  LoRa.setTxPower(TX_POWER);
  LoRa.enableCrc();

  Serial.println("[TX] LoRa initialized successfully");
}

void loop() {
  digitalWrite(LED_PIN, LOW);

  char payload[128];
  snprintf(
    payload,
    sizeof(payload),
    "EVT:TEST;CONF:1.00;NODE:1;SEQ:%lu",
    seq++
  );

  Serial.print("[TX] Sending: ");
  Serial.println(payload);

  LoRa.beginPacket();
  LoRa.print(payload);
  LoRa.endPacket();

  digitalWrite(LED_PIN, HIGH);
  delay(2000);
}
