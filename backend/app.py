import serial
import time
import threading
from datetime import datetime
from collections import deque
from flask import Flask, jsonify, render_template
from flask_socketio import SocketIO, emit
from flask_cors import CORS
from serial.serialutil import SerialException

app = Flask(__name__)
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

# Store last 100 records
history = deque(maxlen=100)

def parse_packet(raw_line):
    """
    Handles format: DATA:EVT:CRACKLING_FIRE;CONF:0.81;LAT:27.7126;LON:85.3426;TS:1766715169;NODE:NODE1;RSSI:-81;SNR:9.8
    """
    # try:
    line_str = raw_line.decode('utf-8', errors='ignore').strip()
    
    # Remove 'DATA:' prefix if it exists to make splitting cleaner
    if line_str.startswith("DATA:"):
        line_str = line_str.replace("DATA:", "", 1)
    
    pairs = line_str.split(';')
    data = {}
    for pair in pairs:
        if ':' in pair:
            # Split only on the first colon found in each segment
            key, value = pair.split(':', 1)
            data[key] = value

    # Process and cast types
    processed = {
        'event': data.get('EVT', "").replace('_', ' '), # "CRACKLING FIRE"
        'confidence': round(float(data.get('CONF', 0.0)) * 100, 1), # 81.0
        'lat': float(data.get('LAT', 0.0)),
        'lon': float(data.get('LON', 0.0)),
        "node" : 1,
        'timestamp': int(data.get('TS', 0)),
        'human_time': datetime.fromtimestamp(int(data.get('TS', 0))).strftime('%H:%M:%S | %b %d') if 'TS' in data else "N/A"
    }
    return processed

    # except Exception as e:
    #     print(f"[!] Parsing error on line [{line_str}]: {e}")
    #     return None

def serial_reader():
    ser = None
    while True:
        try:
            if ser is None or not ser.is_open:
                ser = serial.Serial('/dev/ttyUSB0', 115200, timeout=1)
                print("[+] Serial Connected")

            while True:
                if ser.in_waiting:
                    raw_data = ser.readline()
                    result = parse_packet(raw_data)

                    print(result, "++")

                    if result.get("event"):
                        history.appendleft(result)
                        print(result, "----")
                        socketio.emit('new_lora_event', result)
                    
                time.sleep(.1)

        except SerialException as d:
            print(d)

@app.route("/")
def index():
    return render_template("dashboard.html")

@app.route('/api/history')
def get_history():
    return jsonify(list(history))

if __name__ == "__main__":
    threading.Thread(target=serial_reader, daemon=True).start()
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)