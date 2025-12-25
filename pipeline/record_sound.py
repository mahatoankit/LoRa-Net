import numpy as np
import sounddevice as sd
from scipy.signal import resample
from scipy.io.wavfile import write
import sys


def list_audio_devices():
    """List all available audio input devices"""
    print("\n=== Available Audio Devices ===")
    devices = sd.query_devices()
    for idx, device in enumerate(devices):
        if device['max_input_channels'] > 0:
            print(f"[{idx}] {device['name']}")
            print(f"    Channels: {device['max_input_channels']}, Sample Rate: {device['default_samplerate']} Hz")
    print("=" * 40)
    print()


def record_sound(counter=None, device_index=None, duration=5):
    """
    Record audio from microphone
    
    Args:
        counter: Optional counter for saving to file
        device_index: Microphone device index (None = default)
        duration: Recording duration in seconds
    
    Returns:
        audio: Audio data as numpy array
        sample_rate: Sample rate in Hz
    """
    try:
        # Use default device if not specified
        if device_index is None:
            device_info = sd.query_devices(kind='input')
            device_index = sd.default.device[0]  # Get default input device
        else:
            device_info = sd.query_devices(device_index)
        
        # Get the actual number of input channels available
        max_channels = int(device_info['max_input_channels'])
        sample_rate = int(device_info['default_samplerate'])
        
        # Use 1 channel if mono is available, otherwise use minimum available
        channels = min(1, max_channels)
        
        # Record audio
        audio = sd.rec(
            int(duration * sample_rate),
            samplerate=sample_rate,
            channels=channels,
            dtype='float32',
            device=device_index
        )
        sd.wait()
        
        # Convert to mono if multi-channel
        if audio.ndim > 1:
            audio = audio.mean(axis=1)
        else:
            audio = audio.squeeze()

        if counter is not None:
            write(f"outputs/{counter}.wav", sample_rate, audio)
            print(f"Written file {counter}.wav")

        return audio, sample_rate
        
    except Exception as e:
        raise Exception(f"Audio recording failed: {e}")


if __name__ == "__main__":
    # List available devices
    list_audio_devices()
    
    # Test recording
    print("Testing audio recording (5 seconds)...")
    try:
        audio, sr = record_sound(1)
        print(f"✓ Recording successful! Shape: {audio.shape}, Sample rate: {sr} Hz")
    except Exception as e:
        print(f"✗ Recording failed: {e}")
        sys.exit(1)
