import paho.mqtt.client as mqtt
import json
import time
import threading
from datetime import datetime
import sqlite3

MQTT_BROKER = "broker.mqttdashboard.com"
MQTT_CONTROL_TOPIC = "irrigation-control"
MQTT_EVENTS_TOPIC = "irrigation-events"
MQTT_SENSOR_TOPIC = "wokwi-weather"
MQTT_STATUS_TOPIC = "system-status"

class MultiZoneIrrigationController:
    def __init__(self):
        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1, "multi_zone_controller")
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        
        # Zone configuration matching ESP32 setup
        self.zones = {
            "zone_001": {
                "name": "Paris Garden",
                "location": "Paris",
                "latitude": 48.8566,
                "longitude": 2.3522,
                "status": "OFF",
                "threshold": 35,
                "last_humidity": None
            },
            "zone_002": {
                "name": "Milan Greenhouse", 
                "location": "Milan",
                "latitude": 45.4642,
                "longitude": 9.1900,
                "status": "OFF",
                "threshold": 40,
                "last_humidity": None
            },
            "zone_003": {
                "name": "Geneva Research Station",
                "location": "Geneva", 
                "latitude": 46.2044,
                "longitude": 6.1432,
                "status": "OFF",
                "threshold": 38,
                "last_humidity": None
            }
        }
        
        self.system_mode = "auto"
        self.system_active = True
        
    def on_connect(self, client, userdata, flags, rc):
        print(f"🌍 Multi-Zone Controller connected with result code {rc}")
        client.subscribe(MQTT_EVENTS_TOPIC)
        client.subscribe(MQTT_SENSOR_TOPIC)
        client.subscribe(MQTT_STATUS_TOPIC)
        print(f"📡 Subscribed to irrigation events, sensor data, and system status")
        
    def on_message(self, client, userdata, msg):
        try:
            topic = msg.topic
            data = json.loads(msg.payload.decode())
            
            if topic == MQTT_EVENTS_TOPIC:
                self.handle_irrigation_event(data)
            elif topic == MQTT_SENSOR_TOPIC:
                self.handle_sensor_data(data)
            elif topic == MQTT_STATUS_TOPIC:
                self.handle_system_status(data)
                
        except Exception as e:
            print(f"❌ Error processing message: {e}")
    
    def handle_irrigation_event(self, data):
        """Handle irrigation events from multi-zone system"""
        zone_id = data.get("zone_id")
        event = data.get("event", "")
        location = data.get("location", "Unknown")
        humidity = data.get("humidity")
        
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        if "start" in event:
            if zone_id in self.zones:
                self.zones[zone_id]["status"] = "ON"
            print(f"💧 [{timestamp}] {location} (Zone {zone_id}) irrigation STARTED")
            print(f"   Humidity: {humidity}% (below threshold)")
            
        elif "stop" in event:
            if zone_id in self.zones:
                self.zones[zone_id]["status"] = "OFF"
            print(f"🛑 [{timestamp}] {location} (Zone {zone_id}) irrigation STOPPED")
            print(f"   Humidity: {humidity}% (above threshold)")
    
    def handle_sensor_data(self, data):
        """Process sensor data from multi-zone system"""
        sensor_id = data.get("sensor_id", "")
        zone_id = data.get("zone_id")
        humidity = data.get("humidity")
        
        if zone_id and zone_id in self.zones:
            self.zones[zone_id]["last_humidity"] = humidity
            irrigation_active = data.get("irrigation_active", False)
            self.zones[zone_id]["status"] = "ON" if irrigation_active else "OFF"
    
    def handle_system_status(self, data):
        """Handle complete system status updates"""
        zones_data = data.get("zones", [])
        self.system_mode = data.get("mode", "auto")
        
        for zone_data in zones_data:
            zone_id = zone_data.get("zone_id")
            if zone_id in self.zones:
                self.zones[zone_id]["last_humidity"] = zone_data.get("humidity")
                self.zones[zone_id]["status"] = "ON" if zone_data.get("irrigation_active") else "OFF"
                self.zones[zone_id]["threshold"] = zone_data.get("threshold", 40)
    
    def send_zone_command(self, command, zone_id="all", **kwargs):
        """Send command to specific zone or all zones"""
        message = {
            "command": command,
            "zone_id": zone_id,
            "timestamp": time.time()
        }
        message.update(kwargs)
        
        self.client.publish(MQTT_CONTROL_TOPIC, json.dumps(message))
        
        timestamp = datetime.now().strftime("%H:%M:%S")
        zone_name = self.zones.get(zone_id, {}).get("name", zone_id) if zone_id != "all" else "ALL ZONES"
        print(f"📤 [{timestamp}] Command '{command}' sent to {zone_name}")
        
        if kwargs:
            for key, value in kwargs.items():
                print(f"   {key}: {value}")
    
    def turn_on_zone(self, zone_id):
        """Turn on irrigation for specific zone"""
        self.send_zone_command("irrigation_on", zone_id)
    
    def turn_off_zone(self, zone_id):
        """Turn off irrigation for specific zone"""
        self.send_zone_command("irrigation_off", zone_id)
    
    def turn_on_all_zones(self):
        """Turn on irrigation for all zones"""
        self.send_zone_command("irrigation_on", "all")
    
    def turn_off_all_zones(self):
        """Turn off irrigation for all zones"""
        self.send_zone_command("irrigation_off", "all")
    
    def set_zone_threshold(self, zone_id, threshold):
        """Set humidity threshold for specific zone"""
        self.send_zone_command("set_threshold", zone_id, threshold=threshold)
    
    def set_system_mode(self, mode):
        """Set system mode (auto/manual)"""
        self.send_zone_command("set_mode", "all", mode=mode)
    
    def request_system_status(self):
        """Request current system status"""
        self.send_zone_command("system_status", "all")
    
    def show_zone_status(self):
        """Display current status of all zones"""
        print("\n" + "="*70)
        print("🌍 MULTI-ZONE IRRIGATION SYSTEM STATUS")
        print("="*70)
        print(f"System Mode: {self.system_mode.upper()}")
        print(f"System Active: {'✅ YES' if self.system_active else '❌ NO'}")
        print(f"Total Zones: {len(self.zones)}")
        
        for zone_id, zone_info in self.zones.items():
            status_emoji = "💧" if zone_info["status"] == "ON" else "🏜️"
            humidity_str = f"{zone_info['last_humidity']}%" if zone_info['last_humidity'] else "N/A"
            
            print(f"\n📍 {zone_info['name']} ({zone_id})")
            print(f"   Location: {zone_info['location']} ({zone_info['latitude']}, {zone_info['longitude']})")
            print(f"   Status: {status_emoji} {zone_info['status']}")
            print(f"   Humidity: {humidity_str}")
            print(f"   Threshold: {zone_info['threshold']}%")
        
        print("="*70)
    
    def interactive_menu(self):
        """Interactive control menu for multi-zone system"""
        while True:
            print("\n🌍 MULTI-ZONE IRRIGATION CONTROL MENU")
            print("="*50)
            print("1. Turn ON specific zone")
            print("2. Turn OFF specific zone") 
            print("3. Turn ON all zones")
            print("4. Turn OFF all zones")
            print("5. Set zone threshold")
            print("6. Set system mode (auto/manual)")
            print("7. Show zone status")
            print("8. Request system status update")
            print("9. Exit")
            
            try:
                choice = input("\nEnter choice (1-9): ").strip()
                
                if choice == "1":
                    self.show_zones()
                    zone_id = input("Enter zone ID: ").strip()
                    if zone_id in self.zones:
                        self.turn_on_zone(zone_id)
                    else:
                        print("❌ Invalid zone ID")
                        
                elif choice == "2":
                    self.show_zones()
                    zone_id = input("Enter zone ID: ").strip()
                    if zone_id in self.zones:
                        self.turn_off_zone(zone_id)
                    else:
                        print("❌ Invalid zone ID")
                        
                elif choice == "3":
                    self.turn_on_all_zones()
                    
                elif choice == "4":
                    self.turn_off_all_zones()
                    
                elif choice == "5":
                    self.show_zones()
                    zone_id = input("Enter zone ID (or 'all' for all zones): ").strip()
                    threshold = float(input("Enter humidity threshold (0-100): "))
                    if zone_id == "all":
                        for zid in self.zones.keys():
                            self.set_zone_threshold(zid, threshold)
                    elif zone_id in self.zones:
                        self.set_zone_threshold(zone_id, threshold)
                    else:
                        print("❌ Invalid zone ID")
                        
                elif choice == "6":
                    mode = input("Enter mode (auto/manual): ").strip().lower()
                    if mode in ["auto", "manual"]:
                        self.set_system_mode(mode)
                    else:
                        print("❌ Invalid mode. Use 'auto' or 'manual'")
                        
                elif choice == "7":
                    self.show_zone_status()
                    
                elif choice == "8":
                    self.request_system_status()
                    print("📡 Status update requested...")
                    
                elif choice == "9":
                    print("👋 Exiting multi-zone controller...")
                    break
                    
                else:
                    print("❌ Invalid choice, please try again")
                    
            except KeyboardInterrupt:
                print("\n👋 Exiting multi-zone controller...")
                break
            except Exception as e:
                print(f"❌ Error: {e}")
    
    def show_zones(self):
        """Display available zones"""
        print("\nAvailable Zones:")
        for zone_id, zone_info in self.zones.items():
            print(f"  {zone_id}: {zone_info['name']} ({zone_info['location']})")
    
    def start(self):
        """Start the multi-zone irrigation controller"""
        self.client.connect(MQTT_BROKER, 1883, 60)
        self.client.loop_start()
        
        print("🌍 Multi-Zone Irrigation Controller started!")
        print("   Monitoring multi-zone irrigation system...")
        print("   Use interactive menu for zone control\n")
        
        # Request initial status
        time.sleep(2)
        self.request_system_status()
        
        # Start interactive menu
        self.interactive_menu()
        
        self.client.loop_stop()
        self.client.disconnect()

if __name__ == "__main__":
    controller = MultiZoneIrrigationController()
    controller.start()
