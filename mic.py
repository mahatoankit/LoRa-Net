import numpy as np
import sounddevice as sd
import serial
import time

# =======================
# Serial config
# =======================
SERIAL_PORT = "/dev/ttyUSB0"
BAUD_RATE = 115200

# =======================
# Audio config
# =======================
SAMPLE_RATE = 8000
FRAME_SIZE = 256   # ~32 ms @ 8 kHz

# =======================
# Model quantization params
# =======================
INPUT_SCALE = 0.04135602340102196
INPUT_ZERO_POINT = -96

# =======================
# Frame header
# =======================
HEADER = b'\xAA\x55'

# =======================
# Feature extraction
# =======================
def extract_features(window):
    rms = np.sqrt(np.mean(window ** 2))
    zcr = np.mean(np.abs(np.diff(np.sign(window)))) / 2
    peak = np.max(np.abs(window))
    variance = np.var(window)

    return np.array([rms, zcr, peak, variance], dtype=np.float32)

def quantize_features(x):
    q = np.round(x / INPUT_SCALE) + INPUT_ZERO_POINT
    return np.clip(q, -128, 127).astype(np.int8)

# =======================
# Main loop (STRICT SERIAL)
# =======================
print("Starting phase-based audio → ESP transfer")

while True:
    print("Recording audio frame...")

    # ---- PHASE 1: RECORD ----
    audio = sd.rec(
        frames=FRAME_SIZE,
        samplerate=SAMPLE_RATE,
        channels=1,
        dtype="float32"
    )
    sd.wait()
    window = audio[:, 0]

    # ---- PHASE 2: FEATURE + QUANT ----
    features = extract_features(window)
    q_features = quantize_features(features)

    print("Features:", features)
    print("Quantized:", q_features)

    # ---- PHASE 3: SERIAL SEND ----
    print("Opening serial...")
    ser = serial.Serial(SERIAL_PORT, BAUD_RATE)
    time.sleep(2)  # ESP reset / settle

    ser.write(HEADER + q_features.tobytes())
    ser.flush()

    ser.close()
    print("Frame sent. Serial closed.")

    # ---- PHASE 4: COOLDOWN ----
    print("Cooling down for 60 seconds...\n")
    time.sleep(60)