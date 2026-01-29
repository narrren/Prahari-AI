from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum

class SafetyStatus(str, Enum):
    SAFE = "SAFE"
    CAUTION = "CAUTION"
    DANGER = "DANGER"
    SOS = "SOS"

class GeoPoint(BaseModel):
    lat: float
    lng: float

class TelemetryData(BaseModel):
    device_id: str
    did: str = Field(..., description="Decentralized Identity of the user")
    timestamp: float
    location: GeoPoint
    speed: float = 0.0
    heading: float = 0.0
    battery_level: float = 100.0
    is_panic: bool = False

class AlertType(str, Enum):
    GEOFENCE_BREACH = "GEOFENCE_BREACH"
    INACTIVITY = "INACTIVITY"
    FALL_DETECTED = "FALL_DETECTED"
    SOS_MANUAL = "SOS_MANUAL"

class Alert(BaseModel):
    alert_id: str
    device_id: str
    did: str
    type: AlertType
    severity: str  # HIGH, MEDIUM, LOW
    timestamp: float
    location: GeoPoint
    message: str
    resolved: bool = False

class GeoFence(BaseModel):
    zone_id: str
    name: str
    risk_level: str # HIGH, MEDIUM
    center: GeoPoint
    radius_meters: float
    description: str = ""
