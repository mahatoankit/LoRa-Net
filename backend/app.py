# """
# Flask Backend Server for LoRa Forest Monitoring System
# Reads serial data from LoRa receiver, parses events, and exposes REST API + WebSocket endpoints.
# """
#
# import json
# import time
# import threading
# from datetime import datetime
# from collections import deque
# from flask import Flask, jsonify, request
# from flask_cors import CORS
# from flask_socketio import SocketIO, emit
# import serial
# import serial.tools.list_ports
#
# # Configuration
# SERIAL_PORT = "/dev/ttyUSB0"  # Update as needed
# SERIAL_BAUD = 9600
# MAX_EVENTS = 100  # Store last 100 events in memory
#
# app = Flask(__name__)
# CORS(app, resources={r"/*": {"origins": "*"}})
# socketio = SocketIO(app, cors_allowed_origins="*")
#
# # In-memory event storage
# events_storage = deque(maxlen=MAX_EVENTS)
# serial_connection = None
# serial_thread = None
# running = False
#
#
# def parse_payload(payload):
#     """
#     Parse LoRa payload string into structured JSON.
#
#     Input format: "EVT:GUNSHOT;CONF:0.91;LAT:27.70;LON:85.33;TS:1735119862"
#     Output format: {
#         "event": "GUNSHOT",
#         "confidence": 0.91,
#         "lat": 27.70,
#         "lon": 85.33,
#         "timestamp": 1735119862,
#         "received_at": "2024-12-25T10:30:00Z"
#     }
#     """
#     try:
#         parts = payload.strip().split(';')
#         event_data = {}
#
#         for part in parts:
#             if ':' in part:
#                 key, value = part.split(':', 1)
#
#                 if key == 'EVT':
#                     event_data['event'] = value
#                 elif key == 'CONF':
#                     event_data['confidence'] = float(value)
#                 elif key == 'LAT':
#                     event_data['lat'] = float(value)
#                 elif key == 'LON':
#                     event_data['lon'] = float(value)
#                 elif key == 'TS':
#                     event_data['timestamp'] = int(value)
#
#         # Add server-side timestamp
#         event_data['received_at'] = datetime.utcnow().isoformat() + 'Z'
#
#         return event_data
#
#     except (ValueError, KeyError) as e:
#         print(f"[ERROR] Failed to parse payload: {payload}")
#         print(f"[ERROR] Exception: {e}")
#         return None
#
#
# def read_serial_data():
#     """
#     Continuously read data from serial port in background thread.
#     Parses incoming LoRa data and stores events.
#     """
#     global serial_connection, running
#
#     print(f"[INFO] Attempting to connect to serial port: {SERIAL_PORT}")
#
#     try:
#         serial_connection = serial.Serial(
#             port=SERIAL_PORT,
#             baudrate=SERIAL_BAUD,
#             timeout=1
#         )
#         print(f"[OK] Serial connection established on {SERIAL_PORT} at {SERIAL_BAUD} baud")
#
#     except serial.SerialException as e:
#         print(f"[ERROR] Could not open serial port {SERIAL_PORT}: {e}")
#         print("[INFO] Running in demo mode without serial connection")
#         serial_connection = None
#
#     while running:
#         try:
#             if serial_connection and serial_connection.in_waiting > 0:
#                 # Read line from serial
#                 line = serial_connection.readline().decode('utf-8', errors='ignore').strip()
#
#                 if line:
#                     print(f"[SERIAL] Received: {line}")
#
#                     # Parse payload
#                     event_data = parse_payload(line)
#
#                     if event_data:
#                         # Store event
#                         events_storage.append(event_data)
#                         print(f"[OK] Event stored: {event_data['event']} (Confidence: {event_data['confidence']})")
#
#                         # Broadcast to WebSocket clients
#                         socketio.emit('new_event', event_data, namespace='/')
#                         print(f"[WS] Event broadcast to clients")
#
#             time.sleep(0.1)
#
#         except Exception as e:
#             print(f"[ERROR] Serial read error: {e}")
#             time.sleep(1)
#
#
# def list_serial_ports():
#     """List all available serial ports."""
#     ports = serial.tools.list_ports.comports()
#     available_ports = [port.device for port in ports]
#     return available_ports
#
#
# # REST API Endpoints
#
# @app.route('/')
# def index():
#     """Health check endpoint."""
#     return jsonify({
#         'status': 'running',
#         'service': 'LoRa Forest Monitoring Backend',
#         'version': '1.0.0',
#         'endpoints': {
#             'events': '/events',
#             'latest': '/events/latest',
#             'stats': '/stats',
#             'serial_ports': '/serial/ports'
#         }
#     })
#
#
# @app.route('/events', methods=['GET'])
# def get_events():
#     """
#     Get all stored events.
#     Query parameters:
#         - limit: Number of recent events to return (default: all)
#     """
#     limit = request.args.get('limit', type=int)
#
#     events_list = list(events_storage)
#
#     if limit and limit > 0:
#         events_list = events_list[-limit:]
#
#     return jsonify({
#         'success': True,
#         'count': len(events_list),
#         'events': events_list
#     })
#
#
# @app.route('/events/latest', methods=['GET'])
# def get_latest_event():
#     """Get the most recent event."""
#     if len(events_storage) > 0:
#         return jsonify({
#             'success': True,
#             'event': events_storage[-1]
#         })
#     else:
#         return jsonify({
#             'success': False,
#             'message': 'No events available'
#         }), 404
#
#
# @app.route('/stats', methods=['GET'])
# def get_stats():
#     """Get statistics about events."""
#     if len(events_storage) == 0:
#         return jsonify({
#             'success': True,
#             'total_events': 0,
#             'event_types': {}
#         })
#
#     # Count event types
#     event_types = {}
#     for event in events_storage:
#         event_type = event.get('event', 'UNKNOWN')
#         event_types[event_type] = event_types.get(event_type, 0) + 1
#
#     return jsonify({
#         'success': True,
#         'total_events': len(events_storage),
#         'event_types': event_types,
#         'latest_timestamp': events_storage[-1].get('received_at')
#     })
#
#
# @app.route('/serial/ports', methods=['GET'])
# def get_serial_ports():
#     """List available serial ports."""
#     ports = list_serial_ports()
#     return jsonify({
#         'success': True,
#         'ports': ports,
#         'current_port': SERIAL_PORT
#     })
#
#
# # WebSocket Events
#
# @socketio.on('connect')
# def handle_connect():
#     """Handle client connection to WebSocket."""
#     print(f"[WS] Client connected: {request.sid}")
#     emit('connection_response', {
#         'status': 'connected',
#         'message': 'Successfully connected to LoRa monitoring server'
#     })
#
#
# @socketio.on('disconnect')
# def handle_disconnect():
#     """Handle client disconnection from WebSocket."""
#     print(f"[WS] Client disconnected: {request.sid}")
#
#
# @socketio.on('request_events')
# def handle_request_events(data):
#     """Handle client request for all events."""
#     limit = data.get('limit', 10) if data else 10
#     events_list = list(events_storage)[-limit:]
#
#     emit('events_response', {
#         'success': True,
#         'count': len(events_list),
#         'events': events_list
#     })
#
#
# def start_serial_thread():
#     """Start the serial reading thread."""
#     global serial_thread, running
#
#     running = True
#     serial_thread = threading.Thread(target=read_serial_data, daemon=True)
#     serial_thread.start()
#     print("[INFO] Serial reading thread started")
#
#
# def stop_serial_thread():
#     """Stop the serial reading thread."""
#     global running, serial_connection
#
#     running = False
#     if serial_connection:
#         serial_connection.close()
#         print("[INFO] Serial connection closed")
#
#
# if __name__ == '__main__':
#     print("=" * 50)
#     print("LoRa Forest Monitoring System - Backend Server")
#     print("=" * 50)
#     print()
#
#     # List available serial ports
#     available_ports = list_serial_ports()
#     print(f"[INFO] Available serial ports: {available_ports}")
#     print()
#
#     # Start serial reading thread
#     start_serial_thread()
#
#     try:
#         # Start Flask server with SocketIO
#         print("[INFO] Starting Flask server...")
#         print("[INFO] API available at: http://localhost:5000")
#         print("[INFO] WebSocket available at: ws://localhost:5000")
#         print()
#
#         socketio.run(app, host='0.0.0.0', port=2000, debug=True, allow_unsafe_werkzeug=True)
#
#     except KeyboardInterrupt:
#         print("\n[INFO] Shutting down server...")
#         stop_serial_thread()
#         print("[INFO] Server stopped")




