import sounddevice as sd
import numpy as np
import serial
import time

# -------- SERIAL CONFIG --------
SERIAL_PORT = "/dev/ttyUSB0"   # TRANSMITTER
BAUD_RATE = 115200

# -------- AUDIO CONFIG --------
SAMPLE_RATE = 44100
BLOCK_SIZE = 1024
THRESHOLD = 0.006     # tune if needed
COOLDOWN = 6.0        # seconds (prevents retrigger spam)

last_trigger = 0.0

ser = serial.Serial(SERIAL_PORT, BAUD_RATE)
time.sleep(2)
print("[OK] Serial connected to TX")

def audio_callback(indata, frames, time_info, status):
    global last_trigger
    volume = np.linalg.norm(indata) / frames
    now = time.time()

    print(f"volume: {volume:.4f}")

    if volume > THRESHOLD and (now - last_trigger) > COOLDOWN:
        ser.write(b"TRIGGER\n")
        print(">> TRIGGER SENT")
        last_trigger = now

print("[INFO] Listening to microphone (Ctrl+C to stop)")

with sd.InputStream(
    channels=1,
    samplerate=SAMPLE_RATE,
    blocksize=BLOCK_SIZE,
    callback=audio_callback
):
    try:
        while True:
            time.sleep(0.1)
    except KeyboardInterrupt:
        ser.close()
        print("\n[STOP] Exiting")
