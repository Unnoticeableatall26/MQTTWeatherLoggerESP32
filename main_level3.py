import network
import time
from machine import Pin, PWM
import dht
import ujson
from umqtt.simple import MQTTClient

MQTT_CLIENT_ID = "micropython-weather-demo"
MQTT_BROKER    = "broker.mqttdashboard.com"
MQTT_SENSOR_TOPIC = "wokwi-weather"
MQTT_CONTROL_TOPIC = "irrigation-control"

# Sensor configuration
SENSOR_TYPE = "combined"
LATITUDE = 46.2044  # Geneva coordinates
LONGITUDE = 6.1432
DESCRIPTION = "Geneva Combined Sensor with Irrigation"

# Servo configuration
SERVO_PIN = 18
servo = PWM(Pin(SERVO_PIN), freq=50)

# Servo positions (in PWM duty cycle)
SERVO_CLOSED = 40   # 0 degrees - valve closed
SERVO_OPEN = 115    # 90 degrees - valve open

# Irrigation settings
irrigation_mode = "manual"  # "manual" or "auto"
humidity_threshold = 40  # Below this humidity, irrigation activates
irrigation_active = False
last_irrigation_check = 0

# DHT22 sensor
sensor = dht.DHT22(Pin(15))

def set_servo_position(position):
    """Set servo to specific position (SERVO_CLOSED or SERVO_OPEN)"""
    servo.duty(position)
    time.sleep(0.5)

def on_message(topic, msg):
    """Handle incoming MQTT control messages"""
    global irrigation_mode, humidity_threshold, irrigation_active
    
    try:
        data = ujson.loads(msg.decode())
        command = data.get("command")
        
        if command == "irrigation_on":
            irrigation_active = True
            set_servo_position(SERVO_OPEN)
            print("💧 Irrigation ON - Servo OPEN")
            
        elif command == "irrigation_off":
            irrigation_active = False
            set_servo_position(SERVO_CLOSED)
            print("🚫 Irrigation OFF - Servo CLOSED")
            
        elif command == "set_mode":
            irrigation_mode = data.get("mode", "manual")
            print(f"🔧 Mode changed to: {irrigation_mode}")
            
        elif command == "set_threshold":
            humidity_threshold = data.get("threshold", 40)
            print(f"📊 Humidity threshold set to: {humidity_threshold}%")
            
    except Exception as e:
        print(f"Error processing control message: {e}")

def check_automatic_irrigation(humidity):
    """Check if automatic irrigation should be triggered"""
    global irrigation_active, last_irrigation_check
    
    if irrigation_mode != "auto":
        return
    
    current_time = time.ticks_ms()
    
    # Check every 30 seconds to avoid rapid switching
    if time.ticks_diff(current_time, last_irrigation_check) < 30000:
        return
        
    last_irrigation_check = current_time
    
    if humidity < humidity_threshold and not irrigation_active:
        irrigation_active = True
        set_servo_position(SERVO_OPEN)
        print(f"🤖 AUTO: Humidity {humidity}% < {humidity_threshold}% - Irrigation ON")
        
        # Send notification
        notification = ujson.dumps({
            "sensor_id": MQTT_CLIENT_ID,
            "event": "auto_irrigation_started",
            "humidity": humidity,
            "threshold": humidity_threshold,
            "timestamp": time.time()
        })
        client.publish("irrigation-events", notification)
        
    elif humidity > humidity_threshold + 10 and irrigation_active:  # Hysteresis
        irrigation_active = False
        set_servo_position(SERVO_CLOSED)
        print(f"🤖 AUTO: Humidity {humidity}% > {humidity_threshold + 10}% - Irrigation OFF")
        
        # Send notification
        notification = ujson.dumps({
            "sensor_id": MQTT_CLIENT_ID,
            "event": "auto_irrigation_stopped", 
            "humidity": humidity,
            "threshold": humidity_threshold,
            "timestamp": time.time()
        })
        client.publish("irrigation-events", notification)

# Initialize servo to closed position
set_servo_position(SERVO_CLOSED)
print("🔧 Servo initialized - valve closed")

# Connect to WiFi
sta_if = network.WLAN(network.STA_IF)
sta_if.active(True)
sta_if.connect('Wokwi-GUEST', '')
while not sta_if.isconnected():
    time.sleep(0.1)

print("📶 WiFi connected")

# Connect to MQTT
client = MQTTClient(MQTT_CLIENT_ID, MQTT_BROKER)
client.set_callback(on_message)
client.connect()
client.subscribe(MQTT_CONTROL_TOPIC)
print(f"📡 MQTT connected, subscribed to {MQTT_CONTROL_TOPIC}")

prev_weather = ""
message_counter = 0

while True:
    # Check for incoming MQTT messages
    client.check_msg()
    
    # Read sensor data
    try:
        sensor.measure()
        temp = sensor.temperature()
        humidity = sensor.humidity()
        
        # Check automatic irrigation
        check_automatic_irrigation(humidity)
        
        # Prepare sensor message with irrigation status
        message = ujson.dumps({
            "sensor_id": MQTT_CLIENT_ID,
            "sensor_type": SENSOR_TYPE,
            "temp": temp,
            "humidity": humidity,
            "latitude": LATITUDE,
            "longitude": LONGITUDE,
            "description": DESCRIPTION,
            "irrigation_active": irrigation_active,
            "irrigation_mode": irrigation_mode,
            "humidity_threshold": humidity_threshold
        })
        
        # Send sensor data (every reading)
        if message != prev_weather:
            client.publish(MQTT_SENSOR_TOPIC, message)
            prev_weather = message
            message_counter += 1
            
            if message_counter % 10 == 0:  # Every 10th message
                print(f"📊 Temp: {temp}°C, Humidity: {humidity}%, Irrigation: {'ON' if irrigation_active else 'OFF'}, Mode: {irrigation_mode}")
                
    except Exception as e:
        print(f"Sensor error: {e}")
    
    time.sleep(1)
