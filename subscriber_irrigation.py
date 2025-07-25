import paho.mqtt.client as mqtt
import json
import sqlite3

MQTT_BROKER = "broker.mqttdashboard.com"
MQTT_SENSOR_TOPIC = "wokwi-weather"
MQTT_EVENTS_TOPIC = "irrigation-events"

def on_connect(client, userdata, flags, rc):
    print(f"Connected with result code {rc}")
    client.subscribe(MQTT_SENSOR_TOPIC)
    client.subscribe(MQTT_EVENTS_TOPIC)
    print(f"Subscribed to {MQTT_SENSOR_TOPIC} and {MQTT_EVENTS_TOPIC}")

def on_message(client, userdata, msg):
    try:
        topic = msg.topic
        data = json.loads(msg.payload.decode())
        
        if topic == MQTT_SENSOR_TOPIC:
            handle_sensor_data(data)
        elif topic == MQTT_EVENTS_TOPIC:
            handle_irrigation_event(data)
            
    except Exception as e:
        print(f"Error parsing or inserting data: {e}")

def handle_sensor_data(data):
    """Handle sensor data with irrigation information"""
    temperature = data.get("temp")
    humidity = data.get("humidity")
    sensor_id = data.get("sensor_id", "unknown")
    sensor_type = data.get("sensor_type", "unknown")
    latitude = data.get("latitude")
    longitude = data.get("longitude")
    description = data.get("description", "")
    
    # Level 3 irrigation fields
    irrigation_active = data.get("irrigation_active", False)
    irrigation_mode = data.get("irrigation_mode", "manual")
    humidity_threshold = data.get("humidity_threshold", 40)

    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    
    # Insert or update sensor metadata
    if latitude is not None and longitude is not None:
        cursor.execute('''
            INSERT OR REPLACE INTO sensors (sensor_id, sensor_type, latitude, longitude, description)
            VALUES (?, ?, ?, ?, ?)
        ''', (sensor_id, sensor_type, latitude, longitude, description))
    
    # Insert sensor data with irrigation information
    if temperature is not None or humidity is not None:
        cursor.execute('''
            INSERT INTO sensor_data 
            (sensor_id, temperature, humidity, irrigation_active, irrigation_mode, humidity_threshold)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (sensor_id, temperature, humidity, irrigation_active, irrigation_mode, humidity_threshold))
    
    # Update irrigation settings if this sensor has irrigation capability
    if irrigation_mode in ['manual', 'auto']:
        cursor.execute('''
            INSERT OR REPLACE INTO irrigation_settings 
            (sensor_id, mode, humidity_threshold, is_active, last_updated)
            VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
        ''', (sensor_id, irrigation_mode, humidity_threshold, irrigation_active))
        
    conn.commit()
    conn.close()

    status_indicator = "💧" if irrigation_active else "🏜️"
    print(f"Inserted data: sensor {sensor_id} ({sensor_type}), temp {temperature}, humidity {humidity} {status_indicator}")
    
    if latitude and longitude:
        print(f"  Location: {latitude}, {longitude}")
    
    if irrigation_mode and sensor_id != "unknown":
        irrigation_status = "ON" if irrigation_active else "OFF"
        print(f"  🌿 Irrigation: {irrigation_status} (Mode: {irrigation_mode}, Threshold: {humidity_threshold}%)")

def handle_irrigation_event(data):
    """Handle irrigation events and log them"""
    sensor_id = data.get("sensor_id", "unknown")
    event = data.get("event", "unknown")
    humidity = data.get("humidity")
    threshold = data.get("threshold")
    
    # Determine event type and trigger type
    if "started" in event:
        event_type = "start"
    elif "stopped" in event:
        event_type = "stop"
    else:
        event_type = "unknown"
    
    if "auto" in event:
        trigger_type = "auto"
    else:
        trigger_type = "manual"
    
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    
    # Insert irrigation event
    cursor.execute('''
        INSERT INTO irrigation_events 
        (sensor_id, event_type, trigger_type, humidity_value, threshold_value)
        VALUES (?, ?, ?, ?, ?)
    ''', (sensor_id, event_type, trigger_type, humidity, threshold))
    
    conn.commit()
    conn.close()
    
    print(f"🌿 IRRIGATION EVENT: {sensor_id} - {event_type.upper()} ({trigger_type})")
    if humidity and threshold:
        print(f"   Humidity: {humidity}% (Threshold: {threshold}%)")

if __name__ == "__main__":
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1)
    client.on_connect = on_connect
    client.on_message = on_message

    client.connect(MQTT_BROKER, 1883, 60)
    client.loop_forever()
