import math
from typing import List, Optional
from app.models import GeoPoint, GeoFence
from app.services.db import get_table

# Cache for geofences to avoid hitting DB every second (Simulated for Lambda state)
_GEOFENCE_CACHE: List[GeoFence] = []

def load_geofences():
    """
    Loads geofences from DynamoDB into memory.
    In production, this might verify cache validity or use a specialized geo-index.
    """
    global _GEOFENCE_CACHE
    table = get_table('Prahari_GeoFences')
    try:
        response = table.scan()
        items = response.get('Items', [])
        loaded = []
        for item in items:
            # DynamoDB scan returns Decimals, need to convert if strictly using float in pydantic
            # Boto3 Table resource usually converts to native types automatically for high-level
            # But let's be safe.
            loaded.append(GeoFence(
                zone_id=item['zone_id'],
                name=item['name'],
                risk_level=item['risk_level'],
                center=GeoPoint(lat=float(item['center']['lat']), lng=float(item['center']['lng'])), # Assuming stored as Map
                radius_meters=float(item['radius_meters']),
                description=item.get('description', "")
            ))
        _GEOFENCE_CACHE = loaded
        print(f"Loaded {len(loaded)} geofences into cache.")
    except Exception as e:
        print(f"Error loading geofences: {e}")
        # seed dummy data if empty for demo
        if not _GEOFENCE_CACHE:
             _GEOFENCE_CACHE = [
                 GeoFence(
                     zone_id="ZONE_001",
                     name="Landslide Area X",
                     risk_level="HIGH",
                     center=GeoPoint(lat=27.586, lng=91.860), # Approx Tawang region
                     radius_meters=500.0,
                     description="Test Red Zone"
                 )
             ]

def haversine_distance(p1: GeoPoint, p2: GeoPoint) -> float:
    """
    Calculate the great circle distance between two points 
    on the earth (specified in decimal degrees)
    """
    # convert decimal degrees to radians 
    lon1, lat1, lon2, lat2 = map(math.radians, [p1.lng, p1.lat, p2.lng, p2.lat])

    # haversine formula 
    dlon = lon2 - lon1 
    dlat = lat2 - lat1 
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a)) 
    r = 6371000 # Radius of earth in meters.
    return c * r

def check_geofence_breach(location: GeoPoint) -> Optional[GeoFence]:
    """
    Checks if the given location is inside any Restricted GeoFence.
    Returns the GeoFence if breached, else None.
    """
    if not _GEOFENCE_CACHE:
        load_geofences()

    for fence in _GEOFENCE_CACHE:
        dist = haversine_distance(location, fence.center)
        if dist <= fence.radius_meters:
            return fence
    return None
