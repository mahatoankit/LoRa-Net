import os
import json
import time
import warnings
from threading import Thread
import datetime
# from read_gps import read_gps
from record_sound import record_sound
import asyncio, websockets, json, queue
from run_inference import run_inference
import logging

warnings.filterwarnings("ignore")
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
latest_audio = None
sample_rate = None

audio_queue = queue.Queue()
result_queue = queue.Queue()

URI = "ws://192.168.102.198:8000/ws"          # change to server address

OUTPUT_DIR = "outputs"
os.makedirs(OUTPUT_DIR, exist_ok=True)
print(f"Ensured output directory '{OUTPUT_DIR}' exists.")

def collect_input():
    global latest_audio, sample_rate
    while True:
        audio, sample_rate = record_sound()  # 5s chunk
        audio_queue.put(audio)
        time.sleep(1)

def run_model_loop():
    global latest_audio
    while True:
        audio = audio_queue.get()

        classes, confidence = run_inference(
            audio, sample_rate)

        result = None
        if result is None:
            result = {}
            result['time'] = str(datetime.date.today())
            result['date'] = str(datetime.datetime.now().strftime("%H:%M:%S"))
            result['latitude'] = "27.712623 N"
            result['longitude'] = "85.342602 E"
            result['speed'] = "NA"

        result['class'] = classes
        result['confidence'] = confidence

        result_queue.put(result)

async def ws_send_loop():
    uri = "ws://192.168.102.198:8000/ws"
    async with websockets.connect(uri, ping_interval=None) as ws:
        while True:
            result = await asyncio.get_event_loop().run_in_executor(
                None, result_queue.get
            )
            await ws.send(json.dumps(result))

            with open('logs.txt', 'a') as f:
                f.writelines(json.dumps(result))
                f.write('\n')

def start_ws_thread():
    asyncio.run(ws_send_loop())

Thread(target=collect_input, daemon=True).start()
Thread(target=run_model_loop, daemon=True).start()
Thread(target=start_ws_thread, daemon=True).start()


while True:
    time.sleep(1)


