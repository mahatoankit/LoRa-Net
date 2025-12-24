import sounddevice as sd
import numpy as np

USB_PORT = '/dev/ttyUSB0'
SAMPLE_RATE = 16000
CHUNK = 1024  

def audio_callback(indata, frames, time, status):
    if status:
        print(status)
    data_int16 = (indata * 32767).astype(np.int16)
    
    with open(USB_PORT, 'ab') as f:
        f.write(data_int16.tobytes())

with sd.InputStream(samplerate=SAMPLE_RATE, channels=1, dtype='float32',
                    blocksize=CHUNK, callback=audio_callback):
    print("Streaming audio to", USB_PORT)
    while True:
        pass
