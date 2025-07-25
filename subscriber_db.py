import paho.mqtt.client as mqtt
import json
import sqlite3

MQTT_BROKER = "broker.mqttdashboard.com"
MQTT_TOPIC = "wokwi-weather"

def on_connect(client, userdata, flags, rc):
    print(f"Connected with result code {rc}")
    client.subscribe(MQTT_TOPIC)

def on_message(client, userdata, msg):
    try:
        data = json.loads(msg.payload.decode())
        temperature = data.get("temp")
        humidity = data.get("humidity")
        sensor_id = data.get("sensor_id", "unknown")
        sensor_type = data.get("sensor_type", "unknown")
        latitude = data.get("latitude")
        longitude = data.get("longitude")
        description = data.get("description", "")

        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        
        # Insert or update sensor metadata
        if latitude is not None and longitude is not None:
            cursor.execute('''
                INSERT OR REPLACE INTO sensors (sensor_id, sensor_type, latitude, longitude, description)
                VALUES (?, ?, ?, ?, ?)
            ''', (sensor_id, sensor_type, latitude, longitude, description))
        
        # Insert sensor data (only if temp or humidity is not None)
        if temperature is not None or humidity is not None:
            cursor.execute('''
                INSERT INTO sensor_data (sensor_id, temperature, humidity)
                VALUES (?, ?, ?)
            ''', (sensor_id, temperature, humidity))
            
        conn.commit()
        conn.close()

        print(f"Inserted data: sensor {sensor_id} ({sensor_type}), temp {temperature}, humidity {humidity}")
        if latitude and longitude:
            print(f"  Location: {latitude}, {longitude}")
            
    except Exception as e:
        print(f"Error parsing or inserting data: {e}")

if __name__ == "__main__":
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1)
    client.on_connect = on_connect
    client.on_message = on_message

    client.connect(MQTT_BROKER, 1883, 60)
    client.loop_forever()
