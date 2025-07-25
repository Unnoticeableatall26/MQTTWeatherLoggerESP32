import network
import time
from machine import Pin, PWM
import dht
import ujson
from umqtt.simple import MQTTClient

MQTT_CLIENT_ID = "multi-irrigation-system"
MQTT_BROKER    = "broker.mqttdashboard.com"
MQTT_SENSOR_TOPIC = "wokwi-weather"
MQTT_CONTROL_TOPIC = "irrigation-control"

# Multi-Location Sensor and Irrigation Configuration
LOCATIONS = {
    "paris": {
        "name": "Paris Garden",
        "latitude": 48.8566,
        "longitude": 2.3522,
        "sensors": {
            "temp": {"pin": 15, "type": "DHT22"},
            "humidity": {"pin": 15, "type": "DHT22"}  # Same DHT22 for both
        },
        "irrigation": {
            "servo_pin": 18,
            "zone_id": "zone_001",
            "threshold": 35,
            "active": False
        }
    },
    "milan": {
        "name": "Milan Greenhouse", 
        "latitude": 45.4642,
        "longitude": 9.1900,
        "sensors": {
            "temp": {"pin": 16, "type": "DHT22"},
            "humidity": {"pin": 16, "type": "DHT22"}  # Simulated second sensor
        },
        "irrigation": {
            "servo_pin": 19,
            "zone_id": "zone_002", 
            "threshold": 40,
            "active": False
        }
    },
    "geneva": {
        "name": "Geneva Research Station",
        "latitude": 46.2044,
        "longitude": 6.1432,
        "sensors": {
            "temp": {"pin": 17, "type": "DHT22"},
            "humidity": {"pin": 17, "type": "DHT22"}  # Simulated third sensor
        },
        "irrigation": {
            "servo_pin": 21,
            "zone_id": "zone_003",
            "threshold": 38,
            "active": False
        }
    }
}

# Configuration des pins pour compatibilité tests Level 4
dht_pins = {
    "zone_001": 4,   # Paris DHT22
    "zone_002": 2,   # Milan DHT22  
    "zone_003": 15   # Geneva DHT22
}

servo_pins = {
    "zone_001": 18,  # Paris servo
    "zone_002": 19,  # Milan servo
    "zone_003": 21   # Geneva servo
}

# Servo positions
SERVO_CLOSED = 40
SERVO_OPEN = 115

# Global settings
irrigation_mode = "auto"  # "manual" or "auto"
system_active = True

# Initialize hardware
sensors = {}
servos = {}

# Setup sensors and servos for each location
for location_id, config in LOCATIONS.items():
    # Initialize DHT22 sensor
    sensor_pin = config["sensors"]["temp"]["pin"]
    sensors[location_id] = dht.DHT22(Pin(sensor_pin))
    
    # Initialize servo motor
    servo_pin = config["irrigation"]["servo_pin"]
    servos[location_id] = PWM(Pin(servo_pin), freq=50)
    servos[location_id].duty(SERVO_CLOSED)  # Start closed
    
    print(f"🌍 Initialized {config['name']} - Sensor: Pin {sensor_pin}, Servo: Pin {servo_pin}")

def set_irrigation_status(location_id, status):
    """Control irrigation for specific location"""
    if location_id not in LOCATIONS:
        print(f"❌ Unknown location: {location_id}")
        return False
        
    servo = servos[location_id]
    location_name = LOCATIONS[location_id]["name"]
    
    if status:
        servo.duty(SERVO_OPEN)
        LOCATIONS[location_id]["irrigation"]["active"] = True
        print(f"💧 {location_name} irrigation: ON")
    else:
        servo.duty(SERVO_CLOSED)
        LOCATIONS[location_id]["irrigation"]["active"] = False
        print(f"🏜️ {location_name} irrigation: OFF")
    
    return True

def on_message(topic, msg):
    """Handle MQTT control messages for multi-zone irrigation"""
    global irrigation_mode, system_active
    
    try:
        data = ujson.loads(msg.decode())
        command = data.get("command")
        target_zone = data.get("zone_id", "all")
        
        print(f"📨 Received command: {command} for zone: {target_zone}")
        
        if command == "irrigation_on":
            if target_zone == "all":
                for location_id in LOCATIONS.keys():
                    set_irrigation_status(location_id, True)
            else:
                location_id = find_location_by_zone(target_zone)
                if location_id:
                    set_irrigation_status(location_id, True)
                    
        elif command == "irrigation_off":
            if target_zone == "all":
                for location_id in LOCATIONS.keys():
                    set_irrigation_status(location_id, False)
            else:
                location_id = find_location_by_zone(target_zone)
                if location_id:
                    set_irrigation_status(location_id, False)
                    
        elif command == "set_mode":
            irrigation_mode = data.get("mode", "manual")
            print(f"🔧 System mode changed to: {irrigation_mode}")
            
        elif command == "set_threshold":
            threshold = data.get("threshold", 40)
            if target_zone == "all":
                for location_id in LOCATIONS.keys():
                    LOCATIONS[location_id]["irrigation"]["threshold"] = threshold
                print(f"📊 All zones threshold set to: {threshold}%")
            else:
                location_id = find_location_by_zone(target_zone)
                if location_id:
                    LOCATIONS[location_id]["irrigation"]["threshold"] = threshold
                    print(f"📊 {LOCATIONS[location_id]['name']} threshold set to: {threshold}%")
                    
        elif command == "system_status":
            send_system_status()
            
    except Exception as e:
        print(f"❌ Error processing command: {e}")

