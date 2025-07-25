import paho.mqtt.client as mqtt
import json
import time
import threading
from datetime import datetime

MQTT_BROKER = "broker.mqttdashboard.com"
MQTT_CONTROL_TOPIC = "irrigation-control"
MQTT_EVENTS_TOPIC = "irrigation-events"
MQTT_SENSOR_TOPIC = "wokwi-weather"

class IrrigationController:
    def __init__(self):
        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1, "irrigation_controller")
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        
        # Irrigation settings
        self.sensors_with_irrigation = ["micropython-weather-demo"]
        self.irrigation_schedules = {}
        self.last_sensor_data = {}
        
        # Auto-irrigation settings
        self.auto_irrigation_enabled = True
        self.global_humidity_threshold = 35
        self.check_interval = 30  # seconds
        
    def on_connect(self, client, userdata, flags, rc):
        print(f"🔗 Irrigation Controller connected with result code {rc}")
        client.subscribe(MQTT_EVENTS_TOPIC)
        client.subscribe(MQTT_SENSOR_TOPIC)
        print(f"📡 Subscribed to {MQTT_EVENTS_TOPIC} and {MQTT_SENSOR_TOPIC}")
        
    def on_message(self, client, userdata, msg):
        try:
            topic = msg.topic
            data = json.loads(msg.payload.decode())
            
            if topic == MQTT_EVENTS_TOPIC:
                self.handle_irrigation_event(data)
            elif topic == MQTT_SENSOR_TOPIC:
                self.handle_sensor_data(data)
                
        except Exception as e:
            print(f"❌ Error processing message: {e}")
    
    def handle_irrigation_event(self, data):
        """Handle irrigation events from ESP32"""
        sensor_id = data.get("sensor_id")
        event = data.get("event")
        humidity = data.get("humidity")
        
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        if event == "auto_irrigation_started":
            print(f"🌿 [{timestamp}] AUTO IRRIGATION STARTED for {sensor_id}")
            print(f"   💧 Humidity: {humidity}% (below threshold)")
            
        elif event == "auto_irrigation_stopped":
            print(f"🛑 [{timestamp}] AUTO IRRIGATION STOPPED for {sensor_id}")
            print(f"   ✅ Humidity: {humidity}% (above threshold)")
    
    def handle_sensor_data(self, data):
        """Process incoming sensor data and trigger irrigation if needed"""
        sensor_id = data.get("sensor_id")
        
        if sensor_id in self.sensors_with_irrigation:
            self.last_sensor_data[sensor_id] = data
            
            # Check if we need to trigger irrigation from controller side
            humidity = data.get("humidity")
            if humidity and self.auto_irrigation_enabled:
                self.check_humidity_threshold(sensor_id, humidity)
    
    def check_humidity_threshold(self, sensor_id, humidity):
        """Check if humidity requires intervention"""
        if humidity < self.global_humidity_threshold - 5:  # Emergency low humidity
            print(f"🚨 EMERGENCY: {sensor_id} humidity at {humidity}% - Very low!")
            # Could send emergency irrigation command here
    
    def send_irrigation_command(self, sensor_id, command, **kwargs):
        """Send irrigation control command to specific sensor"""
        message = {
            "command": command,
            "sensor_id": sensor_id,
            "timestamp": time.time()
        }
        message.update(kwargs)
        
        self.client.publish(MQTT_CONTROL_TOPIC, json.dumps(message))
        
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"📤 [{timestamp}] Sent command '{command}' to {sensor_id}")
        
        if kwargs:
            for key, value in kwargs.items():
                print(f"   {key}: {value}")
    
    def irrigation_on(self, sensor_id="micropython-weather-demo"):
        """Turn irrigation ON manually"""
        self.send_irrigation_command(sensor_id, "irrigation_on")
    
    def irrigation_off(self, sensor_id="micropython-weather-demo"):
        """Turn irrigation OFF manually"""
        self.send_irrigation_command(sensor_id, "irrigation_off")
    
    def set_auto_mode(self, sensor_id="micropython-weather-demo"):
        """Set irrigation to automatic mode"""
        self.send_irrigation_command(sensor_id, "set_mode", mode="auto")
    
    def set_manual_mode(self, sensor_id="micropython-weather-demo"):
        """Set irrigation to manual mode"""
        self.send_irrigation_command(sensor_id, "set_mode", mode="manual")
    
    def set_humidity_threshold(self, threshold, sensor_id="micropython-weather-demo"):
        """Set humidity threshold for automatic irrigation"""
        self.send_irrigation_command(sensor_id, "set_threshold", threshold=threshold)
        self.global_humidity_threshold = threshold
    
    def status(self):
        """Print current status"""
        print("\n" + "="*50)
        print("🌿 IRRIGATION SYSTEM STATUS")
        print("="*50)
        print(f"Auto irrigation: {'✅ Enabled' if self.auto_irrigation_enabled else '❌ Disabled'}")
        print(f"Global humidity threshold: {self.global_humidity_threshold}%")
        print(f"Sensors with irrigation: {len(self.sensors_with_irrigation)}")
        
        for sensor_id in self.sensors_with_irrigation:
            if sensor_id in self.last_sensor_data:
                data = self.last_sensor_data[sensor_id]
                humidity = data.get("humidity", "N/A")
                irrigation_active = data.get("irrigation_active", False)
                irrigation_mode = data.get("irrigation_mode", "unknown")
                
                print(f"\n📊 {sensor_id}:")
                print(f"   Humidity: {humidity}%")
                print(f"   Irrigation: {'🟢 ON' if irrigation_active else '🔴 OFF'}")
                print(f"   Mode: {irrigation_mode}")
        print("="*50)
    
    def interactive_menu(self):
        """Interactive control menu"""
        while True:
            print("\n🌿 IRRIGATION CONTROL MENU")
            print("1. Turn irrigation ON")
            print("2. Turn irrigation OFF") 
            print("3. Set AUTO mode")
            print("4. Set MANUAL mode")
            print("5. Set humidity threshold")
            print("6. Show status")
            print("7. Exit")
            
            try:
                choice = input("\nEnter choice (1-7): ").strip()
                
                if choice == "1":
                    self.irrigation_on()
                elif choice == "2":
                    self.irrigation_off()
                elif choice == "3":
                    self.set_auto_mode()
                elif choice == "4":
                    self.set_manual_mode()
                elif choice == "5":
                    threshold = float(input("Enter humidity threshold (0-100): "))
                    self.set_humidity_threshold(threshold)
                elif choice == "6":
                    self.status()
                elif choice == "7":
                    print("👋 Exiting irrigation controller...")
                    break
                else:
                    print("❌ Invalid choice, please try again")
                    
            except KeyboardInterrupt:
                print("\n👋 Exiting irrigation controller...")
                break
            except Exception as e:
                print(f"❌ Error: {e}")
    
    def start(self):
        """Start the irrigation controller"""
        self.client.connect(MQTT_BROKER, 1883, 60)
        self.client.loop_start()
        
        print("🌿 Irrigation Controller started!")
        print("   Monitoring sensor data and irrigation events...")
        print("   Use interactive menu for manual control\n")
        
        # Start interactive menu
        self.interactive_menu()
        
        self.client.loop_stop()
        self.client.disconnect()

if __name__ == "__main__":
    controller = IrrigationController()
    controller.start()
