import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

def plot_data():
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

    df['timestamp'] = pd.to_datetime(df['timestamp'])

    # Create comprehensive plots
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    fig.suptitle('MQTT Weather Logger Dashboard - Multi-Sensor Analysis', fontsize=16, fontweight='bold')

    # Plot 1: Temperature over time for each sensor
    ax1 = axes[0, 0]
    temp_data = df.dropna(subset=['temperature'])
    if not temp_data.empty:
        sensors = temp_data['sensor_id'].unique()
        colors = plt.cm.tab10(np.linspace(0, 1, len(sensors)))
        
        for i, sensor in enumerate(sensors):
            sensor_data = temp_data[temp_data['sensor_id'] == sensor]
            ax1.plot(sensor_data['timestamp'], sensor_data['temperature'], 
                    label=sensor, color=colors[i], marker='o', markersize=3, linewidth=2)
        
        ax1.set_title('Temperature Trends by Sensor', fontweight='bold')
        ax1.set_xlabel('Time')
        ax1.set_ylabel('Temperature (°C)')
        ax1.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        ax1.grid(True, alpha=0.3)
    else:
        ax1.text(0.5, 0.5, 'No temperature data', ha='center', va='center', transform=ax1.transAxes)
        ax1.set_title('Temperature Trends by Sensor')

    # Plot 2: Humidity over time for each sensor
    ax2 = axes[0, 1]
    humid_data = df.dropna(subset=['humidity'])
    if not humid_data.empty:
        sensors = humid_data['sensor_id'].unique()
        colors = plt.cm.tab10(np.linspace(0, 1, len(sensors)))
        
        for i, sensor in enumerate(sensors):
            sensor_data = humid_data[humid_data['sensor_id'] == sensor]
            ax2.plot(sensor_data['timestamp'], sensor_data['humidity'], 
                    label=sensor, color=colors[i], marker='s', markersize=3, linewidth=2)
        
        ax2.set_title('Humidity Trends by Sensor', fontweight='bold')
        ax2.set_xlabel('Time')
        ax2.set_ylabel('Humidity (%)')
        ax2.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        ax2.grid(True, alpha=0.3)
    else:
        ax2.text(0.5, 0.5, 'No humidity data', ha='center', va='center', transform=ax2.transAxes)
        ax2.set_title('Humidity Trends by Sensor')

    # Plot 3: Average values by sensor type
    ax3 = axes[1, 0]
    if 'sensor_type' in df.columns:
        type_stats = df.groupby('sensor_type').agg({
            'temperature': 'mean',
            'humidity': 'mean'
        }).dropna()
        
        if not type_stats.empty:
            x = range(len(type_stats.index))
            width = 0.35
            
            temp_means = type_stats['temperature'].fillna(0)
            humid_means = type_stats['humidity'].fillna(0)
            
            bars1 = ax3.bar([i - width/2 for i in x], temp_means, width, 
                           label='Temperature (°C)', color='orangered', alpha=0.8)
            bars2 = ax3.bar([i + width/2 for i in x], humid_means, width, 
                           label='Humidity (%)', color='skyblue', alpha=0.8)
            
            ax3.set_title('Average Values by Sensor Type', fontweight='bold')
            ax3.set_xlabel('Sensor Type')
            ax3.set_ylabel('Average Value')
            ax3.set_xticks(x)
            ax3.set_xticklabels(type_stats.index, rotation=45)
            ax3.legend()
            ax3.grid(True, alpha=0.3)
            
            # Add value labels on bars
            for bar in bars1:
                height = bar.get_height()
                if height > 0:
                    ax3.text(bar.get_x() + bar.get_width()/2., height + 0.5,
                            f'{height:.1f}', ha='center', va='bottom', fontsize=9)
            
            for bar in bars2:
                height = bar.get_height()
                if height > 0:
                    ax3.text(bar.get_x() + bar.get_width()/2., height + 1,
                            f'{height:.1f}', ha='center', va='bottom', fontsize=9)
        else:
            ax3.text(0.5, 0.5, 'No type data', ha='center', va='center', transform=ax3.transAxes)
    else:
        ax3.text(0.5, 0.5, 'No sensor type data', ha='center', va='center', transform=ax3.transAxes)
    ax3.set_title('Average Values by Sensor Type')

    # Plot 4: Data distribution (readings per sensor)
    ax4 = axes[1, 1]
    sensor_counts = df['sensor_id'].value_counts()
    if not sensor_counts.empty:
        colors = plt.cm.Set3(np.linspace(0, 1, len(sensor_counts)))
        wedges, texts, autotexts = ax4.pie(sensor_counts.values, labels=sensor_counts.index, 
                                          autopct='%1.1f%%', colors=colors, startangle=90)
        ax4.set_title('Data Distribution by Sensor', fontweight='bold')
        
        # Make percentage text more readable
        for autotext in autotexts:
            autotext.set_color('white')
            autotext.set_fontweight('bold')
    else:
        ax4.text(0.5, 0.5, 'No data', ha='center', va='center', transform=ax4.transAxes)
        ax4.set_title('Data Distribution by Sensor')

    plt.tight_layout()
    plt.subplots_adjust(top=0.93)
    plt.show()

    # Print summary statistics
    print("\n" + "="*60)
    print("SUMMARY STATISTICS")
    print("="*60)
    
    print(f"\nTotal sensors: {df['sensor_id'].nunique()}")
    print(f"Total readings: {len(df)}")
    print(f"Date range: {df['timestamp'].min()} to {df['timestamp'].max()}")
    
    if 'sensor_type' in df.columns:
        print(f"\nSensor types: {', '.join(df['sensor_type'].dropna().unique())}")
        
        for sensor_type in df['sensor_type'].dropna().unique():
            type_data = df[df['sensor_type'] == sensor_type]
            print(f"\n{sensor_type.upper()} SENSORS:")
            print(f"  Count: {len(type_data)} readings")
            if not type_data['temperature'].dropna().empty:
                print(f"  Avg Temperature: {type_data['temperature'].mean():.2f}°C")
            if not type_data['humidity'].dropna().empty:
                print(f"  Avg Humidity: {type_data['humidity'].mean():.2f}%")

if __name__ == "__main__":
    plot_data()
