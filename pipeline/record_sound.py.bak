import numpy as np
import sounddevice as sd
from scipy.signal import resample
from scipy.io.wavfile import write


def record_sound(counter=None):
    duration = 5  # seconds
    device_index = 1  # Change this to your mic’s index from previous step
    sample_rate = sd.query_devices(device_index)['default_samplerate']  # Hz
    audio = sd.rec(int(duration * sample_rate), samplerate=sample_rate,
                   channels=1, dtype='float32', device=device_index)
    sd.wait()
    audio = audio.squeeze(1)

    if counter is not None:
        write(f"outputs/{counter}.wav", sample_rate, audio)
        print(f"Written file {counter}.wav")

    if __name__ != "__main__":
        return audio, sample_rate


if __name__ == "__main__":
    record_sound(1)
