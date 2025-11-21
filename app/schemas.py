# app/schemas.py
from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime

class SensorPayload(BaseModel):
    device_id: str
    timestamp: Optional[datetime] = None
    species: Optional[str] = None
    soil_moisture: Optional[float] = None
    air_temp_c: Optional[float] = None
    air_humidity_pct: Optional[float] = None
    light_lux: Optional[float] = None
    extra: Optional[Dict[str, Any]] = {}

class IngestResponse(BaseModel):
    saved: bool
    water_now: Optional[bool] = None
    reason: Optional[str] = None

class PlantCreate(BaseModel):
    name: str
    species: str
    stage: Optional[str] = None
    device_id: Optional[str] = None
    metadata: Optional[Dict[str,Any]] = {}

class PlantOut(PlantCreate):
    id: int

class WaterActuate(BaseModel):
    device_id: str
    duration_seconds: Optional[int] = 5
    token: str  # auth token for devices or user

