from flask import Flask, render_template, request, jsonify
import sqlite3
import pandas as pd
import matplotlib
matplotlib.use('Agg')  # Use non-GUI backend for Flask
import matplotlib.pyplot as plt
import io
import base64
import json
import paho.mqtt.client as mqtt
import threading
import time

app = Flask(__name__)

# MQTT Configuration for irrigation control
MQTT_BROKER = "broker.mqttdashboard.com"
MQTT_CONTROL_TOPIC = "irrigation-control"

# Initialize MQTT client for sending irrigation commands
mqtt_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1, "flask_irrigation_control")
mqtt_client.connect(MQTT_BROKER, 1883, 60)
mqtt_client.loop_start()

def get_data():
    conn = sqlite3.connect('database.db')
    query = '''
    SELECT sd.*, s.sensor_type, s.latitude, s.longitude, s.description
    FROM sensor_data sd
    LEFT JOIN sensors s ON sd.sensor_id = s.sensor_id
    '''
    df = pd.read_sql_query(query, conn)
    conn.close()
    if not df.empty:
        df['timestamp'] = pd.to_datetime(df['timestamp'])
    return df

def get_sensors():
    conn = sqlite3.connect('database.db')
    sensors_df = pd.read_sql_query("SELECT * FROM sensors", conn)
    conn.close()
    return sensors_df

@app.route('/')
def index():
    df = get_data()
    sensors_df = get_sensors()
    
    if df.empty:
        return render_template('index.html', 
                             no_data=True, 
                             sensors=sensors_df.to_dict('records') if not sensors_df.empty else [])

    # Get unique sensors for selection - convert to Python list
    sensors = df['sensor_id'].unique().tolist()
    sensor_types = df['sensor_type'].dropna().unique().tolist()
    
    # Default sensor selection
    selected_sensors = request.args.getlist('sensors')
    if not selected_sensors and len(sensors) > 0:
        selected_sensors = [sensors[0]]
    selected_type = request.args.get('type', 'all')
    
    # Filter data based on selection
    filtered_df = df.copy()
    if selected_sensors:
        filtered_df = filtered_df[filtered_df['sensor_id'].isin(selected_sensors)]
    if selected_type != 'all':
        filtered_df = filtered_df[filtered_df['sensor_type'] == selected_type]
    
    # Create plots
    plot_urls = {}
    
    if not filtered_df.empty:
        # Temperature plot
        temp_data = filtered_df.dropna(subset=['temperature'])
        if not temp_data.empty:
            plt.figure(figsize=(12, 6))
            for sensor in temp_data['sensor_id'].unique():
                sensor_data = temp_data[temp_data['sensor_id'] == sensor]
                plt.plot(sensor_data['timestamp'], sensor_data['temperature'], 
                        label=f"{sensor}", marker='o', markersize=3)
            plt.title('Temperature over Time')
            plt.xlabel('Time')
            plt.ylabel('Temperature (°C)')
            plt.legend()
            plt.xticks(rotation=45)
            plt.tight_layout()
            
            img = io.BytesIO()
            plt.savefig(img, format='png', dpi=100, bbox_inches='tight')
            plt.close()
            img.seek(0)
            plot_urls['temperature'] = base64.b64encode(img.getvalue()).decode()
        
        # Humidity plot
        humid_data = filtered_df.dropna(subset=['humidity'])
        if not humid_data.empty:
            plt.figure(figsize=(12, 6))
            for sensor in humid_data['sensor_id'].unique():
                sensor_data = humid_data[humid_data['sensor_id'] == sensor]
                plt.plot(sensor_data['timestamp'], sensor_data['humidity'], 
                        label=f"{sensor}", marker='o', markersize=3)
            plt.title('Humidity over Time')
            plt.xlabel('Time')
            plt.ylabel('Humidity (%)')
            plt.legend()
            plt.xticks(rotation=45)
            plt.tight_layout()
            
            img = io.BytesIO()
            plt.savefig(img, format='png', dpi=100, bbox_inches='tight')
            plt.close()
            img.seek(0)
            plot_urls['humidity'] = base64.b64encode(img.getvalue()).decode()

    # Prepare sensor statistics - ensure all values are Python types
    stats_by_type = {}
    if 'sensor_type' in filtered_df.columns:
        for sensor_type in filtered_df['sensor_type'].dropna().unique():
            type_data = filtered_df[filtered_df['sensor_type'] == sensor_type]
            temp_avg = type_data['temperature'].mean()
            humid_avg = type_data['humidity'].mean()
            
            stats_by_type[sensor_type] = {
                'count': int(len(type_data)),
                'temp_avg': float(temp_avg) if pd.notnull(temp_avg) else None,
                'humid_avg': float(humid_avg) if pd.notnull(humid_avg) else None
            }

    return render_template('index.html', 
                         plot_urls=plot_urls,
                         sensors=sensors,  # Now a Python list
                         sensor_types=sensor_types,  # Now a Python list
                         selected_sensors=selected_sensors,
                         selected_type=selected_type,
                         stats_by_type=stats_by_type,
                         sensors_info=sensors_df.to_dict('records') if not sensors_df.empty else [])

