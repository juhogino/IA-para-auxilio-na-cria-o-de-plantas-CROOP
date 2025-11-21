# app/auth.py
from fastapi import HTTPException, Header, Depends
from sqlalchemy.orm import Session
from .database import SessionLocal
from .crud import get_device_by_id

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def verify_device_token(device_id: str, x_device_token: str = Header(...), db: Session = Depends(get_db)):
    dev = get_device_by_id(db, device_id)
    if not dev or dev.token != x_device_token:
        raise HTTPException(status_code=401, detail="Invalid device or token")
    return dev
