# Distributed Acoustic Monitoring System

A low-resource acoustic monitoring system using LoRa for long-range wireless communication between field sensors and a central hub.

## System Architecture

```
┌─────────────────────────────────────────┐
│         NODE 1 (Field Sensor)           │
│  ┌──────────┐          ┌──────────┐    │
│  │  Laptop  │  Serial  │ ESP8266  │    │
│  │  + Mic   │◄────────►│ + LoRa   │    │
│  │  + ML    │ 115200   │  RA-02   │    │
│  └──────────┘          └────┬─────┘    │
└─────────────────────────────┼──────────┘
                              │
                         LoRa │ 433 MHz
                              │ ~1-2 km
                              │
┌─────────────────────────────┼──────────┐
│         CENTRAL HUB                     │
│  ┌──────────┐          ┌───┴──────┐    │
│  │Dashboard │  Serial  │ ESP8266  │    │
│  │  Laptop  │◄────────►│ + LoRa   │    │
│  │          │ 115200   │  RA-02   │    │
│  └──────────┘          └──────────┘    │
└─────────────────────────────────────────┘
```

## Features

- **Edge Processing**: ML inference runs on field laptop (no audio transmitted)
- **Low Bandwidth**: Only small alert packets (~60 bytes) sent over LoRa
- **Long Range**: LoRa provides 1-2 km range (line of sight up to 10 km)
- **Low Power**: Optimized for embedded systems using TFLite models
- **Real-time Alerts**: Instant notification of acoustic events

## Hardware Requirements

### Node 1 (Field Sensor)
- Laptop with microphone
- ESP8266 (NodeMCU, Wemos D1 Mini, etc.)
- LoRa RA-02 module (433 MHz)
- USB cable for ESP8266

### Central Hub (Receiver)
- Laptop for dashboard
- ESP8266 (NodeMCU, Wemos D1 Mini, etc.)
- LoRa RA-02 module (433 MHz)
- USB cable for ESP8266

### Wiring (Both Nodes)

| LoRa RA-02 | ESP8266 Pin | NodeMCU Pin |
|------------|-------------|-------------|
| VCC        | 3.3V        | 3.3V        |
| GND        | GND         | GND         |
| NSS        | GPIO15      | D8          |
| SCK        | GPIO14      | D5          |
| MISO       | GPIO12      | D6          |
| MOSI       | GPIO13      | D7          |
| RST        | GPIO16      | D0          |
| DIO0       | GPIO4       | D2          |

## Software Setup

### 1. Arduino IDE Setup

Install required libraries:
```
- LoRa by Sandeep Mistry (v0.8.0+)
```

**For Node 1 Transmitter:**
1. Open `transmitter/node1_transmitter.ino`
2. Verify pin configuration matches your wiring
3. Upload to ESP8266

**For Central Hub Receiver:**
1. Open `receiver/central_hub_receiver.ino`
2. Verify pin configuration matches your wiring
3. Upload to ESP8266

### 2. Python Environment Setup

**On both laptops:**

```bash
cd pipeline/
pip install -r requirements.txt
```

Required packages:
- tensorflow (or tensorflow-lite)
- numpy
- pyserial
- sounddevice (or pyaudio)
- scikit-learn
- joblib

### 3. Convert Keras Model to TFLite (Optional but Recommended)

For better performance on edge devices:

```python
import tensorflow as tf

# Load your Keras model
model = tf.keras.models.load_model('multi_class_audio_classifier.h5')

# Convert to TFLite
converter = tf.lite.TFLiteConverter.from_keras_model(model)
converter.optimizations = [tf.lite.Optimize.DEFAULT]
tflite_model = converter.convert()

# Save
with open('multi_class_audio_classifier.tflite', 'wb') as f:
    f.write(tflite_model)
```

## Usage

### Node 1 (Field Sensor)

1. **Upload Arduino sketch:**
   - Flash `transmitter/node1_transmitter.ino` to ESP8266
   - Open Serial Monitor (115200 baud) to verify initialization

2. **Run Python controller:**
   ```bash
   cd pipeline/
   python node1_controller.py
   ```

3. **Configure alert events:**
   Edit `node1_controller.py`:
   ```python
   ALERT_EVENTS = [
       "gunshot", "scream", "glass_break", "chainsaw"
   ]
   ALERT_THRESHOLD = 0.6  # Minimum confidence
   ```

4. **Update GPS coordinates:**
   ```python
   GPS_LAT = 27.712623
   GPS_LON = 85.342602
   ```

### Central Hub (Receiver)

1. **Upload Arduino sketch:**
   - Flash `receiver/central_hub_receiver.ino` to ESP8266
   - Open Serial Monitor (115200 baud) to verify initialization

2. **Run dashboard:**
   ```bash
   cd pipeline/
   python central_hub_dashboard.py
   ```

3. **View alerts:**
   - Alerts will be displayed in terminal
   - Logs saved to `hub_data/alerts.jsonl`

## Data Flow

### 1. Audio Capture (Node 1 Laptop)
```python
audio, sr = record_sound()  # Captures 5s audio chunk
```

### 2. ML Inference (Node 1 Laptop)
```python
classes, confidences = run_inference(audio, sr)
# Example output: ["gunshot", "unknown", ...], [0.91, 0.05, ...]
```

### 3. Alert Detection (Node 1 Laptop)
```python
if detected_class in ALERT_EVENTS and confidence > ALERT_THRESHOLD:
    send_alert_to_esp8266(event_type, confidence, lat, lon, timestamp)
```

### 4. Serial → LoRa (Node 1 ESP8266)
```
Laptop → Serial → ESP8266
Format: EVT:GUNSHOT;CONF:0.91;LAT:27.70;LON:85.33;TS:1735119862\n
```

