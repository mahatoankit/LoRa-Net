#pragma once
#include <Arduino.h>
#include <math.h>

// Dummy features just to test ML + LoRa
inline void extract_features(float* out) {
  for (int i = 0; i < 10; i++) {
    float energy = random(1, 1000);
    out[i] = logf(energy + 1e-6f);
  }
}
