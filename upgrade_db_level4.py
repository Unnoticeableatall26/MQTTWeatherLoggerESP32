"""
Mise à jour de la base de données pour le support multi-zones Level 4
Ajoute les colonnes nécessaires pour la gestion multi-zones

Auteur: HITEMA IoT Team
Date: Décembre 2024
Version: Level 4 Multi-Zone
"""

import sqlite3
import os
from datetime import datetime

def upgrade_database_to_level4():
    """Mise à jour de la base de données pour Level 4 multi-zones"""
    
    print("🔄 Mise à jour de la base de données pour Level 4...")
    
    # Connexion à la base de données
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    
    try:
        # Vérifier les colonnes existantes dans sensor_data
        cursor.execute("PRAGMA table_info(sensor_data)")
        existing_columns = [row[1] for row in cursor.fetchall()]
        print(f"📋 Colonnes existantes dans sensor_data: {existing_columns}")
        
        # Ajouter les colonnes manquantes pour multi-zones
        if 'zone_id' not in existing_columns:
            cursor.execute("ALTER TABLE sensor_data ADD COLUMN zone_id TEXT")
            print("✅ Colonne 'zone_id' ajoutée à sensor_data")
        
        if 'location' not in existing_columns:
            cursor.execute("ALTER TABLE sensor_data ADD COLUMN location TEXT")
            print("✅ Colonne 'location' ajoutée à sensor_data")
        
        if 'latitude' not in existing_columns:
            cursor.execute("ALTER TABLE sensor_data ADD COLUMN latitude REAL")
            print("✅ Colonne 'latitude' ajoutée à sensor_data")
        
        if 'longitude' not in existing_columns:
            cursor.execute("ALTER TABLE sensor_data ADD COLUMN longitude REAL")
            print("✅ Colonne 'longitude' ajoutée à sensor_data")
        
        if 'irrigation_active' not in existing_columns:
            cursor.execute("ALTER TABLE sensor_data ADD COLUMN irrigation_active BOOLEAN DEFAULT 0")
            print("✅ Colonne 'irrigation_active' ajoutée à sensor_data")
        
        # Vérifier irrigation_events
        cursor.execute("PRAGMA table_info(irrigation_events)")
        irrigation_columns = [row[1] for row in cursor.fetchall()]
        print(f"📋 Colonnes existantes dans irrigation_events: {irrigation_columns}")
        
        if 'event' not in irrigation_columns:
            cursor.execute("ALTER TABLE irrigation_events ADD COLUMN event TEXT")
            print("✅ Colonne 'event' ajoutée à irrigation_events")
        
        if 'zone_id' not in irrigation_columns:
            cursor.execute("ALTER TABLE irrigation_events ADD COLUMN zone_id TEXT")
            print("✅ Colonne 'zone_id' ajoutée à irrigation_events")
        
        if 'humidity' not in irrigation_columns:
            cursor.execute("ALTER TABLE irrigation_events ADD COLUMN humidity REAL")
            print("✅ Colonne 'humidity' ajoutée à irrigation_events")
        
        if 'threshold' not in irrigation_columns:
            cursor.execute("ALTER TABLE irrigation_events ADD COLUMN threshold REAL")
            print("✅ Colonne 'threshold' ajoutée à irrigation_events")
        
        if 'location' not in irrigation_columns:
            cursor.execute("ALTER TABLE irrigation_events ADD COLUMN location TEXT")
            print("✅ Colonne 'location' ajoutée à irrigation_events")
        
        # Créer une table pour les zones si elle n'existe pas
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS irrigation_zones (
                zone_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                location TEXT NOT NULL,
                latitude REAL NOT NULL,
                longitude REAL NOT NULL,
                dht_pin INTEGER NOT NULL,
                servo_pin INTEGER NOT NULL,
                humidity_threshold REAL DEFAULT 40.0,
                active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        print("✅ Table 'irrigation_zones' créée")
        
        # Insérer les zones Level 4
        zones_data = [
            ('zone_001', 'Paris Garden', 'Paris', 48.8566, 2.3522, 4, 18, 35.0),
            ('zone_002', 'Milan Greenhouse', 'Milan', 45.4642, 9.1900, 2, 19, 40.0),
            ('zone_003', 'Geneva Research Station', 'Geneva', 46.2044, 6.1432, 15, 21, 38.0)
        ]
        
        cursor.execute("SELECT COUNT(*) FROM irrigation_zones")
        zone_count = cursor.fetchone()[0]
        
        if zone_count == 0:
            cursor.executemany("""
                INSERT INTO irrigation_zones 
                (zone_id, name, location, latitude, longitude, dht_pin, servo_pin, humidity_threshold)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, zones_data)
            print("✅ Zones Level 4 insérées dans irrigation_zones")
        else:
            print(f"ℹ️  {zone_count} zones déjà présentes dans la base")
        
        # Insérer quelques données d'exemple multi-zones
        sample_data = [
            (datetime.now().timestamp(), 22.5, 30.2, 'zone_001', 'Paris', 48.8566, 2.3522, 1),
            (datetime.now().timestamp(), 24.1, 42.7, 'zone_002', 'Milan', 45.4642, 9.1900, 0),
            (datetime.now().timestamp(), 20.8, 36.5, 'zone_003', 'Geneva', 46.2044, 6.1432, 1)
        ]
        
        cursor.executemany("""
            INSERT INTO sensor_data 
            (timestamp, temperature, humidity, zone_id, location, latitude, longitude, irrigation_active)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, sample_data)
        print("✅ Données d'exemple multi-zones insérées")
        
        # Insérer quelques événements d'irrigation
        sample_events = [
            (datetime.now().timestamp(), 'irrigation_start', 'zone_001', 30.2, 35.0, 'Paris'),
            (datetime.now().timestamp(), 'irrigation_stop', 'zone_001', 42.0, 35.0, 'Paris'),
            (datetime.now().timestamp(), 'threshold_change', 'zone_002', 42.7, 40.0, 'Milan')
        ]
        
        cursor.executemany("""
            INSERT INTO irrigation_events 
            (timestamp, event, zone_id, humidity, threshold, location)
            VALUES (?, ?, ?, ?, ?, ?)
        """, sample_events)
        print("✅ Événements d'irrigation d'exemple insérés")
        
        # Validation finale
        cursor.execute("SELECT COUNT(*) FROM sensor_data WHERE zone_id IS NOT NULL")
        multi_zone_count = cursor.fetchone()[0]
        print(f"📊 {multi_zone_count} enregistrements multi-zones dans sensor_data")
        
        cursor.execute("SELECT COUNT(*) FROM irrigation_events WHERE zone_id IS NOT NULL")
        event_count = cursor.fetchone()[0]
        print(f"📊 {event_count} événements multi-zones dans irrigation_events")
        
        cursor.execute("SELECT COUNT(*) FROM irrigation_zones")
        zone_count = cursor.fetchone()[0]
        print(f"📊 {zone_count} zones configurées dans irrigation_zones")
        
        conn.commit()
        print("✅ Base de données mise à jour avec succès pour Level 4!")
        
    except Exception as e:
        print(f"❌ Erreur lors de la mise à jour: {e}")
        conn.rollback()
    finally:
        conn.close()

def show_database_schema():
    """Afficher le schéma de la base de données"""
    print("\n📋 SCHÉMA DE LA BASE DE DONNÉES LEVEL 4")
    print("="*50)
    
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    
    # Liste des tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    
    for table in tables:
        table_name = table[0]
        print(f"\n🗂️  Table: {table_name}")
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = cursor.fetchall()
        
        for col in columns:
            col_name = col[1]
            col_type = col[2]
            not_null = "NOT NULL" if col[3] else ""
            default_val = f"DEFAULT {col[4]}" if col[4] else ""
            primary_key = "PRIMARY KEY" if col[5] else ""
            
            print(f"   📝 {col_name} ({col_type}) {not_null} {default_val} {primary_key}".strip())
    
    conn.close()

if __name__ == "__main__":
    print("🌍 MISE À JOUR BASE DE DONNÉES LEVEL 4 MULTI-ZONES")
    print("="*60)
    
    # Faire une sauvegarde
    if os.path.exists('database.db'):
        import shutil
        backup_name = f"database_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
        shutil.copy2('database.db', backup_name)
        print(f"💾 Sauvegarde créée: {backup_name}")
    
    # Mise à jour
    upgrade_database_to_level4()
    
    # Afficher le schéma final
    show_database_schema()
    
    print(f"\n🎯 Base de données Level 4 prête!")
