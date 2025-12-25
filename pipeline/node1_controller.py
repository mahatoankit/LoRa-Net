"""
Node 1 Controller - Laptop Side

This script:
1. Captures audio from microphone
2. Runs ML inference to detect acoustic events
3. Sends alert packets to ESP8266 via serial when events are detected
4. ESP8266 forwards alerts via LoRa to Central Hub

Serial Communication:
- Baud rate: 115200
- Format: EVT:TYPE;CONF:0.XX;LAT:XX.XX;LON:XX.XX;TS:TIMESTAMP\n
"""

import os
import json
import time
import warnings
from threading import Thread
import datetime
import serial
import serial.tools.list_ports
from record_sound import record_sound
from run_inference import run_inference
import logging
import queue

warnings.filterwarnings("ignore")
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# -------- Configuration --------
SERIAL_PORT = None  # Auto-detect or set to '/dev/ttyUSB0', 'COM3', etc.
SERIAL_BAUD = 115200
ALERT_THRESHOLD = 0.6  # Minimum confidence to send alert
GPS_LAT = 27.712623  # Default GPS coordinates (update with actual GPS module)
GPS_LON = 85.342602
NODE_ID = "NODE1"
TEST_MODE = True  # Set to False when ESP8266 is connected

# Events that should trigger alerts (customize based on your model)
ALERT_EVENTS = [
    "gunshot", "scream", "glass_break", "explosion", "chainsaw",
    "AXE Chopping", "hand_saw"  # Add your dangerous/suspicious event classes
]

# -------- Global Variables --------
audio_queue = queue.Queue()
result_queue = queue.Queue()
ser = None

OUTPUT_DIR = "outputs"
os.makedirs(OUTPUT_DIR, exist_ok=True)

def find_serial_port():
    """Auto-detect ESP8266 serial port"""
    ports = serial.tools.list_ports.comports()
    
    for port in ports:
        # Common ESP8266 identifiers
        if any(x in port.description.lower() for x in ['ch340', 'cp210', 'usb serial', 'uart', 'esp']):
            logging.info(f"Found potential ESP8266 at: {port.device} - {port.description}")
            return port.device
    
    # If no specific match, list all available ports
    if ports:
        logging.warning("Could not auto-detect ESP8266. Available ports:")
        for port in ports:
            logging.warning(f"  {port.device} - {port.description}")
        return ports[0].device
    
    return None

def init_serial():
    """Initialize serial connection to ESP8266"""
    global ser, SERIAL_PORT
    
    if SERIAL_PORT is None:
        SERIAL_PORT = find_serial_port()
    
    if SERIAL_PORT is None:
        logging.error("No serial port found! Please connect ESP8266.")
        return False
    
    try:
        ser = serial.Serial(SERIAL_PORT, SERIAL_BAUD, timeout=1)
        time.sleep(2)  # Wait for ESP8266 to initialize
        logging.info(f"Serial connection established: {SERIAL_PORT} @ {SERIAL_BAUD} baud")
        return True
    except Exception as e:
        logging.error(f"Failed to open serial port {SERIAL_PORT}: {e}")
        return False

def send_alert_to_esp8266(event_type, confidence, lat, lon, timestamp):
    """
    Send alert packet to ESP8266 via serial
    Format: EVT:TYPE;CONF:0.XX;LAT:XX.XX;LON:XX.XX;TS:TIMESTAMP
    """
    global ser
    
    # Format the payload
    payload = f"EVT:{event_type.upper()};CONF:{confidence:.2f};LAT:{lat:.4f};LON:{lon:.4f};TS:{timestamp};NODE:{NODE_ID}"
    
    # Test mode - just log without sending
    if TEST_MODE:
        logging.warning(f"[TEST MODE - Would send via serial] {payload}")
        return True
    
    try:
        if ser and ser.is_open:
            # Send with newline terminator
            ser.write((payload + '\n').encode('utf-8'))
            ser.flush()
            logging.info(f"[SERIAL TX] {payload}")
            return True
        else:
            logging.error("Serial port not open!")
            return False
    except Exception as e:
        logging.error(f"Failed to send via serial: {e}")
        return False

