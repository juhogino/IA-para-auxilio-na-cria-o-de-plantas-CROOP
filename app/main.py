from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks
from .database import engine, Base, SessionLocal
from . import models, schemas, crud, mqtt_client, ml_model, auth
from sqlalchemy.orm import Session
import os
from dotenv import load_dotenv
load_dotenv()

# create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Plant AI Backend")

ml = ml_model.MLModel()  # loads model from ML_MODEL_PATH env

# start mqtt in background when app starts
@app.on_event("startup")
def startup_event():
    try:
        mqtt_client.start_mqtt_loop()
    except Exception as e:
        print("MQTT startup error (continue):", e)

@app.post("/ingest", response_model=schemas.IngestResponse)
def ingest(payload: schemas.SensorPayload, db: Session = Depends(auth.get_db), x_device_token: str = Depends(lambda: None)):
    """
    Ingest via HTTP. Device should send header 'X-Device-Token' if using token auth.
    For simplicity this endpoint currently allows unauthenticated ingest; adjust as needed.
    """
    # Persist reading
    reading = crud.create_reading(db, payload)
    # prepare features for model
    latest_water = None
    # naive days_since_water: not implemented here; set 0
    features = {
        "soil_moisture": payload.soil_moisture or 0.0,
        "air_temp_c": payload.air_temp_c or 0.0,
        "air_humidity_pct": payload.air_humidity_pct or 0.0,
        "light_lux": payload.light_lux or 0.0,
        "species": payload.species or None,
        "days_since_water": 0.0
    }
    pred = ml.predict_water(features)
    # optionally create water event if auto-actuate (omitted)
    return schemas.IngestResponse(saved=True, water_now=pred.get("water_now"), reason=pred.get("reason"))

@app.get("/plants/{device_id}/status")
def get_status(device_id: str, db: Session = Depends(auth.get_db)):
    latest = crud.get_latest_reading(db, device_id)
    if not latest:
        raise HTTPException(status_code=404, detail="no readings")
    features = {
        "soil_moisture": latest.soil_moisture or 0.0,
        "air_temp_c": latest.air_temp_c or 0.0,
        "air_humidity_pct": latest.air_humidity_pct or 0.0,
        "light_lux": latest.light_lux or 0.0,
        "species": latest.species or None,
        "days_since_water": 0.0
    }
    pred = ml.predict_water(features)
    return {"latest_reading": {
                "timestamp": latest.timestamp,
                "soil_moisture": latest.soil_moisture,
                "air_temp_c": latest.air_temp_c,
                "air_humidity_pct": latest.air_humidity_pct,
                "light_lux": latest.light_lux
            },
            "water_now": pred.get("water_now"),
            "score": pred.get("score"),
            "reason": pred.get("reason")
           }

@app.get("/plants/{device_id}/history")
def history(device_id: str, limit: int = 100, db: Session = Depends(auth.get_db)):
    hist = crud.get_history(db, device_id, limit=limit)
    return {"count": len(hist), "items": [{
        "timestamp": r.timestamp,
        "soil_moisture": r.soil_moisture,
        "air_temp_c": r.air_temp_c,
        "air_humidity_pct": r.air_humidity_pct,
        "light_lux": r.light_lux
    } for r in hist]}

@app.post("/plants", response_model=schemas.PlantOut)
def create_plant(plant: schemas.PlantCreate, db: Session = Depends(auth.get_db)):
    p = crud.create_plant(db, plant)
    return p

@app.post("/actuate")
def actuate(req: schemas.WaterActuate, background: BackgroundTasks, db: Session = Depends(auth.get_db)):
    """
    Request device to actuate (e.g., water). For full automation you'd integrate with MQTT or device control.
    Here we log a water event and (optionally) publish an MQTT message to the device topic.
    """
    # verify token for device simple check
    dev = crud.get_device_by_id(db, req.device_id)
    if not dev or dev.token != req.token:
        raise HTTPException(status_code=401, detail="invalid token")
    # create event
    evt = crud.create_water_event(db, req.device_id, method="remote", reason="user_request", metadata={"duration_seconds": req.duration_seconds})
    # publish MQTT command
    try:
        # publish to topic "plants/{device_id}/actuate"
        import paho.mqtt.publish as publish
        broker = os.getenv("MQTT_BROKER", "localhost")
        port = int(os.getenv("MQTT_PORT", 1883))
        topic = f"plants/{req.device_id}/actuate"
        payload = {"action": "water", "duration": req.duration_seconds}
        background.add_task(publish.single, topic, payload=str(payload), hostname=broker, port=port)
    except Exception as e:
        print("actuate publish error", e)
    return {"ok": True, "event_id": evt.id}