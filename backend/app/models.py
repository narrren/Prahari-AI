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
    INACTIVITY = "INACTIVITY"         # Legacy
    SIGNAL_LOST = "SIGNAL_LOST_CRITICAL" # V3.1
    FALL_DETECTED = "FALL_DETECTED"
    SOS_MANUAL = "SOS_MANUAL"
    Unconscious = "UNCONSCIOUS" # Matches AnomalyDetection enum usage

class Alert(BaseModel):
    alert_id: str
    device_id: str
    did: str
    type: str # Changed to str to allow flexible types like 'SIGNAL_LOST_CRITICAL'
    severity: str  # CRITICAL, HIGH, MEDIUM, LOW
    timestamp: float
    location: GeoPoint
    message: str
    
    # State Management (V3.0 Operations)
    status: str = "DETECTED" # DETECTED, ACKNOWLEDGED, RESOLVED
    ack_by: Optional[str] = None
    ack_time: Optional[float] = None
    resolved_by: Optional[str] = None
    resolved_time: Optional[float] = None
    
    # Smart Intelligence (V3.1)
    confidence: float = 100.0
    suggested_action: str = "Check Dashboard"

# --- GEOFENCE GOVERNANCE MODULE ---

class GeoFence(BaseModel):
    zone_id: str
    name: str
    risk_level: str # HIGH, MEDIUM
    center: GeoPoint
    radius_meters: float
    description: str = ""
    
    # Governance Fields
    version: int = 1
    effective_from: float = 0.0 # Timestamp
    effective_to: Optional[float] = None # None = Indefinite
    approved_by: str = "SYSTEM_BOOTSTRAP"
    audit_hash: str = "" # SHA256(Parameters + PreviousHash)
    is_active: bool = True
    reason: str = "Initial Deployment"

class GeofenceAuditLog(BaseModel):
    """
    Immutable record of a boundary change.
    """
    log_id: str
    zone_id: str
    action: str # CREATE, UPDATE, EXPIRE
    actor_id: str
    timestamp: float
    old_hash: str
    new_hash: str
    reason: str
