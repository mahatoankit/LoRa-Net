# # pi_client.py
# # ---------------------------------------------------------------
# # pip install websockets
# import asyncio, websockets, json, uuid, datetime as dt, random

# URI = "ws://192.168.102.198:8000/ws"          # change to server address

# def fake_detect() -> dict:
#     return {
#         "device_id": "pi-001",
#         "top_class": random.choice(["chainsaw", "rain", "insects", "axe_chopping"]),
#         "def_prob":  round(random.uniform(0.05, 0.95), 3)
#     }

# async def main():
#     async with websockets.connect(URI) as ws:
#         while True:
#             msg = fake_detect()
#             msg["clip_id"]   = uuid.uuid4().hex
#             msg["timestamp"] = dt.datetime.utcnow().isoformat() + "Z"
#             await ws.send(json.dumps(msg))
#             await asyncio.sleep(1)   # next 1-second chunk

# asyncio.run(main())



import threading, queue, time, json, websockets, asyncio

audio_queue = queue.Queue()
result_queue = queue.Queue()

# --- 1. Audio recording thread ---
def record_audio_loop():
    while True:
        audio = ...   # get 1 sec audio chunk as np.array or bytes
        audio_queue.put(audio)
        time.sleep(1) # Simulate timing

# --- 2. Inference thread ---
def inference_loop():
    while True:
        audio = audio_queue.get()
        pred = run_model(audio)   # Replace with your model code
        result = {
            "class": pred["class"],
            "confidence": float(pred["confidence"]),
            "timestamp": time.time()
        }
        result_queue.put(result)

# --- 3. WebSocket sender thread (runs async in its own event loop) ---
async def ws_send_loop():
    uri = "ws://<server-ip>:8000/ws"
    async with websockets.connect(uri) as ws:
        while True:
            result = await asyncio.get_event_loop().run_in_executor(
                None, result_queue.get
            )
            await ws.send(json.dumps(result))
            # (optional) receive from server: reply = await ws.recv()

def start_ws_thread():
    asyncio.run(ws_send_loop())

# --- Start all threads ---
threading.Thread(target=record_audio_loop, daemon=True).start()
threading.Thread(target=inference_loop, daemon=True).start()
threading.Thread(target=start_ws_thread, daemon=True).start()

# --- Keep main thread alive ---
while True:
    time.sleep(5)
