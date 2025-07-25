import paho.mqtt.client as mqtt
import json
import random
import time
import threading

MQTT_BROKER = "broker.mqttdashboard.com"
MQTT_TOPIC = "wokwi-weather"

# Define multiple sensors with their positions
SENSORS = [
    {
        "sensor_id": "temp-sensor-001",
        "sensor_type": "temperature",
        "latitude": 48.8566,
        "longitude": 2.3522,
        "description": "Paris Temperature Sensor"
    },
    {
        "sensor_id": "humid-sensor-001", 
        "sensor_type": "humidity",
        "latitude": 48.8566,
        "longitude": 2.3522,
        "description": "Paris Humidity Sensor"
    },
    {
        "sensor_id": "temp-sensor-002",
        "sensor_type": "temperature", 
        "latitude": 45.4642,
        "longitude": 9.1900,
        "description": "Milan Temperature Sensor"
    },
    {
        "sensor_id": "humid-sensor-002",
        "sensor_type": "humidity",
        "latitude": 45.4642,
        "longitude": 9.1900,
        "description": "Milan Humidity Sensor"
    }
]

def publish_sensor_data(sensor_config, client):
    """Publish data for a specific sensor"""
    while True:
        try:
            if sensor_config["sensor_type"] == "temperature":
                data = {
                    "sensor_id": sensor_config["sensor_id"],
                    "sensor_type": sensor_config["sensor_type"],
                    "temp": round(random.uniform(18, 32), 2),
                    "humidity": None,  # Temperature-only sensor
                    "latitude": sensor_config["latitude"],
                    "longitude": sensor_config["longitude"],
                    "description": sensor_config["description"]
                }
            elif sensor_config["sensor_type"] == "humidity":
                data = {
                    "sensor_id": sensor_config["sensor_id"],
                    "sensor_type": sensor_config["sensor_type"],
                    "temp": None,  # Humidity-only sensor
                    "humidity": round(random.uniform(30, 80), 2),
                    "latitude": sensor_config["latitude"],
                    "longitude": sensor_config["longitude"],
                    "description": sensor_config["description"]
                }
            
            client.publish(MQTT_TOPIC, json.dumps(data))
            print(f"Published from {sensor_config['sensor_id']}: {data}")
            
            # Random interval between 3-8 seconds
            time.sleep(random.uniform(3, 8))
            
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"Error publishing from {sensor_config['sensor_id']}: {e}")
            time.sleep(5)

if __name__ == "__main__":
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1, "multi_sensor_publisher")
    client.connect(MQTT_BROKER, 1883, 60)
    client.loop_start()
    
    threads = []
    
    try:
        # Start a thread for each sensor
        for sensor in SENSORS:
            thread = threading.Thread(target=publish_sensor_data, args=(sensor, client))
            thread.daemon = True
            thread.start()
            threads.append(thread)
            print(f"Started publisher for {sensor['sensor_id']}")
        
        # Keep main thread alive
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\nShutting down publishers...")
        client.loop_stop()
        client.disconnect()
