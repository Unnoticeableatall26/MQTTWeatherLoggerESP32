import sqlite3
import pandas as pd

def analyze_data():
    conn = sqlite3.connect('database.db')
    
    # Get data with sensor information
    query = '''
    SELECT sd.*, s.sensor_type, s.latitude, s.longitude, s.description
    FROM sensor_data sd
    LEFT JOIN sensors s ON sd.sensor_id = s.sensor_id
    '''
    df = pd.read_sql_query(query, conn)
    conn.close()

    if df.empty:
        print("No data found.")
        return

    # Convert timestamp to datetime
    df['timestamp'] = pd.to_datetime(df['timestamp'])

    # Overall statistics
    print("=== OVERALL STATISTICS ===")
    print(df[['temperature', 'humidity']].describe())

    # Statistics by sensor ID
    print("\n=== STATISTICS BY SENSOR ===")
    grouped = df.groupby('sensor_id')[['temperature', 'humidity']]
    print(grouped.agg(['mean', 'min', 'max', 'std']).round(2))

    # Statistics by sensor type
    print("\n=== STATISTICS BY SENSOR TYPE ===")
    if 'sensor_type' in df.columns:
        type_grouped = df.groupby('sensor_type')[['temperature', 'humidity']]
        stats_by_type = type_grouped.agg(['count', 'mean', 'min', 'max', 'std']).round(2)
        print(stats_by_type)
    
    # Statistics by location (if available)
    print("\n=== STATISTICS BY LOCATION ===")
    if 'latitude' in df.columns and 'longitude' in df.columns:
        df['location'] = df['latitude'].astype(str) + ',' + df['longitude'].astype(str)
        location_grouped = df.groupby('location')[['temperature', 'humidity']]
        location_stats = location_grouped.agg(['count', 'mean', 'min', 'max']).round(2)
        print(location_stats)

    # Statistics by hour
    print("\n=== STATISTICS BY HOUR ===")
    df['hour'] = df['timestamp'].dt.hour
    grouped_hour = df.groupby('hour')[['temperature', 'humidity']]
    hourly_stats = grouped_hour.agg(['mean', 'min', 'max']).round(2)
    print(hourly_stats)

    # Temperature vs Humidity sensors comparison
    print("\n=== SENSOR TYPE COMPARISON ===")
    if 'sensor_type' in df.columns:
        temp_sensors = df[df['sensor_type'] == 'temperature']['temperature'].dropna()
        humid_sensors = df[df['sensor_type'] == 'humidity']['humidity'].dropna()
        combined_sensors = df[df['sensor_type'] == 'combined']
        
        if not temp_sensors.empty:
            print(f"Temperature-only sensors: {len(temp_sensors)} readings, avg: {temp_sensors.mean():.2f}°C")
        if not humid_sensors.empty:
            print(f"Humidity-only sensors: {len(humid_sensors)} readings, avg: {humid_sensors.mean():.2f}%")
        if not combined_sensors.empty:
            print(f"Combined sensors: {len(combined_sensors)} readings")
            if not combined_sensors['temperature'].dropna().empty:
                print(f"  - Avg temperature: {combined_sensors['temperature'].mean():.2f}°C")
            if not combined_sensors['humidity'].dropna().empty:
                print(f"  - Avg humidity: {combined_sensors['humidity'].mean():.2f}%")

if __name__ == "__main__":
    analyze_data()