"""
Unified Flask Backend for LoRa Forest Monitoring
- Reads real serial LoRa data OR simulates events
- Exposes REST API
- Streams events via WebSocket
"""

import time
import random
import threading
from datetime import datetime
from collections import deque

from flask import Flask, jsonify, request, render_template
from flask_cors import CORS
from flask_socketio import SocketIO, emit

import serial
import serial.tools.list_ports

# ================= CONFIG =================

SERIAL_PORT = "/dev/ttyUSB0"
SERIAL_BAUD = 9600
MAX_EVENTS = 100
SIMULATION_INTERVAL = 5  # seconds

EVENT_TYPES = [
    "GUNSHOT", "SAW_MACHINE", "CHOPPING_TREE",
    "EXPLOSION", "VEHICLE_HORN", "ALARM"
]

# ================= APP =================

app = Flask(__name__)
CORS(app)

# FORCE THREADING (NO EVENTLET)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="threading")

events_storage = deque(maxlen=MAX_EVENTS)
serial_connection = None
running = True

# ================= HELPERS =================

def utc_now():
    return datetime.utcnow().isoformat() + "Z"


def broadcast_event(event):
    events_storage.append(event)
    socketio.emit("new_event", event)
    print(f"[WS] Broadcasted {event['event']} @ {event['lat']},{event['lon']}")


