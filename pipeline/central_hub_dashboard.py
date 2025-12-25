"""
Central Hub Dashboard - Laptop Side

This script:
1. Receives alert packets from ESP8266 via serial
2. Parses and displays acoustic event alerts
3. Logs all events to file
4. Can forward to web dashboard (optional)

Serial Communication:
- Baud rate: 115200
- Receives format: DATA:EVT:TYPE;CONF:0.XX;LAT:XX.XX;LON:XX.XX;TS:TIMESTAMP;RSSI:-XX
"""

import serial
import serial.tools.list_ports
import time
import json
import logging
from datetime import datetime
import os
from threading import Thread
import queue

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# -------- Configuration --------
SERIAL_PORT = None  # Auto-detect or set manually
SERIAL_BAUD = 115200
OUTPUT_DIR = "hub_data"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Optional: WebSocket forwarding
ENABLE_WEBSOCKET = False
WEBSOCKET_URI = "ws://localhost:8000/ws"

alert_queue = queue.Queue()

def find_serial_port():
    """Auto-detect ESP8266 serial port"""
    ports = serial.tools.list_ports.comports()
    
    for port in ports:
        if any(x in port.description.lower() for x in ['ch340', 'cp210', 'usb serial', 'uart', 'esp']):
            logging.info(f"Found potential ESP8266 at: {port.device} - {port.description}")
            return port.device
    
    if ports:
        logging.warning("Could not auto-detect ESP8266. Available ports:")
        for port in ports:
            logging.warning(f"  {port.device} - {port.description}")
        return ports[0].device
    
    return None

def parse_alert_payload(payload):
    """
    Parse alert payload into dictionary
    Format: EVT:TYPE;CONF:0.XX;LAT:XX.XX;LON:XX.XX;TS:TIMESTAMP;NODE:NODEID;RSSI:-XX;SNR:X.X
    """
    alert = {}
    
    try:
        # Split by semicolon
        parts = payload.split(';')
        
        for part in parts:
            if ':' in part:
                key, value = part.split(':', 1)
                key = key.strip().lower()
                value = value.strip()
                
                # Parse specific fields
                if key == 'evt':
                    alert['event_type'] = value
                elif key == 'conf':
                    alert['confidence'] = float(value)
                elif key == 'lat':
                    alert['latitude'] = float(value)
                elif key == 'lon':
                    alert['longitude'] = float(value)
                elif key == 'ts':
                    alert['timestamp'] = int(value)
                    alert['datetime'] = datetime.fromtimestamp(int(value)).isoformat()
                elif key == 'node':
                    alert['node_id'] = value
                elif key == 'rssi':
                    alert['rssi'] = int(value)
                elif key == 'snr':
                    alert['snr'] = float(value)
        
        # Add received time
        alert['received_at'] = datetime.now().isoformat()
        
        return alert
        
    except Exception as e:
        logging.error(f"Failed to parse payload: {e}")
        return None

def display_alert(alert):
    """Display alert in a formatted way"""
    print("\n" + "=" * 60)
    print("🚨 ALERT RECEIVED 🚨")
    print("=" * 60)
    print(f"Event Type:   {alert.get('event_type', 'UNKNOWN')}")
    print(f"Confidence:   {alert.get('confidence', 0)*100:.1f}%")
    print(f"Location:     {alert.get('latitude', 'N/A')}, {alert.get('longitude', 'N/A')}")
    print(f"Timestamp:    {alert.get('datetime', 'N/A')}")
    print(f"Node ID:      {alert.get('node_id', 'N/A')}")
    print(f"Signal RSSI:  {alert.get('rssi', 'N/A')} dBm")
    print(f"Signal SNR:   {alert.get('snr', 'N/A')} dB")
    print(f"Received at:  {alert.get('received_at', 'N/A')}")
    print("=" * 60)
    print()

def save_alert(alert):
    """Save alert to JSON log file"""
    try:
        log_file = os.path.join(OUTPUT_DIR, 'alerts.jsonl')
        with open(log_file, 'a') as f:
            f.write(json.dumps(alert) + '\n')
    except Exception as e:
        logging.error(f"Failed to save alert: {e}")

def listen_serial(ser):
    """Listen to serial port and process incoming data"""
    logging.info("Listening for incoming alerts...")
    
    while True:
        try:
            if ser.in_waiting > 0:
                line = ser.readline().decode('utf-8', errors='ignore').strip()
                
                if not line:
                    continue
                
                # Check if this is alert data or debug message
                if line.startswith('DATA:'):
                    # Extract payload
                    payload = line[5:]  # Remove 'DATA:' prefix
                    
                    # Parse alert
                    alert = parse_alert_payload(payload)
                    
                    if alert:
                        alert_queue.put(alert)
                    else:
                        logging.warning(f"Failed to parse alert: {payload}")
                
                else:
                    # Debug message from ESP8266
                    logging.debug(f"[ESP8266] {line}")
                    
        except Exception as e:
            logging.error(f"Serial read error: {e}")
            time.sleep(1)

def process_alerts():
    """Process alerts from queue"""
    while True:
        try:
            alert = alert_queue.get()
            
            # Display alert
            display_alert(alert)
            
            # Save to file
            save_alert(alert)
            
            # Optional: Forward to websocket
            if ENABLE_WEBSOCKET:
                try:
                    import asyncio
                    import websockets
                    asyncio.run(send_to_websocket(alert))
                except Exception as e:
                    logging.error(f"WebSocket forwarding failed: {e}")
                    
        except Exception as e:
            logging.error(f"Alert processing error: {e}")

async def send_to_websocket(alert):
    """Forward alert to WebSocket server"""
    try:
        async with websockets.connect(WEBSOCKET_URI) as ws:
            await ws.send(json.dumps(alert))
    except Exception as e:
        logging.error(f"WebSocket error: {e}")

def main():
    """Main function"""
    global SERIAL_PORT
    
    print("\n" + "=" * 60)
    print("Central Hub Dashboard - Acoustic Monitoring System")
    print("=" * 60 + "\n")
    
    # Find serial port
    if SERIAL_PORT is None:
        SERIAL_PORT = find_serial_port()
    
    if SERIAL_PORT is None:
        logging.error("No serial port found! Please connect ESP8266.")
        return
    
    # Open serial connection
    try:
        ser = serial.Serial(SERIAL_PORT, SERIAL_BAUD, timeout=1)
        time.sleep(2)  # Wait for ESP8266 to initialize
        logging.info(f"Connected to: {SERIAL_PORT} @ {SERIAL_BAUD} baud")
    except Exception as e:
        logging.error(f"Failed to open serial port: {e}")
        return
    
    logging.info(f"Logs will be saved to: {OUTPUT_DIR}/alerts.jsonl")
    logging.info("Waiting for alerts...")
    print()
    
    # Start processing thread
    alert_thread = Thread(target=process_alerts, daemon=True)
    alert_thread.start()
    
    # Main thread listens to serial
    try:
        listen_serial(ser)
    except KeyboardInterrupt:
        print("\n\nShutting down...")
        ser.close()
        logging.info("Goodbye!")

if __name__ == "__main__":
    main()