def find_location_by_zone(zone_id):
    """Find location by zone ID"""
    for location_id, config in LOCATIONS.items():
        if config["irrigation"]["zone_id"] == zone_id:
            return location_id
    return None

def check_automatic_irrigation():
    """Check all locations for automatic irrigation triggers"""
    if irrigation_mode != "auto" or not system_active:
        return
        
    for location_id, config in LOCATIONS.items():
        try:
            # Read sensor data
            sensor = sensors[location_id]
            sensor.measure()
            humidity = sensor.humidity()
            
            threshold = config["irrigation"]["threshold"]
            currently_active = config["irrigation"]["active"]
            
            # Check if irrigation should be activated
            if humidity < threshold and not currently_active:
                set_irrigation_status(location_id, True)
                send_irrigation_event(location_id, "auto_start", humidity, threshold)
                
            # Check if irrigation should be deactivated (with hysteresis)
            elif humidity > threshold + 10 and currently_active:
                set_irrigation_status(location_id, False)
                send_irrigation_event(location_id, "auto_stop", humidity, threshold)
                
        except Exception as e:
            print(f"❌ Error checking {location_id}: {e}")

def send_irrigation_event(location_id, event_type, humidity, threshold):
    """Send irrigation event notification"""
    config = LOCATIONS[location_id]
    
    event_data = {
        "sensor_id": f"irrigation-{location_id}",
        "event": f"{event_type}_irrigation",
        "location": config["name"],
        "zone_id": config["irrigation"]["zone_id"],
        "humidity": humidity,
        "threshold": threshold,
        "latitude": config["latitude"],
        "longitude": config["longitude"],
        "timestamp": time.time()
    }
    
    client.publish("irrigation-events", ujson.dumps(event_data))
    print(f"🌿 Event sent: {event_type} for {config['name']}")

def send_system_status():
    """Send complete system status"""
    status_data = {
        "system_id": MQTT_CLIENT_ID,
        "mode": irrigation_mode,
        "active": system_active,
        "zones": []
    }
    
    for location_id, config in LOCATIONS.items():
        try:
            sensor = sensors[location_id]
            sensor.measure()
            
            zone_status = {
                "zone_id": config["irrigation"]["zone_id"],
                "location": config["name"],
                "latitude": config["latitude"],
                "longitude": config["longitude"],
                "temperature": sensor.temperature(),
                "humidity": sensor.humidity(),
                "irrigation_active": config["irrigation"]["active"],
                "threshold": config["irrigation"]["threshold"]
            }
            status_data["zones"].append(zone_status)
            
        except Exception as e:
            print(f"❌ Error reading {location_id}: {e}")
    
    client.publish("system-status", ujson.dumps(status_data))

# Connect to WiFi
sta_if = network.WLAN(network.STA_IF)
sta_if.active(True)
sta_if.connect('Wokwi-GUEST', '')
while not sta_if.isconnected():
    time.sleep(0.1)

print("📶 Multi-Zone Irrigation System - WiFi Connected")

# Connect to MQTT
client = MQTTClient(MQTT_CLIENT_ID, MQTT_BROKER)
client.set_callback(on_message)
client.connect()
client.subscribe(MQTT_CONTROL_TOPIC)
print(f"📡 Connected to MQTT, subscribed to {MQTT_CONTROL_TOPIC}")

# Send initial system status
send_system_status()

# Main loop
message_counter = 0
last_auto_check = 0

while True:
    # Check for MQTT messages
    client.check_msg()
    
    current_time = time.ticks_ms()
    
    # Automatic irrigation check every 30 seconds
    if time.ticks_diff(current_time, last_auto_check) > 30000:
        check_automatic_irrigation()
        last_auto_check = current_time
    
    # Send sensor data every 10 seconds
    if message_counter % 10 == 0:
        for location_id, config in LOCATIONS.items():
            try:
                sensor = sensors[location_id]
                sensor.measure()
                
                sensor_data = {
                    "sensor_id": f"multi-sensor-{location_id}",
                    "sensor_type": "combined",
                    "temp": sensor.temperature(),
                    "humidity": sensor.humidity(),
                    "latitude": config["latitude"],
                    "longitude": config["longitude"],
                    "description": f"{config['name']} Multi-Zone Sensor",
                    "zone_id": config["irrigation"]["zone_id"],
                    "irrigation_active": config["irrigation"]["active"],
                    "irrigation_mode": irrigation_mode,
                    "humidity_threshold": config["irrigation"]["threshold"]
                }
                
                client.publish(MQTT_SENSOR_TOPIC, ujson.dumps(sensor_data))
                
                if message_counter % 50 == 0:  # Status every 50 iterations
                    irrigation_status = "ON" if config["irrigation"]["active"] else "OFF"
                    print(f"📊 {config['name']}: {sensor.temperature()}°C, {sensor.humidity()}%, Irrigation: {irrigation_status}")
                    
            except Exception as e:
                print(f"❌ Sensor error for {location_id}: {e}")
    
    message_counter += 1
    time.sleep(1)
