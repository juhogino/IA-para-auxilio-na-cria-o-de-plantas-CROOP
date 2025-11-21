from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, JSON, ForeignKey
from sqlalchemy.orm import relationship
from .database import Base
import datetime

class Device(Base):
    __tablename__ = "devices"
    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(String, unique=True, index=True, nullable=False)
    token = Column(String, nullable=False)  # simple token auth for device
    owner = Column(String, nullable=True)

class Plant(Base):
    __tablename__ = "plants"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    species = Column(String, nullable=False)
    stage = Column(String, nullable=True)
    device_id = Column(String, ForeignKey("devices.device_id"), nullable=True)
    metadata = Column(JSON, default={})

    device = relationship("Device", backref="plants")

class SensorReading(Base):
    __tablename__ = "readings"
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    device_id = Column(String, nullable=False, index=True)
    species = Column(String, nullable=True)
    soil_moisture = Column(Float, nullable=True)
    air_temp_c = Column(Float, nullable=True)
    air_humidity_pct = Column(Float, nullable=True)
    light_lux = Column(Float, nullable=True)
    extra = Column(JSON, default={})

class WaterEvent(Base):
    __tablename__ = "water_events"
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    device_id = Column(String, nullable=False, index=True)
    method = Column(String, default="manual")  # manual or auto
    reason = Column(String, nullable=True)
    metadata = Column(JSON, default={})