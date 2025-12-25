// =======================================
// ESP8266 LoRa RECEIVER (433 MHz) – FINAL
// =======================================

#include <Arduino.h>
#include <SPI.h>
#include <LoRa.h>

// -------- LoRa Pins (ESP8266) --------
#define LORA_SS   D4    // GPIO2
#define LORA_RST  D0    // GPIO16
#define LORA_DIO0 D2    // GPIO4

// -------- LoRa Config --------
#define LORA_FREQ 433E6
#define SPREADING_FACTOR 7
#define SIGNAL_BANDWIDTH 125E3

#define SERIAL_BAUD 115200
#define LED_PIN LED_BUILTIN

void setup() {
  Serial.begin(SERIAL_BAUD);
  delay(200);               // IMPORTANT for ESP8266
  
  pinMode(LED_PIN, OUTPUT);
  digitalWrite(LED_PIN, HIGH);

  Serial.println("\n[RX] Booting Central Hub Receiver");

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

  Serial.println("[RX] LoRa initialized successfully");
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
