import sqlite3

def init_db():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    
    # Create sensors table to store sensor metadata
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sensors (
            sensor_id TEXT PRIMARY KEY,
            sensor_type TEXT NOT NULL,
            latitude REAL,
            longitude REAL,
            description TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create sensor_data table for readings
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sensor_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sensor_id TEXT,
            temperature REAL,
            humidity REAL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (sensor_id) REFERENCES sensors (sensor_id)
        )
    ''')
    
    # Insert sample sensors if they don't exist
    sample_sensors = [
        ('temp-sensor-001', 'temperature', 48.8566, 2.3522, 'Paris Temperature Sensor'),
        ('humid-sensor-001', 'humidity', 48.8566, 2.3522, 'Paris Humidity Sensor'),
        ('temp-sensor-002', 'temperature', 45.4642, 9.1900, 'Milan Temperature Sensor'),
        ('humid-sensor-002', 'humidity', 45.4642, 9.1900, 'Milan Humidity Sensor'),
        ('micropython-weather-demo', 'combined', 46.2044, 6.1432, 'Geneva Combined Sensor')
    ]
    
    cursor.executemany('''
        INSERT OR IGNORE INTO sensors (sensor_id, sensor_type, latitude, longitude, description)
        VALUES (?, ?, ?, ?, ?)
    ''', sample_sensors)
    
    conn.commit()
    conn.close()
    print("Database initialized with sensors table and sample data.")

if __name__ == "__main__":
    init_db()
