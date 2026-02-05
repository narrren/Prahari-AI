from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum

# --- ENUMS ---
class SafetyStatus(str, Enum):
    SAFE = "SAFE"
    CAUTION = "CAUTION"
    DANGER = "DANGER"
    SOS = "SOS"

class AlertType(str, Enum):
    GEOFENCE_BREACH = "GEOFENCE_BREACH"
    INACTIVITY = "INACTIVITY"         # Legacy
    SIGNAL_LOST = "SIGNAL_LOST_CRITICAL" # V3.1
    FALL_DETECTED = "FALL_DETECTED"
    SOS_MANUAL = "SOS_MANUAL"
    Unconscious = "UNCONSCIOUS" 

class SystemMode(str, Enum):
    NORMAL = "NORMAL"
    DEGRADED = "DEGRADED" # Autonomous fallback
    EMERGENCY = "EMERGENCY" # Kill Switch Active
    CYBER_LOCKDOWN = "CYBER_LOCKDOWN" # Anti-Hacking Mode

class PriorityLevel(int, Enum):
    MILITARY = 100
    DISASTER = 80
    CIVIL = 50
    TOURISM = 20

# --- SUB-MODELS ---
class GeoPoint(BaseModel):
    lat: float
    lng: float

class IncidentHandoff(BaseModel):
    from_actor: str
    to_actor: str
    timestamp: float
    reason: str

class DecisionRecord(BaseModel):
    """
    Immutable record of Human-AI Interaction.
    """
    decision_id: str
    alert_id: str
    ai_recommendation: str
    operator_action: str
    divergence_flag: bool # True if Human ignored AI
    justification: Optional[str] = None
    timestamp: float

# --- CORE MODELS ---
class TelemetryData(BaseModel):
    device_id: str
    did: str = Field(..., description="Decentralized Identity of the user")
    timestamp: float
    location: GeoPoint
    speed: float = 0.0
    heading: float = 0.0
    battery_level: float = 100.0
    is_panic: bool = False
    
    # V5.0 Behavioral Biometrics
    humanity_score: float = 100.0 # 0-100% "Human Entropy" score

class Alert(BaseModel):
    alert_id: str
    device_id: str
    did: str
    type: str 
    severity: str  # CRITICAL, HIGH, MEDIUM, LOW
    timestamp: float
    location: GeoPoint
    message: str
    
    # State Management (V3.0 Operations)
    status: str = "DETECTED" # DETECTED, ACKNOWLEDGED, RESOLVED, ESCALATED
    ack_by: Optional[str] = None
    ack_time: Optional[float] = None
    resolved_by: Optional[str] = None
    resolved_time: Optional[float] = None
    
    # Incident Ownership (V3.2 ICS)
    owner_id: Optional[str] = None # Functional Commander
    handoff_log: List[IncidentHandoff] = []
    escalation_level: int = 0
    
    # Smart Intelligence (V3.1)
    confidence: float = 100.0
    suggested_action: str = "Check Dashboard"
    
    # V5.0 Trustless Governance
    attestation_status: str = "UNVERIFIED" # UNVERIFIED, ATTESTED
    attestors: List[str] = [] 

# --- V5.0 SOAR & FORENSICS ---
class ForensicVerification(BaseModel):
    doc_hash: str
    status: str # VERIFIED, TAMPERED, UNKNOWN
    timestamp: float
    blockchain_txid: str
    signer_did: str

class CyberHudState(BaseModel):
    threat_level: str # LOW, ELEVATED, CRITICAL
    active_countermeasures: List[str]
    blacklisted_ips: List[str]
    last_attack_timestamp: float = 0.0

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
    effective_from: float = 0.0 
    effective_to: Optional[float] = None 
    approved_by: str = "SYSTEM_BOOTSTRAP"
    audit_hash: str = "" 
    is_active: bool = True
    reason: str = "Initial Deployment"
    
    # Conflict Resolution (V3.2)
    priority: int = 20 # Default to Tourism
    authority: str = "CIVIL_ADMIN" # MILITARY, DISASTER_RESPONSE, etc.

class GeofenceAuditLog(BaseModel):
    """
    Immutable record of a boundary change.
    """
    log_id: str
    zone_id: str
    action: str 
    actor_id: str
    timestamp: float
    old_hash: str
    new_hash: str
    reason: str
