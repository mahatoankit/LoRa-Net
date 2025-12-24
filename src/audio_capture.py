import sounddevice as sd
import numpy as np
import serial
import time

# Set the correct COM/USB port for your ESP8266
# On Windows: COM3, COM4 etc.
# On Linux: /dev/ttyUSB0
SERIAL_PORT = '/dev/ttyUSB0'  
BAUD_RATE = 115200

# Connect to ESP8266
ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
time.sleep(2)  # wait for ESP8266 to reset

# Audio parameters
SAMPLE_RATE = 8000  # Hz
CHUNK = 1024  # frames per buffer

def audio_callback(indata, frames, time_info, status):
    # Convert to 1D numpy array (mono)
    audio_data = indata[:, 0]

    # Compute RMS (simple amplitude feature)
    rms = np.sqrt(np.mean(audio_data**2))

    # Optional: compute a thresholded event (simulate chainsaw detection)
    event = 1 if rms > 0.02 else 0

    # Prepare message to send to ESP8266
    msg = f"{rms:.5f},{event}\n"
    ser.write(msg.encode())

# Open audio input stream
with sd.InputStream(channels=1,
                    samplerate=SAMPLE_RATE,
                    blocksize=CHUNK,
                    callback=audio_callback):
    print("Streaming audio to ESP8266... Press Ctrl+C to stop.")
    while True:
        time.sleep(0.1)
