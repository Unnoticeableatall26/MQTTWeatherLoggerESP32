import sqlite3

def init_irrigation_db():
    """Initialize database with irrigation tables for Level 3"""
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    
    # Create irrigation_events table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS irrigation_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sensor_id TEXT NOT NULL,
            event_type TEXT NOT NULL,  -- 'start', 'stop', 'manual_on', 'manual_off'
            trigger_type TEXT NOT NULL,  -- 'manual', 'auto', 'emergency'
            humidity_value REAL,
            threshold_value REAL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (sensor_id) REFERENCES sensors (sensor_id)
        )
    ''')
    
    # Create irrigation_settings table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS irrigation_settings (
            sensor_id TEXT PRIMARY KEY,
            mode TEXT DEFAULT 'manual',  -- 'manual' or 'auto'
            humidity_threshold REAL DEFAULT 40,
            is_active BOOLEAN DEFAULT 0,
            last_updated DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (sensor_id) REFERENCES sensors (sensor_id)
        )
    ''')
    
    # Add irrigation columns to sensor_data table if they don't exist
    try:
        cursor.execute('''
            ALTER TABLE sensor_data ADD COLUMN irrigation_active BOOLEAN DEFAULT 0
        ''')
        print("Added irrigation_active column to sensor_data")
    except sqlite3.OperationalError:
        pass  # Column already exists
    
    try:
        cursor.execute('''
            ALTER TABLE sensor_data ADD COLUMN irrigation_mode TEXT DEFAULT 'manual'
        ''')
        print("Added irrigation_mode column to sensor_data")
    except sqlite3.OperationalError:
        pass  # Column already exists
    
    try:
        cursor.execute('''
            ALTER TABLE sensor_data ADD COLUMN humidity_threshold REAL DEFAULT 40
        ''')
        print("Added humidity_threshold column to sensor_data")
    except sqlite3.OperationalError:
        pass  # Column already exists
    
    # Insert default irrigation settings for existing sensors
    sample_irrigation_settings = [
        ('micropython-weather-demo', 'auto', 40, 0),
        ('temp-sensor-001', 'manual', 35, 0),
        ('humid-sensor-001', 'auto', 30, 0),
        ('temp-sensor-002', 'manual', 35, 0),
        ('humid-sensor-002', 'auto', 30, 0)
    ]
    
    cursor.executemany('''
        INSERT OR IGNORE INTO irrigation_settings (sensor_id, mode, humidity_threshold, is_active)
        VALUES (?, ?, ?, ?)
    ''', sample_irrigation_settings)
    
    conn.commit()
    conn.close()
    print("✅ Database initialized with irrigation tables and settings.")

def check_irrigation_db():
    """Check irrigation database content"""
    try:
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        
        print("=== IRRIGATION SETTINGS ===")
        cursor.execute("SELECT * FROM irrigation_settings")
        settings = cursor.fetchall()
        print(f"Found {len(settings)} irrigation settings:")
        for setting in settings:
            print(f"  Sensor: {setting[0]}, Mode: {setting[1]}, Threshold: {setting[2]}%, Active: {setting[3]}")
        
        print("\n=== IRRIGATION EVENTS ===")
        cursor.execute("SELECT COUNT(*) FROM irrigation_events")
        count = cursor.fetchone()[0]
        print(f"Found {count} irrigation events")
        
        if count > 0:
            cursor.execute("SELECT * FROM irrigation_events ORDER BY timestamp DESC LIMIT 5")
            events = cursor.fetchall()
            print("Recent events:")
            for event in events:
                print(f"  {event[1]} - {event[2]} ({event[3]}) at {event[6]}")
        
        print("\n=== SENSOR DATA WITH IRRIGATION ===")
        cursor.execute("""
            SELECT sensor_id, temperature, humidity, irrigation_active, irrigation_mode, timestamp 
            FROM sensor_data 
            WHERE irrigation_active IS NOT NULL 
            ORDER BY timestamp DESC LIMIT 5
        """)
        data = cursor.fetchall()
        if data:
            print("Recent sensor data with irrigation info:")
            for row in data:
                print(f"  {row[0]} - Temp: {row[1]}°C, Humidity: {row[2]}%, Irrigation: {row[3]}, Mode: {row[4]} at {row[5]}")
        
        conn.close()
        print("\n✅ Irrigation database check completed!")
        
    except Exception as e:
        print(f"❌ Irrigation database check failed: {e}")

if __name__ == "__main__":
    init_irrigation_db()
    print()
    check_irrigation_db()
