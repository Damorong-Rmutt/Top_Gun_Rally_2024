import asyncio
import json
import random
from datetime import datetime, timezone, timedelta
from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
import paho.mqtt.client as mqtt

app = FastAPI()

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# MQTT Configuration
BROKER = "100.125.25.71"  # Replace with your broker address
PORT = 1883
TOPICS = ["commando/classification", "machine/data"]

# WebSocket Connections
websocket_connections = []

# Data Storage
data = {
    "classification": {},
    "machine_data": {},
    "prediction_data": {}
}

# Helper to get Thailand Time
def get_thailand_time():
    thailand_timezone = timezone(timedelta(hours=7))
    return datetime.now(thailand_timezone).strftime("%Y-%m-%d %H:%M:%S")

# MQTT Client Setup
mqtt_client = mqtt.Client()

def on_message(client, userdata, message):
    """
    Callback function to handle incoming MQTT messages.
    """
    global data
    topic = message.topic
    payload = message.payload.decode("utf-8")
    print(f"Received message from topic '{topic}': {payload}")

    try:
        # Process `audio/classification`
        if topic == "commando/classification":
            classification_data = json.loads(payload)
            data["classification"] = classification_data

        # Process `machine/data`
        elif topic == "machine/data":
            machine_data = json.loads(payload)
            data["machine_data"] = machine_data

        # Broadcast updated data to WebSocket clients
        full_data = {
            "classification": data.get("classification", {}),
            "machine_data": data.get("machine_data", {}),
        }
        print(f"Broadcasting to WebSocket clients: {full_data}")
        for websocket in websocket_connections:
            asyncio.create_task(websocket.send_json(full_data))

    except json.JSONDecodeError:
        print(f"Invalid JSON received on topic '{topic}': {payload}")
    except Exception as e:
        print(f"Error processing MQTT message: {e}")

mqtt_client.on_message = on_message
mqtt_client.connect(BROKER, PORT, 60)

# Subscribe to topics
for topic in TOPICS:
    mqtt_client.subscribe(topic)
    print(f"Subscribed to topic: {topic}")

mqtt_client.loop_start()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for real-time communication with clients.
    """
    await websocket.accept()
    websocket_connections.append(websocket)
    print(f"WebSocket client connected. Total connections: {len(websocket_connections)}")
    try:
        while True:
            await websocket.receive_text()  # Keep connection alive
    except Exception as e:
        print(f"WebSocket disconnected: {e}")
    finally:
        websocket_connections.remove(websocket)
        print(f"WebSocket client disconnected. Total connections: {len(websocket_connections)}")

@app.get("/status")
async def get_status():
    """
    Endpoint to get the latest data.
    """
    return data
