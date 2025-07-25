import network
import time
from machine import Pin
import dht
import ujson
from umqtt.simple import MQTTClient

MQTT_CLIENT_ID = "micropython-weather-demo"
MQTT_BROKER    = "broker.mqttdashboard.com"
MQTT_TOPIC     = "wokwi-weather"

# Sensor configuration
SENSOR_TYPE = "combined"
LATITUDE = 46.2044  # Geneva coordinates
LONGITUDE = 6.1432
DESCRIPTION = "Geneva Combined Sensor"

sensor = dht.DHT22(Pin(15))

sta_if = network.WLAN(network.STA_IF)
sta_if.active(True)
sta_if.connect('Wokwi-GUEST', '')
while not sta_if.isconnected():
    time.sleep(0.1)

client = MQTTClient(MQTT_CLIENT_ID, MQTT_BROKER)
client.connect()

prev_weather = ""
while True:
    sensor.measure()
    message = ujson.dumps({
        "sensor_id": MQTT_CLIENT_ID,
        "sensor_type": SENSOR_TYPE,
        "temp": sensor.temperature(),
        "humidity": sensor.humidity(),
        "latitude": LATITUDE,
        "longitude": LONGITUDE,
        "description": DESCRIPTION
    })
    if message != prev_weather:
        client.publish(MQTT_TOPIC, message)
        prev_weather = message
    time.sleep(1)
