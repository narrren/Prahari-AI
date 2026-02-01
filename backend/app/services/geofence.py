import math
import time
import uuid
import hashlib
from typing import List, Optional
from app.models import GeoPoint, GeoFence, GeofenceAuditLog
from app.services.db import get_table

# --- 1. SPATIAL AI HELPER (Pure Python "Shapely" Implementation) ---
class PolygonZone:
    def __init__(self, points):
        self.points = points # List of (lat, lng) tuples

    def contains(self, point_lat, point_lng):
        """
        Ray Casting Algorithm to check if point is inside polygon.
        Standard Point-in-Polygon check.
        """
        inside = False
        n = len(self.points)
        p1x, p1y = self.points[0]
        for i in range(n + 1):
            p2x, p2y = self.points[i % n]
            if point_lng > min(p1y, p2y):
                if point_lng <= max(p1y, p2y):
                    if point_lat <= max(p1x, p2x):
                        if p1y != p2y:
                            xinters = (point_lng - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                        if p1x == p2x or point_lat <= xinters:
                            inside = not inside
            p1x, p1y = p2x, p2y
        return inside

# Defined Red Zone near Tawang (as per User Request)
RED_ZONE_TAWANG = PolygonZone([
    (27.5890, 91.8610), 
    (27.5870, 91.8630), 
    (27.5870, 91.8610), 
    (27.5890, 91.8630) # Rough box around the hotspot
])

# Also keep the cache for standard circular zones if needed
_GEOFENCE_CACHE: List[GeoFence] = []

def log_geofence_audit(audit: GeofenceAuditLog):
    """
    Simulates writing to an immutable Audit Log (Blockchain/WORM Storage).
    """
    print(f"\n[GEOFENCE GOVERNANCE AUDIT] ================================")
    print(f"ACTOR     : {audit.actor_id}")
    print(f"ACTION    : {audit.action}")
    print(f"ZONE_ID   : {audit.zone_id}")
    print(f"HASH_OLD  : {audit.old_hash}")
    print(f"HASH_NEW  : {audit.new_hash}")
    print(f"REASON    : {audit.reason}")
    print(f"TIMESTAMP : {time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(audit.timestamp))}")
    print(f"==========================================================\n")

def create_governed_geofence(
    name: str, 
    center: GeoPoint, 
    radius: float, 
    risk: str, 
    actor_id: str, 
    reason: str, 
    duration_hours: int = None,
    priority: int = 20, # V3.2
    authority: str = "CIVIL_ADMIN" # V3.2
) -> GeoFence:
    """
    Creates a new Versioned, Governance-Compliant Geofence.
    """
    now = time.time()
    zone_id = f"ZONE_{uuid.uuid4().hex[:8].upper()}"
    
    # Calculate Integrity Hash (Merkle-like)
    # Hash(Name + Lat + Lng + Radius + Risk + Reason + Priority)
    payload = f"{name}{center.lat}{center.lng}{radius}{risk}{reason}{priority}"
    new_hash = hashlib.sha256(payload.encode()).hexdigest()
    
    effective_to = (now + (duration_hours * 3600)) if duration_hours else None
    
    fence = GeoFence(
        zone_id=zone_id,
        name=name,
        risk_level=risk,
        center=center,
        radius_meters=radius,
        description=reason,
        version=1,
        effective_from=now,
        effective_to=effective_to,
        approved_by=actor_id,
        audit_hash=new_hash,
        is_active=True,
        reason=reason,
        priority=priority,
        authority=authority
    )
    
    # Persist
    try:
        table = get_table('Prahari_GeoFences')
        # ... logic ...
        
        # Add to Cache
        _GEOFENCE_CACHE.append(fence)
        
        # Audit Log
        audit = GeofenceAuditLog(
            log_id=str(uuid.uuid4()),
            zone_id=zone_id,
            action="CREATE",
            actor_id=actor_id,
            timestamp=now,
            old_hash="0000000000000000",
            new_hash=new_hash,
            reason=reason
        )
        log_geofence_audit(audit)
        
    except Exception as e:
        print(f"Failed to persist geofence: {e}")
        
    return fence

def expire_geofence(zone_id: str):
    """
    Set active=False (Soft Delete).
    """
    target = next((f for f in _GEOFENCE_CACHE if f.zone_id == zone_id), None)
    if target:
        target.is_active = False # Cache update
        # DB Update would go here
        
def load_geofences():
    """
    Hydrate cache from DB or Seed Default.
    """
    global _GEOFENCE_CACHE
    # For this demo/prototype, we seed a default if empty to avoid crashing
    if not _GEOFENCE_CACHE:
        _GEOFENCE_CACHE = [
            GeoFence(
                 zone_id="ZONE_INIT_001",
                 name="Tawang Monastery Perimeter",
                 center=GeoPoint(lat=27.5861, lng=91.8594),
                 radius_meters=300.0,
                 risk_level="MEDIUM",
                 description="Cultural Heritage Site - No Drone Zone",
                 priority=50,
                 authority="CIVIL_ADMIN",
                 approved_by="SYSTEM",
                 is_active=True,
                 version=1
            ),
             GeoFence(
                 zone_id="ZONE_MIL_002",
                 name="Border Outpost Alpha",
                 center=GeoPoint(lat=27.6000, lng=91.8000),
                 radius_meters=500.0,
                 risk_level="HIGH",
                 description="Restricted Military Area",
                 priority=100,
                 authority="DEFENSE_MINISTRY",
                 approved_by="SYSTEM",
                 is_active=True,
                 version=1
            )
        ]

def haversine_distance(p1: GeoPoint, p2: GeoPoint) -> float:
    """
    Calculate great-circle distance between two points in meters.
    """
    R = 6371000 # Earth radius in meters
    phi1, phi2 = math.radians(p1.lat), math.radians(p2.lat)
    dphi = math.radians(p2.lat - p1.lat)
    dlambda = math.radians(p2.lng - p1.lng)
    
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    return R * c

def check_geofence_breach(location: GeoPoint) -> Optional[GeoFence]:
    """
    Hybrid Check with PRIORITY CONFLICT RESOLUTION (V3.2).
    1. Collect ALL overlapping zones.
    2. Sort by Priority (Military > Civil > Tourism).
    3. Return highest authority zone.
    """
    breached_zones = []

    # 1. Polygon Check (Static Military Zone)
    if RED_ZONE_TAWANG.contains(location.lat, location.lng):
        breached_zones.append(GeoFence(
            zone_id="POLY_RED_01",
            name="Restricted Border Zone (Polygon)",
            risk_level="HIGH",
            center=location, 
            radius_meters=0.0,
            description="Geospatial Polygon Breach",
            approved_by="MILITARY_COMMAND",
            priority=100, # MILITARY Priority
            authority="DEFENSE_MINISTRY",
            version=99
        ))

    # 2. Circular Check (Dynamic Zones)
    if not _GEOFENCE_CACHE:
        load_geofences()

    for fence in _GEOFENCE_CACHE:
        dist = haversine_distance(location, fence.center)
        if dist <= fence.radius_meters:
            breached_zones.append(fence)

    if not breached_zones:
        return None

    # 3. Conflict Resolution: Highest Priority Wins
    # If tie, use most restrictive risk (HIGH > MEDIUM) - simplistic sort here on priority
    breached_zones.sort(key=lambda x: x.priority, reverse=True)
    
    winning_zone = breached_zones[0]
    
    # Conflict Debugging
    if len(breached_zones) > 1:
        # print(f"DEBUG: Conflict Resolved. Winner: {winning_zone.name} ({winning_zone.priority}) over {breached_zones[1].name}")
        pass

    return winning_zone
