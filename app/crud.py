# app/crud.py
from sqlalchemy.orm import Session
from . import models, schemas
import datetime

def create_device(db: Session, device_id: str, token: str, owner: str = None):
    d = models.Device(device_id=device_id, token=token, owner=owner)
    db.add(d); db.commit(); db.refresh(d)
    return d

def get_device_by_id(db: Session, device_id: str):
    return db.query(models.Device).filter(models.Device.device_id == device_id).first()

def create_reading(db: Session, payload: schemas.SensorPayload):
    r = models.SensorReading(
        timestamp = payload.timestamp or datetime.datetime.utcnow(),
        device_id = payload.device_id,
        species = payload.species,
        soil_moisture = payload.soil_moisture,
        air_temp_c = payload.air_temp_c,
        air_humidity_pct = payload.air_humidity_pct,
        light_lux = payload.light_lux,
        extra = payload.extra or {}
    )
    db.add(r); db.commit(); db.refresh(r)
    return r

def get_latest_reading(db: Session, device_id: str):
    return db.query(models.SensorReading).filter(models.SensorReading.device_id==device_id).order_by(models.SensorReading.timestamp.desc()).first()

def create_water_event(db: Session, device_id: str, method="manual", reason=None, metadata=None):
    we = models.WaterEvent(device_id=device_id, method=method, reason=reason, metadata=metadata or {})
    db.add(we); db.commit(); db.refresh(we)
    return we

def create_plant(db: Session, plant: schemas.PlantCreate):
    p = models.Plant(name=plant.name, species=plant.species, stage=plant.stage, device_id=plant.device_id, metadata=plant.metadata)
    db.add(p); db.commit(); db.refresh(p)
    return p

def get_plant(db: Session, plant_id: int):
    return db.query(models.Plant).filter(models.Plant.id==plant_id).first()

def get_history(db: Session, device_id: str, limit: int = 100):
    return db.query(models.SensorReading).filter(models.SensorReading.device_id==device_id).order_by(models.SensorReading.timestamp.desc()).limit(limit).all()
