"""
Démonstration Level 4 - Système Multi-Zones en Action
Lance le système complet et montre les fonctionnalités multi-zones

Auteur: HITEMA IoT Team
Date: Décembre 2024
Version: Level 4 Multi-Zone Demo
"""

import threading
import time
import json
import subprocess
import sys
from datetime import datetime
import paho.mqtt.client as mqtt

MQTT_BROKER = "broker.mqttdashboard.com"
MQTT_CONTROL_TOPIC = "irrigation-control"

class Level4Demo:
    def __init__(self):
        self.demo_active = True
        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1, "level4_demo")
        
    def print_banner(self):
        print("🌍" + "="*68 + "🌍")
        print("🎯 DÉMONSTRATION LEVEL 4 - SYSTÈME MULTI-ZONES")
        print("🌍" + "="*68 + "🌍")
        print("📍 Zones configurées:")
        print("   🇫🇷 Zone 001: Paris Garden (48.8566, 2.3522)")
        print("   🇮🇹 Zone 002: Milan Greenhouse (45.4642, 9.1900)")
        print("   🇨🇭 Zone 003: Geneva Research Station (46.2044, 6.1432)")
        print("\n🚀 Fonctionnalités Level 4:")
        print("   ✅ Irrigation multi-zones avec contrôle individuel")
        print("   ✅ Coordonnées GPS par zone")
        print("   ✅ Seuils d'humidité spécifiques par zone")
        print("   ✅ Servos multiples (pins 18, 19, 21)")
        print("   ✅ Capteurs DHT22 multiples (pins 4, 2, 15)")
        print("   ✅ Commandes MQTT zone-spécifiques")
        print("   ✅ Dashboard multi-zones")
        print("🌍" + "="*68 + "🌍\n")
    
    def send_demo_commands(self):
        """Envoyer des commandes de démonstration"""
        print("📡 Connexion au broker MQTT...")
        self.client.connect(MQTT_BROKER, 1883, 60)
        self.client.loop_start()
        
        time.sleep(2)
        
        demo_sequences = [
            {
                "title": "🇫🇷 Test Irrigation Paris (Zone 001)",
                "commands": [
                    {"command": "irrigation_on", "zone_id": "zone_001", "delay": 3},
                    {"command": "irrigation_off", "zone_id": "zone_001", "delay": 2}
                ]
            },
            {
                "title": "🇮🇹 Changement seuil Milan (Zone 002)",
                "commands": [
                    {"command": "set_threshold", "zone_id": "zone_002", "threshold": 45, "delay": 2}
                ]
            },
            {
                "title": "🇨🇭 Test Irrigation Geneva (Zone 003)",
                "commands": [
                    {"command": "irrigation_on", "zone_id": "zone_003", "delay": 3},
                    {"command": "irrigation_off", "zone_id": "zone_003", "delay": 2}
                ]
            },
            {
                "title": "🌍 Commandes Globales",
                "commands": [
                    {"command": "system_status", "zone_id": "all", "delay": 2},
                    {"command": "set_mode", "zone_id": "all", "mode": "auto", "delay": 2}
                ]
            }
        ]
        
        for sequence in demo_sequences:
            print(f"\n{sequence['title']}")
            print("-" * 50)
            
            for cmd in sequence['commands']:
                message = {k: v for k, v in cmd.items() if k != 'delay'}
                json_msg = json.dumps(message)
                
                result = self.client.publish(MQTT_CONTROL_TOPIC, json_msg)
                
                if result.rc == 0:
                    timestamp = datetime.now().strftime("%H:%M:%S")
                    zone_name = f"Zone {cmd['zone_id']}" if cmd['zone_id'] != "all" else "Toutes zones"
                    print(f"✅ [{timestamp}] Commande '{cmd['command']}' → {zone_name}")
                    
                    if 'threshold' in cmd:
                        print(f"   📊 Nouveau seuil: {cmd['threshold']}%")
                    if 'mode' in cmd:
                        print(f"   ⚙️  Mode: {cmd['mode']}")
                else:
                    print(f"❌ Erreur envoi commande: {result.rc}")
                
                time.sleep(cmd.get('delay', 1))
        
        self.client.loop_stop()
        self.client.disconnect()
    
    def show_zone_status(self):
        """Afficher le statut des zones"""
        print("\n🗺️  STATUT TEMPS RÉEL DES ZONES")
        print("="*50)
        
        zones = [
            {"id": "zone_001", "name": "Paris Garden", "flag": "🇫🇷", "coord": "48.86°N, 2.35°E"},
            {"id": "zone_002", "name": "Milan Greenhouse", "flag": "🇮🇹", "coord": "45.46°N, 9.19°E"},
            {"id": "zone_003", "name": "Geneva Research", "flag": "🇨🇭", "coord": "46.20°N, 6.14°E"}
        ]
        
        for zone in zones:
            print(f"{zone['flag']} {zone['name']} ({zone['id']})")
            print(f"   📍 Coordonnées: {zone['coord']}")
            print(f"   🌡️  Capteur: DHT22 (Pin configuré)")
            print(f"   💧 Servo: Pin configuré pour irrigation")
            print(f"   📊 Seuil: Spécifique à la zone")
            print()
    
    def run_interactive_demo(self):
        """Démonstration interactive"""
        while self.demo_active:
            print("\n🎮 MENU DÉMONSTRATION LEVEL 4")
            print("="*40)
            print("1. 🚀 Lancer séquence de démonstration automatique")
            print("2. 🗺️  Afficher statut des zones")
            print("3. 🎛️  Lancer contrôleur multi-zones")
            print("4. 📊 Voir les tests Level 4")
            print("5. 🌐 Ouvrir dashboard web")
            print("6. 📖 Voir documentation Level 4")
            print("7. ❌ Quitter")
            
            try:
                choice = input("\nChoisissez une option (1-7): ").strip()
                
                if choice == "1":
                    print("\n🚀 Lancement de la démonstration automatique...")
                    self.send_demo_commands()
                    print("\n✅ Démonstration terminée!")
                    
                elif choice == "2":
                    self.show_zone_status()
                    
                elif choice == "3":
                    print("🎛️  Lancement du contrôleur multi-zones...")
                    print("ℹ️  Utilisez Ctrl+C pour revenir au menu principal")
                    try:
                        subprocess.run([sys.executable, "multi_zone_controller.py"], check=True)
                    except subprocess.CalledProcessError:
                        print("❌ Erreur lors du lancement du contrôleur")
                    except KeyboardInterrupt:
                        print("\n↩️  Retour au menu principal...")
                        
                elif choice == "4":
                    print("📊 Lancement des tests Level 4...")
                    try:
                        subprocess.run([sys.executable, "test_level4_multi_zone.py"], check=True)
                    except subprocess.CalledProcessError:
                        print("❌ Erreur lors des tests")
                        
                elif choice == "5":
                    print("🌐 Lancement du dashboard web...")
                    print("🔗 Accès: http://localhost:5000")
                    print("ℹ️  Utilisez Ctrl+C pour arrêter le serveur")
                    try:
                        subprocess.run([sys.executable, "app.py"], check=True)
                    except subprocess.CalledProcessError:
                        print("❌ Erreur lors du lancement du dashboard")
                    except KeyboardInterrupt:
                        print("\n↩️  Serveur arrêté, retour au menu...")
                        
                elif choice == "6":
                    self.show_documentation()
                    
                elif choice == "7":
                    print("👋 Fin de la démonstration Level 4!")
                    self.demo_active = False
                    
                else:
                    print("❌ Option invalide, veuillez réessayer")
                    
            except KeyboardInterrupt:
                print("\n👋 Fin de la démonstration Level 4!")
                self.demo_active = False
            except Exception as e:
                print(f"❌ Erreur: {e}")
    
    def show_documentation(self):
        """Afficher la documentation Level 4"""
        print("\n📖 DOCUMENTATION LEVEL 4 - SYSTÈME MULTI-ZONES")
        print("="*60)
        print("🎯 OBJECTIFS LEVEL 4:")
        print("   • Implémenter un système d'irrigation multi-zones")
        print("   • Gérer plusieurs locations géographiques")
        print("   • Contrôle individuel par zone")
        print("   • Surveillance GPS de chaque zone")
        print()
        print("🏗️  ARCHITECTURE:")
        print("   • main_level4_multi_irrigation.py - ESP32 multi-zones")
        print("   • multi_zone_controller.py - Contrôleur Python")
        print("   • diagram.json - 3 DHT22 + 3 servos")
        print("   • Base de données étendue avec zones")
        print("   • Dashboard multi-zones")
        print()
        print("🌍 ZONES CONFIGURÉES:")
        print("   • Zone 001: Paris Garden (35% seuil)")
        print("   • Zone 002: Milan Greenhouse (40% seuil)")
        print("   • Zone 003: Geneva Research (38% seuil)")
        print()
        print("🔧 AMÉLIORATIONS POSSIBLES:")
        print("   • Détection d'intrusion avec OpenCV")
        print("   • Classification maladies des plantes")
        print("   • Intégration ESP32 physique")
        print("   • Alertes météo par zone")
        print("="*60)

def main():
    print("🌍 Initialisation de la démonstration Level 4...")
    demo = Level4Demo()
    
    demo.print_banner()
    
    # Vérification rapide des fichiers
    required_files = [
        "main_level4_multi_irrigation.py",
        "multi_zone_controller.py", 
        "test_level4_multi_zone.py",
        "app.py"
    ]
    
    missing_files = []
    for file_name in required_files:
        try:
            with open(file_name, 'r'):
                pass
        except FileNotFoundError:
            missing_files.append(file_name)
    
    if missing_files:
        print(f"⚠️  Fichiers manquants: {missing_files}")
        print("❌ Veuillez d'abord compléter l'installation Level 4")
        return
    
    print("✅ Tous les fichiers Level 4 présents!")
    print("🚀 Prêt pour la démonstration...")
    
    # Lancer la démonstration interactive
    demo.run_interactive_demo()

if __name__ == "__main__":
    main()
