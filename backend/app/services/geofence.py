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
    duration_hours: int = None
) -> GeoFence:
    """
    Creates a new Versioned, Governance-Compliant Geofence.
    """
    now = time.time()
    zone_id = f"ZONE_{uuid.uuid4().hex[:8].upper()}"
    
    # Calculate Integrity Hash (Merkle-like)
    # Hash(Name + Lat + Lng + Radius + Risk + Reason)
    payload = f"{name}{center.lat}{center.lng}{radius}{risk}{reason}"
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
        reason=reason
    )
    
    # Persist
    try:
        table = get_table('Prahari_GeoFences')
        # Serialize properly (converting floats to Decimal handled by boto3 or helper usually, 
        # but here we rely on simple puts or need helper. For demo we assume happy path or helper exists)
        # We will skip complex decimal conversion here for brevity of the snippet
        # In prod: use `json.loads(fence.json(), parse_float=Decimal)` pattern
        pass 
        # table.put_item(Item=json.loads(fence.json())) 
        
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

def expire_geofence(zone_id: str, actor_id: str, reason: str):
    """
    Expire a geofence (Soft Delete).
    """
    global _GEOFENCE_CACHE
    now = time.time()
    
    target = next((f for f in _GEOFENCE_CACHE if f.zone_id == zone_id), None)
    if not target:
        print("Geofence not found for expiry")
        return

    # Update state
    old_hash = target.audit_hash
    target.is_active = False
    target.effective_to = now
    
    # Re-hash for termination event
    payload = f"{target.zone_id}EXPIRED{now}"
    new_hash = hashlib.sha256(payload.encode()).hexdigest()
    
    # Audit
    audit = GeofenceAuditLog(
        log_id=str(uuid.uuid4()),
        zone_id=zone_id,
        action="EXPIRE",
        actor_id=actor_id,
        timestamp=now,
        old_hash=old_hash,
        new_hash=new_hash,
        reason=reason
    )
    log_geofence_audit(audit)
    
    # Refresh cache to filter it out next time? 
    # Or just keep it marked inactive.

def load_geofences():
    """
    Loads geofences from DynamoDB into memory.
    GOVERNANCE UPDATE: Only loads 'Active' and 'Effective' zones.
    """
    global _GEOFENCE_CACHE
    table = get_table('Prahari_GeoFences')
    try:
        response = table.scan()
        items = response.get('Items', [])
        loaded = []
        now = time.time()
        
        for item in items:
            # Parse Dates
            eff_from = float(item.get('effective_from', 0))
            eff_to = float(item.get('effective_to', 0)) if item.get('effective_to') else None
            is_active = item.get('is_active', True)
            
            # Governance Filter
            if not is_active: continue
            if now < eff_from: continue
            if eff_to and now > eff_to: continue
            
            loaded.append(GeoFence(
                zone_id=item['zone_id'],
                name=item['name'],
                risk_level=item['risk_level'],
                center=GeoPoint(lat=float(item['center']['lat']), lng=float(item['center']['lng'])),
                radius_meters=float(item['radius_meters']),
                description=item.get('description', ""),
                version=int(item.get('version', 1)),
                approved_by=item.get('approved_by', 'SYSTEM'),
                audit_hash=item.get('audit_hash', '')
            ))
        _GEOFENCE_CACHE = loaded
        print(f"Loaded {len(loaded)} ACTIVE Gov-Compliant geofences.")
    except Exception as e:
        print(f"Error loading geofences: {e}")
        # Default fallback
        if not _GEOFENCE_CACHE:
            _GEOFENCE_CACHE = [
                GeoFence(
                    zone_id="ZONE_001",
                    name="Tawang Landslide Zone A",
                    risk_level="HIGH",
                    center=GeoPoint(lat=27.5880, lng=91.8620), 
                    radius_meters=150.0,
                    description="High Risk Landslide Area",
                    version=1,
                    approved_by="SYSTEM_INIT",
                    audit_hash="GENESIS_BLOCK"
                )
            ]

def haversine_distance(p1: GeoPoint, p2: GeoPoint) -> float:
    # ... (Standard Haversine) ...
    lon1, lat1, lon2, lat2 = map(math.radians, [p1.lng, p1.lat, p2.lng, p2.lat])
    dlon = lon2 - lon1 
    dlat = lat2 - lat1 
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a)) 
    r = 6371000 
    return c * r

def check_geofence_breach(location: GeoPoint) -> Optional[GeoFence]:
    """
    Hybrid Check:
    1. Polygon Check (Static)
    2. Radius Check (Dynamic Governance Cache)
    """
    # 1. Polygon Check
    if RED_ZONE_TAWANG.contains(location.lat, location.lng):
        return GeoFence(
            zone_id="POLY_RED_01",
            name="Restricted Border Zone (Polygon)",
            risk_level="HIGH",
            center=location, 
            radius_meters=0.0,
            description="Geospatial Polygon Breach",
            approved_by="MILITARY_COMMAND"
        )

    # 2. Circular Check
    if not _GEOFENCE_CACHE:
        load_geofences()

    for fence in _GEOFENCE_CACHE:
        dist = haversine_distance(location, fence.center)
        if dist <= fence.radius_meters:
            return fence
    return None
