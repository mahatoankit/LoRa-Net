import json, uuid, datetime
from typing import Set
from fastapi import FastAPI, WebSocket, WebSocketDisconnect

app = FastAPI()
CLIENTS: Set[WebSocket] = set()            # live sockets

def iso_now() -> str:
    return datetime.datetime.utcnow().isoformat(timespec="milliseconds") + "Z"

@app.websocket("/ws")
async def relay(ws: WebSocket):
    await ws.accept()
    CLIENTS.add(ws)
    print("✔ WS joined:", ws.client)

    try:
        async for txt in ws.iter_text():           # Pi sends frames; dashboards rarely do
            try:
                msg = json.loads(txt)
            except json.JSONDecodeError:
                continue                           # Ignore bad frames

            # === PRINT THE RECEIVED MESSAGE ===
            print(f"📩 Received from {ws.client}: {msg}")

            print("\n----------------------------------- \n ")
            for n in range(len(msg["class"])):
                print(f"{msg["class"][n]}: {msg["confidence"][n]}")
                print("\n")

            # ensure id + timestamp
            msg.setdefault("id", str(uuid.uuid4()))
            msg.setdefault("timestamp", iso_now())

            # broadcast to every client
            dead = set()
            for cli in CLIENTS:
                try: await cli.send_text(json.dumps(msg))
                except WebSocketDisconnect: dead.add(cli)
            CLIENTS.difference_update(dead)


    finally:
        CLIENTS.discard(ws)
        print("✖ WS left  :", ws.client)
