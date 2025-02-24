import paho.mqtt.client as mqtt
import mysql.connector
import json
from datetime import datetime

# ตั้งค่า MySQL Database
DB_CONFIG = {
    "host": "db",
    "user": "root",
    "password": "root",
    "database": "machine_data"
}

# ตั้งค่า MQTT Broker
BROKER = "mqtt-broker"
PORT = 1883
TOPIC = "audio/report"

# ฟังก์ชันบันทึกข้อมูลลง MySQL
def save_to_database(data):
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # SQL Query สำหรับบันทึกข้อมูล
        sql = """
        INSERT INTO classification_results (timestamp, event, classification, confidence)
        VALUES (%s, %s, %s, %s)
        """
        values = (
            datetime.strptime(data["timestamp"], "%Y-%m-%dT%H:%M:%SZ"),
            data["event"],
            data["classification"],
            float(data["confidence"])
        )
        cursor.execute(sql, values)
        conn.commit()
        print("Data saved to database.")
    except mysql.connector.Error as err:
        print(f"Error: {err}")
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

# Callback เมื่อมีข้อมูลเข้ามา
def on_message(client, userdata, msg):
    try:
        data = json.loads(msg.payload.decode())
        print(f"Received data: {data}")
        save_to_database(data)
    except Exception as e:
        print(f"Error: {e}")

# เริ่มต้น Subscriber
def start_server():
    client = mqtt.Client()
    client.on_message = on_message
    client.connect(BROKER, PORT)
    client.subscribe(TOPIC)
    print(f"Subscribed to topic {TOPIC}")
    client.loop_forever()

if __name__ == "__main__":
    start_server()
