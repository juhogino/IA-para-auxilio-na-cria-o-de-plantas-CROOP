# app/mqtt_client.py
import os
import json
import threading
import time
from paho.mqtt import client as mqtt
from .crud import create_reading
from .database import SessionLocal
from .schemas import SensorPayload
from dotenv import load_dotenv
load_dotenv()

MQTT_BROKER = os.getenv("MQTT_BROKER", "localhost")
MQTT_PORT = int(os.getenv("MQTT_PORT", 1883))
MQTT_TOPIC = os.getenv("MQTT_TOPIC", "plants/+/sensors")

def on_connect(client, userdata, flags, rc):
    print("MQTT connected with rc=", rc)
    client.subscribe(MQTT_TOPIC)

def on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode())
        # expected to be compatible with SensorPayload
        sp = SensorPayload(**payload)
        db = SessionLocal()
        try:
            create_reading(db, sp)
            print("Saved reading from", sp.device_id)
        finally:
            db.close()
    except Exception as e:
        print("MQTT message handling error:", e)

def start_mqtt_loop():
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(MQTT_BROKER, MQTT_PORT, 60)
    client.loop_start()
    print("MQTT loop started connecting to", MQTT_BROKER)
    return client