def parse_payload(payload):
    try:
        parts = payload.strip().split(";")
        data = {}

        for part in parts:
            if ":" not in part:
                continue
            k, v = part.split(":", 1)

            if k == "EVT":
                data["event"] = v
            elif k == "CONF":
                data["confidence"] = float(v)
            elif k == "LAT":
                data["lat"] = float(v)
            elif k == "LON":
                data["lon"] = float(v)
            elif k == "TS":
                data["timestamp"] = int(v)

        data["received_at"] = utc_now()
        return data

    except Exception as e:
        print("[ERROR] Payload parse failed:", e)
        return None


# ================= SERIAL THREAD =================

def read_serial():
    global serial_connection

    try:
        serial_connection = serial.Serial(
            SERIAL_PORT, SERIAL_BAUD, timeout=1
        )
        print(f"[OK] Serial connected: {SERIAL_PORT}")
    except Exception as e:
        print("[WARN] Serial unavailable, switching to simulation")
        serial_connection = None
        return

    while running:
        try:
            if serial_connection.in_waiting:
                line = serial_connection.readline().decode(errors="ignore").strip()
                if not line:
                    continue

                print("[SERIAL]", line)
                event = parse_payload(line)
                if event:
                    broadcast_event(event)

        except Exception as e:
            print("[ERROR] Serial read:", e)
            time.sleep(1)


@app.route("/dashboard")
def dashboard():
    return render_template("index.html")


# ================= SIMULATION THREAD =================

def simulate_events():
    while running:
        time.sleep(SIMULATION_INTERVAL)

        event = {
            "event": random.choice(EVENT_TYPES),
            "confidence": round(random.uniform(0.75, 0.99), 2),
            "lat": round(random.uniform(27.6, 27.8), 4),
            "lon": round(random.uniform(85.2, 85.4), 4),
            "timestamp": int(time.time()),
            "received_at": utc_now(),
        }

        broadcast_event(event)


# ================= REST API =================

@app.route("/")
def health():
    return jsonify({
        "status": "running",
        "events_cached": len(events_storage)
    })


@app.route("/events")
def get_events():
    limit = request.args.get("limit", type=int)
    data = list(events_storage)
    if limit:
        data = data[-limit:]
    return jsonify({"count": len(data), "events": data})


@app.route("/events/latest")
def latest():
    if not events_storage:
        return jsonify({"error": "no events"}), 404
    return jsonify(events_storage[-1])


@app.route("/serial/ports")
def serial_ports():
    ports = [p.device for p in serial.tools.list_ports.comports()]
    return jsonify({"ports": ports})


# ================= SOCKET.IO =================

@socketio.on("connect")
def on_connect():
    print("[WS] Client connected", request.sid)
    emit("initial_events", list(events_storage))


@socketio.on("disconnect")
def on_disconnect():
    print("[WS] Client disconnected", request.sid)


# ================= MAIN =================

if __name__ == "__main__":
    print("===================================")
    print(" LoRa Forest Monitoring Backend ")
    print("===================================")

    threading.Thread(target=read_serial, daemon=True).start()
    threading.Thread(target=simulate_events, daemon=True).start()

    socketio.run(
        app,
        host="0.0.0.0",
        port=5000,
        debug=True,
        allow_unsafe_werkzeug=True
    )
