import sqlite3

def check_database():
    """Check the database content"""
    try:
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        
        # Check sensors table
        print("=== SENSORS TABLE ===")
        cursor.execute("SELECT * FROM sensors")
        sensors = cursor.fetchall()
        print(f"Found {len(sensors)} sensors:")
        for sensor in sensors:
            print(f"  ID: {sensor[0]}, Type: {sensor[1]}, Location: ({sensor[2]}, {sensor[3]}), Description: {sensor[4]}")
        
        # Check sensor_data table
        print("\n=== SENSOR DATA TABLE ===")
        cursor.execute("SELECT COUNT(*) FROM sensor_data")
        count = cursor.fetchone()[0]
        print(f"Found {count} sensor readings")
        
        if count > 0:
            cursor.execute("SELECT * FROM sensor_data ORDER BY timestamp DESC LIMIT 5")
            recent_data = cursor.fetchall()
            print("Recent readings:")
            for data in recent_data:
                print(f"  {data[1]} - Temp: {data[2]}°C, Humidity: {data[3]}% at {data[4]}")
        
        conn.close()
        print("\n✅ Database check completed successfully!")
        
    except Exception as e:
        print(f"❌ Database check failed: {e}")

if __name__ == "__main__":
    check_database()
