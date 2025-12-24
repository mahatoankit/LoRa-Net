import sounddevice as sd
import serial
import time

SERIAL_PORT = '/dev/ttyUSB0'
BAUD_RATE = 115200

# Open serial
ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
time.sleep(2)

SAMPLE_RATE = 8000
CHUNK = 256  # small chunk to stream continuously

def audio_callback(indata, frames, time_info, status):
    # Convert to 8-bit unsigned integer
    audio_bytes = ((indata[:,0] + 1.0) * 127.5).astype('uint8')
    ser.write(audio_bytes.tobytes())

# Open input stream
with sd.InputStream(channels=1,
                    samplerate=SAMPLE_RATE,
                    blocksize=CHUNK,
                    callback=audio_callback):
    print("Streaming raw audio to NodeMCU...")
    while True:
        pass
