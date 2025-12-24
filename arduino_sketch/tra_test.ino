#include <SPI.h>
#include <LoRa.h>

// Pin mapping for ESP8266
#define LORA_SS    15   // D8
#define LORA_RST   16   // D0
#define LORA_DIO0  5    // D1

String inputString = "";         // String to hold incoming serial data
bool stringComplete = false;     // Whether the string is complete

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

  // Set sync word to match receiver
  LoRa.setSyncWord(0xF3);
  
  Serial.println("LoRa Initialized Successfully.");
  Serial.println("Type your message and press Enter to send:");
  
  inputString.reserve(200);  // Reserve 200 bytes for input string
}

void loop() { 
  // Read serial input
  while (Serial.available()) {
    char inChar = (char)Serial.read();
    
    if (inChar == '\n' || inChar == '\r') {
      stringComplete = true;
    } else {
      inputString += inChar;
    }
  }
  
  // Send message when complete
  if (stringComplete) {
    if (inputString.length() > 0) {
      Serial.print("Sending: ");
      Serial.println(inputString);
      Serial.print("Length: ");
      Serial.println(inputString.length());

      LoRa.beginPacket();
      LoRa.print(inputString);
      int result = LoRa.endPacket();
      
      if (result == 1) {
        Serial.println("Message sent successfully!");
      } else {
        Serial.println("Send failed!");
      }
    }
    
    // Clear the string for next input
    inputString = "";
    stringComplete = false;
    Serial.println("Type your message and press Enter to send:");
  }
}