def collect_audio():
    """Continuously capture audio chunks"""
    logging.info("Audio capture thread started")
    while True:
        try:
            audio, sample_rate = record_sound()  # Captures audio chunk
            audio_queue.put((audio, sample_rate))
        except Exception as e:
            logging.error(f"Audio capture error: {e}")
            time.sleep(1)

def run_inference_loop():
    """Process audio and run ML inference"""
    logging.info("Inference thread started")
    
    while True:
        try:
            audio, sample_rate = audio_queue.get()
            
            # Run inference
            classes, confidences = run_inference(audio, sample_rate)
            
            # Create result dictionary
            result = {
                'timestamp': int(time.time()),
                'datetime': datetime.datetime.now().isoformat(),
                'latitude': GPS_LAT,
                'longitude': GPS_LON,
                'classes': classes,
                'confidences': confidences,
                'node_id': NODE_ID
            }
            
            result_queue.put(result)
            
            # Log results
            logging.info("Inference complete:")
            for cls, conf in zip(classes[:3], confidences[:3]):  # Top 3 results
                logging.info(f"  {cls}: {conf:.2f}%")
                
        except Exception as e:
            logging.error(f"Inference error: {e}")

def process_and_send_alerts():
    """Process inference results and send alerts via serial"""
    logging.info("Alert processing thread started")
    
    while True:
        try:
            result = result_queue.get()
            
            # Find highest confidence event
            max_idx = 0
            max_conf = result['confidences'][0] / 100.0  # Convert percentage to 0-1
            
            for i, conf in enumerate(result['confidences']):
                if conf > result['confidences'][max_idx]:
                    max_idx = i
                    max_conf = conf / 100.0
            
            detected_class = result['classes'][max_idx]
            
            # Check if this event should trigger an alert
            should_alert = False
            for alert_event in ALERT_EVENTS:
                if alert_event.lower() in detected_class.lower():
                    should_alert = True
                    break
            
            # Send alert if confidence is high enough and it's an alert event
            if should_alert and max_conf >= ALERT_THRESHOLD:
                logging.warning(f"🚨 ALERT TRIGGERED: {detected_class} (confidence: {max_conf:.2%})")
                
                send_alert_to_esp8266(
                    event_type=detected_class,
                    confidence=max_conf,
                    lat=result['latitude'],
                    lon=result['longitude'],
                    timestamp=result['timestamp']
                )
            
            # Log all results to file
            with open(os.path.join(OUTPUT_DIR, 'detection_log.jsonl'), 'a') as f:
                f.write(json.dumps(result) + '\n')
                
        except Exception as e:
            logging.error(f"Alert processing error: {e}")

def main():
    """Main function"""
    logging.info("=" * 50)
    logging.info("Node 1 Controller - Acoustic Monitoring System")
    logging.info("=" * 50)
    
    if TEST_MODE:
        logging.warning("⚠️  RUNNING IN TEST MODE (No serial communication)")
        logging.warning("Set TEST_MODE = False when ESP8266 is connected")
    else:
        # Initialize serial connection
        if not init_serial():
            logging.error("Failed to initialize serial connection. Exiting.")
            return
    
    # Start threads
    logging.info("Starting processing threads...")
    
    audio_thread = Thread(target=collect_audio, daemon=True)
    inference_thread = Thread(target=run_inference_loop, daemon=True)
    alert_thread = Thread(target=process_and_send_alerts, daemon=True)
    
    audio_thread.start()
    inference_thread.start()
    alert_thread.start()
    
    logging.info("All threads started successfully")
    logging.info("System is now monitoring for acoustic events...")
    logging.info(f"Alert threshold: {ALERT_THRESHOLD*100:.0f}%")
    logging.info(f"Monitoring for events: {', '.join(ALERT_EVENTS)}")
    logging.info("=" * 50)
    
    # Keep main thread alive and monitor serial responses
    try:
        while True:
            if not TEST_MODE and ser and ser.is_open and ser.in_waiting > 0:
                # Read any debug messages from ESP8266
                response = ser.readline().decode('utf-8', errors='ignore').strip()
                if response:
                    logging.debug(f"[ESP8266] {response}")
            time.sleep(0.1)
    except KeyboardInterrupt:
        logging.info("\nShutting down...")
        if not TEST_MODE and ser and ser.is_open:
            ser.close()
        logging.info("Goodbye!")

if __name__ == "__main__":
    main()
