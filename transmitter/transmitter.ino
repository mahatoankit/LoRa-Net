#include <Arduino.h>
#include <SPI.h>
#include <LoRa.h>
#include <math.h>

#include "model_data.h"
#include "features.h"

// -------- LoRa pins (ESP8266 + Ra-02) --------
#define LORA_SS   D8
#define LORA_RST  D0
#define LORA_DIO0 D2
#define LORA_FREQ 915E6   // change if needed

// -------- TFLite Micro --------
#include "tensorflow/lite/micro/all_ops_resolver.h"
#include "tensorflow/lite/micro/micro_interpreter.h"
#include "tensorflow/lite/schema/schema_generated.h"
#include "tensorflow/lite/version.h"

constexpr int kTensorArenaSize = 8 * 1024;
uint8_t tensor_arena[kTensorArenaSize];

tflite::MicroInterpreter* interpreter;
TfLiteTensor* input;
TfLiteTensor* output;

void setup() {
  Serial.begin(115200);

  // ---- LoRa ----
  LoRa.setPins(LORA_SS, LORA_RST, LORA_DIO0);
  if (!LoRa.begin(LORA_FREQ)) {
    Serial.println("LoRa failed");
    while (1);
  }
  Serial.println("LoRa ready");

  // ---- TFLite ----
  const tflite::Model* model = tflite::GetModel(audio_model_int8_tflite);
  static tflite::AllOpsResolver resolver;

  static tflite::MicroInterpreter static_interpreter(
    model, resolver, tensor_arena, kTensorArenaSize
  );
  interpreter = &static_interpreter;

  if (interpreter->AllocateTensors() != kTfLiteOk) {
    Serial.println("AllocateTensors failed");
    while (1);
  }

  input = interpreter->input(0);
  output = interpreter->output(0);

  Serial.println("Model ready");
}

void loop() {
  float features[10];
  extract_features(features);   // dummy for now

  // ---- Quantize input ----
  for (int i = 0; i < 10; i++) {
    input->data.int8[i] = (int8_t)round(
      features[i] / input->params.scale + input->params.zero_point
    );
  }

  interpreter->Invoke();

  // ---- Output ----
  int8_t q = output->data.int8[0];
  float confidence =
    (q - output->params.zero_point) * output->params.scale;

  Serial.println(confidence, 4);

  if (confidence > 0.6) {
    LoRa.beginPacket();
    LoRa.print("EVENT");
    LoRa.endPacket();
    delay(5000);
  }

  delay(200);
}
