// ================================
// ESP8266 LoRa RECEIVER (STABLE)
// ================================

#include <Arduino.h>
#include <SPI.h>
#include <LoRa.h>

// -------- Pins --------
#define LORA_SS   D4
#define LORA_RST  D0
#define LORA_DIO0 D2

// -------- LoRa Config --------
#define LORA_FREQ 433E6
#define SPREADING_FACTOR 7
#define SIGNAL_BANDWIDTH 125E3

#define LED_PIN LED_BUILTIN
#define SERIAL_BAUD 115200

void setup() {
  Serial.begin(SERIAL_BAUD);
  delay(200); // ESP8266-safe Serial startup

  pinMode(LED_PIN, OUTPUT);
  digitalWrite(LED_PIN, HIGH);

  Serial.println("\n[RX] Booting Receiver...");

  SPI.begin(D5, D6, D7, LORA_SS);

  pinMode(LORA_RST, OUTPUT);
  digitalWrite(LORA_RST, LOW);
  delay(10);
  digitalWrite(LORA_RST, HIGH);
  delay(10);

  LoRa.setPins(LORA_SS, LORA_RST, LORA_DIO0);

  if (!LoRa.begin(LORA_FREQ)) {
    Serial.println("[RX] LoRa init FAILED");
    while (1) {
      digitalWrite(LED_PIN, LOW);
      delay(100);
      digitalWrite(LED_PIN, HIGH);
      delay(100);
    }
  }

  LoRa.setSpreadingFactor(SPREADING_FACTOR);
  LoRa.setSignalBandwidth(SIGNAL_BANDWIDTH);
  LoRa.enableCrc();

  Serial.println("[RX] LoRa Ready @ 433 MHz");
  Serial.println("[RX] Waiting for packets...");
}

void loop() {
  int packetSize = LoRa.parsePacket();
  if (!packetSize) return;

  digitalWrite(LED_PIN, LOW);

  char buffer[256];
  int i = 0;

  while (LoRa.available() && i < 255) {
    buffer[i++] = (char)LoRa.read();
  }
  buffer[i] = '\0';

  int rssi = LoRa.packetRssi();
  float snr = LoRa.packetSnr();

  Serial.print("DATA:");
  Serial.print(buffer);
  Serial.print(";RSSI:");
  Serial.print(rssi);
  Serial.print(";SNR:");
  Serial.println(snr, 1);

  digitalWrite(LED_PIN, HIGH);
}
