import websocket
import json
import mysql.connector

api_key = "d461a1c66600c00454145f7e17b588dd"
url = f"ws://technest.ddns.net:8001/ws?apikey={api_key}"

db_config = {
    "host":"100.125.25.71", 
    "user": "root",
    "password": "root",
    "database": "machine_data"
}

def insert_data_to_db(data):
    """
    Insert received data into the MySQL database.
    """
    conn = None
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()

        power = data["Energy Consumption"]["Power"]
        voltage_l1 = data["Voltage"]["L1-GND"]
        voltage_l2 = data["Voltage"]["L2-GND"]
        voltage_l3 = data["Voltage"]["L3-GND"]
        pressure = data["Pressure"]
        force = data["Force"]
        cycle_count = data["Cycle Count"]
        punch_position = data["Position of the Punch"]

        query = """
        INSERT INTO sensor_data
        (power, voltage_l1_gnd, voltage_l2_gnd, voltage_l3_gnd, pressure, `forces`, cycle_count, position)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """
        values = (power, voltage_l1, voltage_l2, voltage_l3, pressure, force, cycle_count, punch_position)
        cursor.execute(query, values)
        conn.commit()

        print("Data inserted into database:", values)

    except Exception as e:
        print("Error inserting data into database:", e)

    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()


def on_message(ws, message):
    try:    
        data = json.loads(message)

        print("Energy Consumption:")
        print(f"  Power: {data['Energy Consumption']['Power']}")

        print("\nVoltage:")
        for key, value in data['Voltage'].items():
            print(f"  {key}: {value}")

        print("\nPressure:", data['Pressure'])
        print("Force:", data['Force'])
        print("Cycle Count:", data['Cycle Count'])
        print("Position of the Punch:", data['Position of the Punch'])
        insert_data_to_db(data)

    except Exception as e:
        print("Error processing message:", e)

def on_error(ws, error):
    print("WebSocket error:", error)

def on_close(ws, close_status_code, close_msg):
    print("WebSocket connection closed")

def on_open(ws):
    print("WebSocket connection opened")
    ws.send(api_key)

ws = websocket.WebSocketApp(
    url,
    on_message=on_message,
    on_error=on_error,
    on_close=on_close
)

ws.on_open = on_open
ws.run_forever()