### 5. LoRa Transmission (Node 1 ESP8266)
```cpp
LoRa.beginPacket();
LoRa.print(payload);
LoRa.endPacket();
```

### 6. LoRa Reception (Central Hub ESP8266)
```cpp
String data = LoRa.readString();
int rssi = LoRa.packetRssi();
```

### 7. LoRa → Serial (Central Hub ESP8266)
```
ESP8266 → Serial → Dashboard
Format: DATA:EVT:GUNSHOT;CONF:0.91;LAT:27.70;LON:85.33;TS:1735119862;RSSI:-45;SNR:8.5\n
```

### 8. Dashboard Display (Central Hub Laptop)
```
🚨 ALERT RECEIVED 🚨
Event Type:   GUNSHOT
Confidence:   91.0%
Location:     27.7126, 85.3426
Timestamp:    2025-12-25T09:30:42
Signal RSSI:  -45 dBm
```

## Payload Format

### Serial: Laptop → ESP8266
```
EVT:TYPE;CONF:0.XX;LAT:XX.XXXX;LON:XX.XXXX;TS:TIMESTAMP;NODE:NODEID\n
```

Example:
```
EVT:GUNSHOT;CONF:0.91;LAT:27.7126;LON:85.3426;TS:1735119862;NODE:NODE1\n
```

### LoRa: Node 1 → Central Hub
Same format as above (no changes by ESP8266)

### Serial: ESP8266 → Dashboard
```
DATA:EVT:TYPE;CONF:0.XX;LAT:XX.XXXX;LON:XX.XXXX;TS:TIMESTAMP;NODE:NODEID;RSSI:XX;SNR:X.X\n
```

Example:
```
DATA:EVT:GUNSHOT;CONF:0.91;LAT:27.7126;LON:85.3426;TS:1735119862;NODE:NODE1;RSSI:-45;SNR:8.5\n
```

## Configuration

### LoRa Parameters (Must match on both nodes)

In Arduino sketches:
```cpp
#define LORA_FREQ 433E6        // 433 MHz (or 915E6 for 915 MHz)
#define SPREADING_FACTOR 7     // SF7-SF9 (lower = faster, less range)
#define SIGNAL_BANDWIDTH 125E3 // 125 kHz
#define TX_POWER 17            // 2-20 dBm
```

### Python Configuration

**node1_controller.py:**
```python
SERIAL_PORT = None          # Auto-detect or '/dev/ttyUSB0', 'COM3'
SERIAL_BAUD = 115200
ALERT_THRESHOLD = 0.6       # Minimum confidence (0.0-1.0)
GPS_LAT = 27.712623         # Update with actual GPS
GPS_LON = 85.342602
NODE_ID = "NODE1"
```

**central_hub_dashboard.py:**
```python
SERIAL_PORT = None          # Auto-detect or set manually
SERIAL_BAUD = 115200
OUTPUT_DIR = "hub_data"     # Log directory
```

## Troubleshooting

### ESP8266 Not Initializing
1. Check wiring (especially power and ground)
2. Verify pin definitions match your board
3. Try different USB cable/port
4. Check if LoRa module is genuine (433 MHz vs 915 MHz)

### No LoRa Reception
1. Verify frequency matches on both nodes (433 MHz or 915 MHz)
2. Check spreading factor and bandwidth are identical
3. Ensure antennas are connected
4. Check distance (start with <10m for testing)
5. Verify both devices initialized successfully (check Serial Monitor)

### Serial Port Issues
1. Linux: Add user to dialout group: `sudo usermod -a -G dialout $USER`
2. Check port permissions: `ls -l /dev/ttyUSB0`
3. Close Serial Monitor before running Python scripts
4. Try different USB ports

### Model Not Loading
1. Ensure `label_binarizer.pkl` is in pipeline directory
2. Check if `yamnet.tflite` exists in `models/` directory
3. Verify Python packages installed: `pip list | grep tensorflow`

### High False Positive Rate
1. Increase `ALERT_THRESHOLD` (e.g., from 0.6 to 0.75)
2. Refine `ALERT_EVENTS` list to be more specific
3. Retrain model with more balanced dataset

## Performance Optimization

### Memory Usage
- TFLite models: ~10 MB (vs ~40 MB for Keras)
- Packet size: <60 bytes
- RAM usage: ~50 MB Python process

### Latency
- Audio capture: 5 seconds
- Inference: 2-5 seconds (depends on hardware)
- LoRa transmission: <1 second
- Total: ~7-10 seconds from event to dashboard

### Range
- Urban: 500m - 1 km
- Rural: 1-2 km
- Line of sight: up to 10 km

### Power Consumption
- ESP8266 TX: ~170 mA
- ESP8266 RX: ~60 mA
- Can run on battery with solar panel

## Files Overview

```
├── transmitter/
│   └── node1_transmitter.ino      # ESP8266 transmitter code
├── receiver/
│   └── central_hub_receiver.ino   # ESP8266 receiver code
├── pipeline/
│   ├── node1_controller.py        # Field laptop controller
│   ├── central_hub_dashboard.py   # Central hub dashboard
│   ├── run_inference.py           # Optimized ML inference
│   ├── record_sound.py            # Audio capture
│   ├── read_gps.py                # GPS reading (optional)
│   └── requirements.txt           # Python dependencies
├── models/
│   ├── yamnet.tflite              # YAMNet embedding model
│   └── multi_class_audio_classifier.h5  # Classification model
└── README_SYSTEM.md               # This file
```

## License

MIT License - Feel free to use and modify for your needs.

## Acknowledgments

- YAMNet model: Google Research
- LoRa library: Sandeep Mistry
- TensorFlow Lite: TensorFlow Team
