import serial
import time
from datetime import datetime

# --- CONFIGURATION ---
SERIAL_PORT = '/dev/ttyUSB0'       # Replace with '/dev/ttyUSB0' or similar
BAUD_RATE = 115200         # Match your LoRa module settings
RECONNECT_DELAY = 5        # Seconds to wait before trying to reconnect

def parse_packet(raw_line):
    """
    Parses a raw line like: "EVT:GUNSHOT;CONF:0.91;LAT:27.70;LON:85.33;TS:1735119862"
    Returns a dictionary with converted data types.
    """
    try:
        # 1. Decode bytes to string
        line_str = raw_line.decode('utf-8', errors='ignore').strip()
        
        # 2. Split into pairs (e.g., ["EVT:GUNSHOT", "CONF:0.91"])
        pairs = line_str.split(';')
        
        data = {}
        for pair in pairs:
            if ':' in pair:
                key, value = pair.split(':', 1) # Split only on the first colon
                data[key] = value

        # 3. Type Conversion (Make the data usable)
        processed = {
            'event': data.get('EVT', 'UNKNOWN'),
            'confidence': float(data.get('CONF', 0.0)),
            'lat': float(data.get('LAT', 0.0)),
            'lon': float(data.get('LON', 0.0)),
            'timestamp': int(data.get('TS', 0)),
            'raw_ts': data.get('TS')
        }
        
        # Convert Unix timestamp to human-readable time
        if processed['timestamp'] > 0:
            processed['human_time'] = datetime.fromtimestamp(processed['timestamp'])
            
        return processed

    except ValueError as e:
        print(f"[!] Data conversion error: {e}")
        return None
    except Exception as e:
        print(f"[!] Parsing error: {e}")
        return None

def main_loop():
    ser = None
    
    while True:
        try:
            # Attempt connection
            if ser is None or not ser.is_open:
                print(f"[*] Attempting to connect to {SERIAL_PORT}...")
                ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
                print(f"[+] Connected successfully.")

            # Reading loop
            while True:
                if ser.in_waiting > 0:
                    raw_data = ser.readline()
                    
                    # Parse the data
                    result = parse_packet(raw_data)
                    
                    if result:
                        print("------------------------------------------------")
                        print(f"⚠️  EVENT DETECTED: {result['event']}")
                        print(f"📍 Location:       {result['lat']}, {result['lon']}")
                        print(f"🎯 Confidence:     {result['confidence'] * 100:.1f}%")
                        print(f"🕒 Time:           {result.get('human_time', 'N/A')}")
                        print("------------------------------------------------")
                
                # Small sleep to prevent CPU hogging
                time.sleep(0.01)

        except serial.SerialException:
            print(f"[!] Connection lost. Retrying in {RECONNECT_DELAY} seconds...")
            if ser:
                ser.close()
            time.sleep(RECONNECT_DELAY)
            
        except KeyboardInterrupt:
            print("\n[!] User stopped script.")
            if ser: 
                ser.close()
            break

if __name__ == "__main__":
    main_loop()