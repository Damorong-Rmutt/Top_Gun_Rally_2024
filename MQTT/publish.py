import time
import random
import json
from datetime import datetime
import paho.mqtt.client as mqtt
import pytz

BROKER = "mqtt-broker"  # หรือ "localhost" หากรันในเครื่องเดียวกัน
PORT = 1883

# Topics
TOPICS = {
    "predictions": "audio/predictions",
    "machine_data": "machine/data",
}

mqtt_client = mqtt.Client()

def connect_mqtt():
    mqtt_client.connect(BROKER, PORT, 60)
    print("Connected to MQTT Broker")

def get_thailand_time():
    """Get current time in Thailand timezone."""
    tz = pytz.timezone('Asia/Bangkok')
    now = datetime.now(tz)
    return now.strftime("%H:%M:%S")

def publish_fake_data():
    connect_mqtt()
    while True:
        # สร้างข้อมูลสำหรับ `audio/predictions`
        prediction_data = {
            "timestamp": get_thailand_time(),
            "prediction": random.choice(["Normal", "Faulty"]),
        }

        # สร้างข้อมูลสำหรับ `machine/data`
        machine_data = {
            "timestamp": get_thailand_time(),
            "energy_consumption": round(random.uniform(50.0, 150.0), 2),
            "pressure": round(random.uniform(1000.0, 2000.0), 2),
            "punch": round(random.uniform(10.0, 50.0), 2),
            "position_of_punch": round(random.uniform(0.0, 10.0), 2),
        }

        # ส่งข้อมูลไปยัง `audio/predictions`
        mqtt_client.publish(TOPICS["predictions"], json.dumps(prediction_data))
        print(f"Published to {TOPICS['predictions']}: {prediction_data}")

        # ส่งข้อมูลไปยัง `machine/data`
        mqtt_client.publish(TOPICS["machine_data"], json.dumps(machine_data))
        print(f"Published to {TOPICS['machine_data']}: {machine_data}")

        time.sleep(0.2)  # ส่งข้อมูลทุก 2 วินาที

if __name__ == "__main__":
    publish_fake_data()
