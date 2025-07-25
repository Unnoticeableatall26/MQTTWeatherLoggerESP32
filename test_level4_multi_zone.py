"""
Test de vérification pour le Niveau 4 - Système Multi-Zones
Vérifie toutes les améliorations du système d'irrigation multi-zones

Auteur: HITEMA IoT Team
Date: Décembre 2024
Version: Level 4
"""

import time
import json
import sqlite3
import threading
import subprocess
import sys
from datetime import datetime
import paho.mqtt.client as mqtt

MQTT_BROKER = "broker.mqttdashboard.com"
MQTT_CONTROL_TOPIC = "irrigation-control"
MQTT_EVENTS_TOPIC = "irrigation-events"
MQTT_SENSOR_TOPIC = "wokwi-weather"

class Level4MultiZoneTest:
    def __init__(self):
        self.test_passed = 0
        self.test_failed = 0
        self.mqtt_messages = []
        self.irrigation_events = []
        self.sensor_data = []
        
        # Expected zones for Level 4
        self.expected_zones = {
            "zone_001": {
                "name": "Paris Garden",
                "location": "Paris",
                "coordinates": (48.8566, 2.3522),
                "pin_dht": 4,
                "pin_servo": 18
            },
            "zone_002": {
                "name": "Milan Greenhouse", 
                "location": "Milan",
                "coordinates": (45.4642, 9.1900),
                "pin_dht": 2,
                "pin_servo": 19
            },
            "zone_003": {
                "name": "Geneva Research Station",
                "location": "Geneva",
                "coordinates": (46.2044, 6.1432),
                "pin_dht": 15,
                "pin_servo": 21
            }
        }
        
        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1, "level4_test_client")
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        
    def on_connect(self, client, userdata, flags, rc):
        print(f"📡 Test client connected to MQTT broker (rc={rc})")
        client.subscribe(MQTT_EVENTS_TOPIC)
        client.subscribe(MQTT_SENSOR_TOPIC)
        
    def on_message(self, client, userdata, msg):
        try:
            data = json.loads(msg.payload.decode())
            data['timestamp'] = time.time()
            data['topic'] = msg.topic
            
            self.mqtt_messages.append(data)
            
            if msg.topic == MQTT_EVENTS_TOPIC:
                self.irrigation_events.append(data)
            elif msg.topic == MQTT_SENSOR_TOPIC:
                self.sensor_data.append(data)
                
        except Exception as e:
            print(f"❌ Error processing MQTT message: {e}")
    
    def print_test_header(self, test_name):
        print(f"\n{'='*60}")
        print(f"🧪 TEST: {test_name}")
        print(f"{'='*60}")
        
    def check_result(self, condition, test_description):
        if condition:
            print(f"✅ {test_description}")
            self.test_passed += 1
            return True
        else:
            print(f"❌ {test_description}")
            self.test_failed += 1
            return False
    
    def test_file_existence(self):
        """Test 1: Vérifier l'existence des fichiers Level 4"""
        self.print_test_header("Existence des fichiers Level 4")
        
        required_files = [
            "main_level4_multi_irrigation.py",
            "multi_zone_controller.py",
            "diagram.json",
            "app.py",
            "database.db"
        ]
        
        for file_name in required_files:
            try:
                with open(file_name, 'r', encoding='utf-8') as f:
                    content = f.read()
                self.check_result(len(content) > 0, f"Fichier {file_name} existe et n'est pas vide")
            except FileNotFoundError:
                self.check_result(False, f"Fichier {file_name} trouvé")
            except Exception as e:
                self.check_result(False, f"Erreur lors de la lecture de {file_name}: {e}")
    
    def test_multi_zone_configuration(self):
        """Test 2: Vérifier la configuration multi-zones"""
        self.print_test_header("Configuration Multi-Zones")
        
        try:
            with open("main_level4_multi_irrigation.py", 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Vérifier les configurations de zones
            for zone_id, zone_info in self.expected_zones.items():
                zone_found = zone_id in content
                self.check_result(zone_found, f"Zone {zone_id} ({zone_info['location']}) configurée")
                
                location_found = zone_info['location'] in content
                self.check_result(location_found, f"Location {zone_info['location']} trouvée")
                
                # Vérifier les coordonnées GPS
                lat_str = str(zone_info['coordinates'][0])
                lon_str = str(zone_info['coordinates'][1])
                coords_found = lat_str in content and lon_str in content
                self.check_result(coords_found, f"Coordonnées GPS pour {zone_info['location']} trouvées")
            
            # Vérifier les pins DHT et servo
            pin_configs = ["dht_pins", "servo_pins", "PWM"]
            for config in pin_configs:
                config_found = config in content
                self.check_result(config_found, f"Configuration {config} trouvée")
                
        except Exception as e:
            print(f"❌ Erreur lors du test de configuration: {e}")
    
    def test_mqtt_multi_zone_topics(self):
        """Test 3: Vérifier les topics MQTT multi-zones"""
        self.print_test_header("Topics MQTT Multi-Zones")
        
        # Start MQTT client
        self.client.connect(MQTT_BROKER, 1883, 60)
        self.client.loop_start()
        
        print("📡 Connexion au broker MQTT...")
        time.sleep(2)
        
        # Test zone-specific commands
        test_commands = [
            {"command": "irrigation_on", "zone_id": "zone_001"},
            {"command": "irrigation_off", "zone_id": "zone_002"},
            {"command": "set_threshold", "zone_id": "zone_003", "threshold": 45},
            {"command": "system_status", "zone_id": "all"}
        ]
        
        for cmd in test_commands:
            message = json.dumps(cmd)
            result = self.client.publish(MQTT_CONTROL_TOPIC, message)
            
            zone_desc = f"Zone {cmd['zone_id']}" if cmd['zone_id'] != "all" else "Toutes zones"
            self.check_result(result.rc == 0, f"Commande '{cmd['command']}' envoyée à {zone_desc}")
            time.sleep(0.5)
        
        self.client.loop_stop()
        self.client.disconnect()
    
    def test_database_multi_zone_schema(self):
        """Test 4: Vérifier le schéma base de données multi-zones"""
        self.print_test_header("Schéma Base de Données Multi-Zones")
        
        try:
            conn = sqlite3.connect('database.db')
            cursor = conn.cursor()
            
            # Vérifier la table sensor_data avec support multi-zones
            cursor.execute("PRAGMA table_info(sensor_data)")
            columns = [row[1] for row in cursor.fetchall()]
            
            required_columns = ['id', 'timestamp', 'temperature', 'humidity', 'zone_id', 'location']
            for col in required_columns:
                col_exists = col in columns
                self.check_result(col_exists, f"Colonne '{col}' dans table sensor_data")
            
            # Vérifier la table irrigation_events avec zones
            cursor.execute("PRAGMA table_info(irrigation_events)")
            columns = [row[1] for row in cursor.fetchall()]
            
            irrigation_columns = ['id', 'timestamp', 'event', 'zone_id', 'humidity', 'threshold']
            for col in irrigation_columns:
                col_exists = col in columns
                self.check_result(col_exists, f"Colonne '{col}' dans table irrigation_events")
            
            # Vérifier s'il y a des données multi-zones
            cursor.execute("SELECT DISTINCT zone_id FROM sensor_data WHERE zone_id IS NOT NULL")
            zones_in_db = [row[0] for row in cursor.fetchall()]
            
            zones_found = len(zones_in_db) > 0
            self.check_result(zones_found, f"Données multi-zones trouvées: {zones_in_db}")
            
            conn.close()
            
        except Exception as e:
            print(f"❌ Erreur lors du test base de données: {e}")
    
    def test_wokwi_multi_sensor_diagram(self):
        """Test 5: Vérifier le diagramme Wokwi multi-capteurs"""
        self.print_test_header("Diagramme Wokwi Multi-Capteurs")
        
        try:
            with open("diagram.json", 'r', encoding='utf-8') as f:
                diagram = json.load(f)
            
            parts = diagram.get('parts', [])
            connections = diagram.get('connections', [])
            
            # Vérifier les composants attendus
            expected_components = {
                'esp32': 1,
                'dht22': 3,  # 3 DHT22 pour 3 zones
                'servo': 3   # 3 servos pour 3 zones
            }
            
            for part_type, expected_count in expected_components.items():
                actual_count = sum(1 for part in parts if part_type in part.get('type', ''))
                self.check_result(
                    actual_count >= expected_count,
                    f"Au moins {expected_count} composant(s) {part_type} trouvé(s) ({actual_count})"
                )
            
            # Vérifier les connexions multiples
            connection_count = len(connections)
            min_expected_connections = 20  # ESP32 + 3 DHT22 + 3 servos = nombreuses connexions
            self.check_result(
                connection_count >= min_expected_connections,
                f"Connexions suffisantes trouvées ({connection_count}/{min_expected_connections})"
            )
            
            # Vérifier les pins spécifiques
            connection_str = str(connections)
            expected_pins = ["18", "19", "21", "4", "2", "15"]  # Servo et DHT pins
            for pin in expected_pins:
                pin_found = f":{pin}" in connection_str or f"D{pin}" in connection_str
                self.check_result(pin_found, f"Pin {pin} utilisée dans les connexions")
                
        except Exception as e:
            print(f"❌ Erreur lors du test diagramme: {e}")
    
    def test_controller_multi_zone_features(self):
        """Test 6: Vérifier les fonctionnalités du contrôleur multi-zones"""
        self.print_test_header("Fonctionnalités Contrôleur Multi-Zones")
        
        try:
            with open("multi_zone_controller.py", 'r', encoding='utf-8') as f:
                controller_content = f.read()
            
            # Vérifier les fonctionnalités multi-zones
            multi_zone_features = [
                "MultiZoneIrrigationController",
                "zone_001",
                "zone_002", 
                "zone_003",
                "Paris",
                "Milan",
                "Geneva",
                "turn_on_zone",
                "turn_off_zone",
                "set_zone_threshold",
                "show_zone_status",
                "LOCATIONS" # Pour vérifier la compatibilité avec ESP32
            ]
            
            for feature in multi_zone_features:
                feature_found = feature in controller_content
                self.check_result(feature_found, f"Fonctionnalité '{feature}' implémentée")
            
            # Vérifier les coordonnées GPS des zones
            gps_coordinates = ["48.8566", "45.4642", "46.2044"]  # Paris, Milan, Geneva
            for coord in gps_coordinates:
                coord_found = coord in controller_content
                self.check_result(coord_found, f"Coordonnée GPS {coord} trouvée")
                
        except Exception as e:
            print(f"❌ Erreur lors du test contrôleur: {e}")
    
    def test_level4_improvements(self):
        """Test 7: Vérifier les améliorations spécifiques au Level 4"""
        self.print_test_header("Améliorations Level 4")
        
        improvements_found = {
            "multi_zone": False,
            "gps_coordinates": False,
            "zone_specific_thresholds": False,
            "individual_servo_control": False,
            "enhanced_mqtt": False
        }
        
        # Vérifier main_level4_multi_irrigation.py
        try:
            with open("main_level4_multi_irrigation.py", 'r', encoding='utf-8') as f:
                main_content = f.read()
            
            if "LOCATIONS" in main_content and len([line for line in main_content.split('\n') if 'zone_' in line]) >= 3:
                improvements_found["multi_zone"] = True
            
            if "latitude" in main_content and "longitude" in main_content:
                improvements_found["gps_coordinates"] = True
            
            if "threshold" in main_content and "zone_" in main_content:
                improvements_found["zone_specific_thresholds"] = True
            
            if "servo_pins" in main_content and "PWM" in main_content:
                improvements_found["individual_servo_control"] = True
            
            if "zone_id" in main_content and "MQTT" in main_content:
                improvements_found["enhanced_mqtt"] = True
                
        except Exception as e:
            print(f"❌ Erreur lors de la vérification des améliorations: {e}")
        
        # Vérifier les résultats
        for improvement, found in improvements_found.items():
            self.check_result(found, f"Amélioration Level 4: {improvement.replace('_', ' ').title()}")
    
    def run_comprehensive_test(self):
        """Exécuter tous les tests Level 4"""
        print("🌍 TESTS DE VÉRIFICATION LEVEL 4 - SYSTÈME MULTI-ZONES")
        print("="*70)
        print("Vérification des améliorations et fonctionnalités multi-zones")
        print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*70)
        
        # Exécuter tous les tests
        self.test_file_existence()
        self.test_multi_zone_configuration()
        self.test_mqtt_multi_zone_topics()
        self.test_database_multi_zone_schema()
        self.test_wokwi_multi_sensor_diagram()
        self.test_controller_multi_zone_features()
        self.test_level4_improvements()
        
        # Résumé final
        total_tests = self.test_passed + self.test_failed
        success_rate = (self.test_passed / total_tests * 100) if total_tests > 0 else 0
        
        print(f"\n{'='*70}")
        print("🏆 RÉSUMÉ DES TESTS LEVEL 4")
        print(f"{'='*70}")
        print(f"✅ Tests réussis: {self.test_passed}")
        print(f"❌ Tests échoués: {self.test_failed}")
        print(f"📊 Taux de réussite: {success_rate:.1f}%")
        
        if success_rate >= 90:
            print("🎉 EXCELLENT! Level 4 Multi-Zones prêt pour production!")
        elif success_rate >= 75:
            print("✅ BIEN! Level 4 fonctionnel avec quelques améliorations possibles")
        elif success_rate >= 50:
            print("⚠️  MOYEN. Plusieurs points à corriger")
        else:
            print("❌ ATTENTION! Corrections importantes nécessaires")
        
        # Recommandations Level 4
        print(f"\n📋 RECOMMANDATIONS LEVEL 4:")
        print("1. Vérifier les 3 zones (Paris, Milan, Geneva) configurées")
        print("2. Tester l'irrigation individuelle par zone")
        print("3. Valider les coordonnées GPS de chaque zone")
        print("4. Vérifier les seuils d'humidité spécifiques par zone")
        print("5. Tester les commandes MQTT zone-spécifiques")
        print("6. Préparer pour les améliorations additionnelles:")
        print("   - Détection d'intrusion avec OpenCV")
        print("   - Classification des maladies des plantes")
        print("   - Intégration ESP32 physique")
        
        print(f"\n{'='*70}")
        return success_rate >= 75

if __name__ == "__main__":
    print("🧪 Lancement des tests Level 4 Multi-Zones...")
    test_suite = Level4MultiZoneTest()
    success = test_suite.run_comprehensive_test()
    
    if success:
        print("\n🎯 Level 4 Multi-Zones validé! Prêt pour les améliorations avancées.")
    else:
        print("\n⚠️ Quelques ajustements nécessaires avant finalisation.")
    
    sys.exit(0 if success else 1)
