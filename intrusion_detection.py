"""
Level 4+ Amélioration: Système de Détection d'Intrusion avec OpenCV
Ajoute la détection de personnes dans les zones d'irrigation

Auteur: HITEMA IoT Team
Date: Décembre 2024
Version: Level 4+ Intrusion Detection
"""

import cv2
import json
import time
import paho.mqtt.client as mqtt
import threading
from datetime import datetime
import numpy as np

MQTT_BROKER = "broker.mqttdashboard.com" 
MQTT_INTRUSION_TOPIC = "security-alerts"
MQTT_CONTROL_TOPIC = "irrigation-control"

class IntrusionDetectionSystem:
    def __init__(self):
        # Configuration des zones de surveillance
        self.zones = {
            "zone_001": {
                "name": "Paris Garden",
                "location": "Paris",
                "coordinates": (48.8566, 2.3522),
                "camera_id": 0,  # Webcam principale
                "detection_active": True
            },
            "zone_002": {
                "name": "Milan Greenhouse", 
                "location": "Milan",
                "coordinates": (45.4642, 9.1900),
                "camera_id": 1,  # Caméra secondaire (si disponible)
                "detection_active": False  # Simulé pour demo
            },
            "zone_003": {
                "name": "Geneva Research Station",
                "location": "Geneva",
                "coordinates": (46.2044, 6.1432),
                "camera_id": 2,  # Caméra tertiaire (si disponible)
                "detection_active": False  # Simulé pour demo
            }
        }
        
        # Initialisation OpenCV pour détection de personnes
        self.hog = cv2.HOGDescriptor()
        self.hog.setSVMDetector(cv2.HOGDescriptor_getDefaultPeopleDetector())
        
        # MQTT client pour alertes
        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1, "intrusion_detector")
        self.client.on_connect = self.on_connect
        
        # Variables de contrôle
        self.detection_running = False
        self.last_detection = {}
        self.detection_cooldown = 10  # 10 secondes entre détections
        
    def on_connect(self, client, userdata, flags, rc):
        print(f"🔐 Système de détection connecté au MQTT (rc={rc})")
    
    def detect_intrusion_camera(self, zone_id):
        """Détection d'intrusion par caméra pour une zone"""
        zone = self.zones[zone_id]
        camera_id = zone["camera_id"]
        
        print(f"📹 Démarrage détection caméra pour {zone['name']} (Zone {zone_id})")
        
        try:
            cap = cv2.VideoCapture(camera_id)
            
            if not cap.isOpened():
                print(f"❌ Impossible d'ouvrir la caméra {camera_id} pour {zone['name']}")
                return
            
            print(f"✅ Caméra {camera_id} ouverte pour surveillance de {zone['name']}")
            print("   Appuyez sur 'q' pour arrêter la surveillance")
            
            while self.detection_running:
                ret, frame = cap.read()
                if not ret:
                    print("❌ Erreur lecture caméra")
                    break
                
                # Détection de personnes avec HOG
                boxes, weights = self.hog.detectMultiScale(frame, winStride=(8,8))
                
                current_time = time.time()
                persons_detected = len(boxes)
                
                # Si des personnes sont détectées
                if persons_detected > 0:
                    # Vérifier le cooldown
                    last_alert = self.last_detection.get(zone_id, 0)
                    if current_time - last_alert > self.detection_cooldown:
                        
                        # Envoyer alerte MQTT
                        self.send_intrusion_alert(zone_id, persons_detected, zone['coordinates'])
                        self.last_detection[zone_id] = current_time
                        
                        # Actions de sécurité
                        self.security_response(zone_id)
                
                # Dessiner les rectangles de détection
                for (x, y, w, h) in boxes:
                    cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
                
                # Afficher informations sur l'image
                info_text = f"{zone['name']} - Personnes: {persons_detected}"
                cv2.putText(frame, info_text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
                
                timestamp = datetime.now().strftime("%H:%M:%S")
                cv2.putText(frame, timestamp, (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
                
                # Afficher le feed
                cv2.imshow(f"Surveillance {zone['name']}", frame)
                
                # Contrôles clavier
                key = cv2.waitKey(1) & 0xFF
                if key == ord('q'):
                    print(f"🛑 Arrêt surveillance {zone['name']}")
                    break
                elif key == ord('s'):
                    # Sauvegarder screenshot
                    filename = f"intrusion_{zone_id}_{int(current_time)}.jpg"
                    cv2.imwrite(filename, frame)
                    print(f"📸 Screenshot sauvé: {filename}")
            
            cap.release()
            cv2.destroyAllWindows()
            
        except Exception as e:
            print(f"❌ Erreur détection caméra {zone['name']}: {e}")
    
    def send_intrusion_alert(self, zone_id, person_count, coordinates):
        """Envoyer alerte d'intrusion via MQTT"""
        alert_data = {
            "alert_type": "intrusion_detected",
            "zone_id": zone_id,
            "zone_name": self.zones[zone_id]["name"],
            "location": self.zones[zone_id]["location"],
            "coordinates": {
                "latitude": coordinates[0],
                "longitude": coordinates[1]
            },
            "person_count": person_count,
            "timestamp": time.time(),
            "severity": "HIGH" if person_count > 2 else "MEDIUM"
        }
        
        message = json.dumps(alert_data)
        result = self.client.publish(MQTT_INTRUSION_TOPIC, message)
        
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"🚨 [{timestamp}] ALERTE INTRUSION!")
        print(f"   Zone: {self.zones[zone_id]['name']}")
        print(f"   Personnes détectées: {person_count}")
        print(f"   Coordonnées: {coordinates}")
        print(f"   Sévérité: {alert_data['severity']}")
    
    def security_response(self, zone_id):
        """Actions de sécurité automatiques"""
        # Arrêter l'irrigation de la zone compromise
        security_command = {
            "command": "emergency_stop",
            "zone_id": zone_id,
            "reason": "intrusion_detected",
            "timestamp": time.time()
        }
        
        self.client.publish(MQTT_CONTROL_TOPIC, json.dumps(security_command))
        print(f"🛑 Irrigation d'urgence arrêtée pour Zone {zone_id}")
        
        # Log de sécurité
        with open("security_log.txt", "a") as log_file:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            log_entry = f"[{timestamp}] INTRUSION DETECTED - Zone {zone_id} ({self.zones[zone_id]['name']})\n"
            log_file.write(log_entry)
    
    def simulate_detection_other_zones(self):
        """Simuler la détection pour les zones sans caméra"""
        while self.detection_running:
            time.sleep(30)  # Vérification toutes les 30 secondes
            
            for zone_id, zone in self.zones.items():
                if zone_id != "zone_001" and zone["detection_active"]:
                    # Simulation aléatoire (5% de chance de détection)
                    import random
                    if random.random() < 0.05:
                        person_count = random.randint(1, 3)
                        self.send_intrusion_alert(zone_id, person_count, zone["coordinates"])
                        self.security_response(zone_id)
    
    def start_detection_system(self):
        """Démarrer le système complet de détection"""
        print("🔐 SYSTÈME DE DÉTECTION D'INTRUSION LEVEL 4+")
        print("="*55)
        print("🎯 Zones surveillées:")
        for zone_id, zone in self.zones.items():
            status = "🟢 ACTIVE" if zone["detection_active"] else "🔴 SIMULÉE"
            print(f"   📍 {zone['name']} ({zone_id}) - {status}")
        
        print("\n🚀 Démarrage du système...")
        
        # Connexion MQTT
        self.client.connect(MQTT_BROKER, 1883, 60)
        self.client.loop_start()
        
        self.detection_running = True
        
        # Thread pour surveillance caméra principale (Paris)
        camera_thread = threading.Thread(
            target=self.detect_intrusion_camera, 
            args=("zone_001",),
            daemon=True
        )
        camera_thread.start()
        
        # Thread pour simulation autres zones
        simulation_thread = threading.Thread(
            target=self.simulate_detection_other_zones,
            daemon=True
        )
        simulation_thread.start()
        
        print("✅ Système de détection actif!")
        print("📹 Surveillance caméra: Zone Paris")
        print("🤖 Simulation: Zones Milan & Geneva")
        print("⚠️  Les alertes sont envoyées via MQTT")
        print("\nCommandes:")
        print("   - 'q' dans la fenêtre caméra pour arrêter")
        print("   - 's' dans la fenêtre caméra pour screenshot")
        print("   - Ctrl+C pour arrêt d'urgence")
        
        try:
            # Garder le système actif
            camera_thread.join()
        except KeyboardInterrupt:
            print("\n🛑 Arrêt du système de détection...")
        finally:
            self.detection_running = False
            self.client.loop_stop()
            self.client.disconnect()
            cv2.destroyAllWindows()

def install_opencv_if_needed():
    """Installer OpenCV si nécessaire"""
    try:
        import cv2
        print("✅ OpenCV disponible")
        return True
    except ImportError:
        print("❌ OpenCV non installé")
        print("💾 Installation recommandée:")
        print("   pip install opencv-python")
        return False

def main():
    print("🔐 Initialisation du système de détection d'intrusion...")
    
    if not install_opencv_if_needed():
        print("⚠️  OpenCV requis pour la détection d'intrusion")
        return
    
    print("🎮 Options:")
    print("1. 🚀 Lancer détection complète (avec caméra)")
    print("2. 🧪 Mode test (simulation uniquement)")
    print("3. ❌ Annuler")
    
    choice = input("\nChoisissez une option (1-3): ").strip()
    
    if choice == "1":
        print("🚀 Lancement du système complet...")
        detector = IntrusionDetectionSystem()
        detector.start_detection_system()
        
    elif choice == "2":
        print("🧪 Mode test activé...")
        detector = IntrusionDetectionSystem()
        # Désactiver caméra pour test
        detector.zones["zone_001"]["detection_active"] = False
        detector.zones["zone_002"]["detection_active"] = True
        detector.zones["zone_003"]["detection_active"] = True
        
        detector.client.connect(MQTT_BROKER, 1883, 60)
        detector.client.loop_start()
        
        # Simuler quelques détections
        for i in range(3):
            detector.send_intrusion_alert("zone_002", 2, (45.4642, 9.1900))
            time.sleep(2)
            detector.send_intrusion_alert("zone_003", 1, (46.2044, 6.1432))
            time.sleep(3)
        
        print("✅ Tests terminés!")
        detector.client.loop_stop()
        detector.client.disconnect()
        
    else:
        print("👋 Annulation...")

if __name__ == "__main__":
    main()