@app.route('/api/sensors')
def api_sensors():
    """API endpoint to get sensor data for map"""
    sensors_df = get_sensors()
    df = get_data()
    
    sensors_data = []
    for _, sensor in sensors_df.iterrows():
        # Get latest reading for this sensor
        sensor_data = df[df['sensor_id'] == sensor['sensor_id']]
        latest_temp = None
        latest_humidity = None
        last_seen = None
        
        if not sensor_data.empty:
            latest = sensor_data.iloc[-1]
            latest_temp = float(latest['temperature']) if pd.notnull(latest['temperature']) else None
            latest_humidity = float(latest['humidity']) if pd.notnull(latest['humidity']) else None
            last_seen = latest['timestamp'].isoformat() if pd.notnull(latest['timestamp']) else None
        
        sensors_data.append({
            'sensor_id': str(sensor['sensor_id']),
            'sensor_type': str(sensor['sensor_type']),
            'latitude': float(sensor['latitude']) if pd.notnull(sensor['latitude']) else None,
            'longitude': float(sensor['longitude']) if pd.notnull(sensor['longitude']) else None,
            'description': str(sensor['description']) if pd.notnull(sensor['description']) else "",
            'latest_temp': latest_temp,
            'latest_humidity': latest_humidity,
            'last_seen': last_seen
        })
    
    return jsonify(sensors_data)

# Level 3: Irrigation Control Endpoints

@app.route('/api/irrigation/status')
def irrigation_status():
    """Get irrigation status for all sensors"""
    conn = sqlite3.connect('database.db')
    
    # Get current irrigation settings
    settings_df = pd.read_sql_query("SELECT * FROM irrigation_settings", conn)
    
    # Get latest sensor data with irrigation info
    query = '''
    SELECT sensor_id, temperature, humidity, irrigation_active, irrigation_mode, 
           humidity_threshold, timestamp
    FROM sensor_data 
    WHERE timestamp IN (
        SELECT MAX(timestamp) 
        FROM sensor_data 
        GROUP BY sensor_id
    )
    '''
    data_df = pd.read_sql_query(query, conn)
    
    # Get recent irrigation events
    events_df = pd.read_sql_query("""
        SELECT * FROM irrigation_events 
        ORDER BY timestamp DESC LIMIT 10
    """, conn)
    
    conn.close()
    
    return jsonify({
        'settings': settings_df.to_dict('records'),
        'current_data': data_df.to_dict('records'),
        'recent_events': events_df.to_dict('records')
    })

@app.route('/api/irrigation/control', methods=['POST'])
def irrigation_control():
    """Send irrigation control commands"""
    try:
        data = request.get_json()
        sensor_id = data.get('sensor_id', 'micropython-weather-demo')
        command = data.get('command')
        
        message = {
            "command": command,
            "sensor_id": sensor_id,
            "timestamp": time.time()
        }
        
        # Add additional parameters based on command
        if command == "set_threshold":
            message["threshold"] = data.get('threshold', 40)
        elif command == "set_mode":
            message["mode"] = data.get('mode', 'manual')
        
        # Send MQTT command
        mqtt_client.publish(MQTT_CONTROL_TOPIC, json.dumps(message))
        
        return jsonify({
            'success': True,
            'message': f'Command {command} sent to {sensor_id}',
            'data': message
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400

@app.route('/api/irrigation/events')
def irrigation_events():
    """Get irrigation events history"""
    conn = sqlite3.connect('database.db')
    
    # Get pagination parameters
    limit = request.args.get('limit', 50, type=int)
    offset = request.args.get('offset', 0, type=int)
    
    query = '''
    SELECT ie.*, s.sensor_type, s.description
    FROM irrigation_events ie
    LEFT JOIN sensors s ON ie.sensor_id = s.sensor_id
    ORDER BY ie.timestamp DESC
    LIMIT ? OFFSET ?
    '''
    
    events_df = pd.read_sql_query(query, conn, params=(limit, offset))
    conn.close()
    
    return jsonify(events_df.to_dict('records'))

if __name__ == "__main__":
    app.run(debug=True)
