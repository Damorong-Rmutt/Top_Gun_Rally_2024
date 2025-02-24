import paho.mqtt.client as mqtt
import mysql.connector
import time

# MySQL setup
def setup_database():
    conn = mysql.connector.connect(
        host="db",  # Replace with your MySQL server hostname
        user="root",                 # Replace with your MySQL username
        password="root",     # Replace with your MySQL password
        database="mqtt_db"           # Replace with your database name
    )
    cursor = conn.cursor()
    # Ensure the table exists
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id INT AUTO_INCREMENT PRIMARY KEY,
            topic VARCHAR(255) NOT NULL,
            payload TEXT NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    return conn

# Callback when the client connects to the broker
def on_connect(client, userdata, flags, return_code):
    if return_code == 0:
        print("Connected successfully")
        client.subscribe("test/#")  # Replace with your topic
    else:
        print(f"Failed to connect, return code: {return_code}")

# Callback when a message is received
def on_message(client, userdata, message):
    print(f"Received message on topic {message.topic}: {message.payload.decode('utf-8')}")
    # Insert message into the database
    cursor = userdata['db_conn'].cursor()
    cursor.execute(
        "INSERT INTO messages (topic, payload) VALUES (%s, %s)",
        (message.topic, message.payload.decode('utf-8'))
    )
    userdata['db_conn'].commit()

# MQTT client setup
def main():
    # Set up the database connection
    db_conn = setup_database()

    # Create the MQTT client
    client = mqtt.Client(userdata={"db_conn": db_conn})
    #client.username_pw_set("admin", "test")  # Replace with your MQTT credentials
    client.on_connect = on_connect
    client.on_message = on_message

    # Connect to the MQTT broker
    client.connect("host.docker.internal", 1883)  # Replace with your broker address
    client.loop_start()

    try:
        while True:
            time.sleep(1)  # Keep the script running
    except KeyboardInterrupt:
        print("Stopping...")
    finally:
        client.disconnect()
        client.loop_stop()
        db_conn.close()

if __name__ == "__main__":
    main()
