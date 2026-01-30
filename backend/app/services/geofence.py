import math
from typing import List, Optional
from app.models import GeoPoint, GeoFence
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
# Coordinates roughly match the "Red" simulation area
RED_ZONE_TAWANG = PolygonZone([
    (27.5890, 91.8610), 
    (27.5870, 91.8630), 
    (27.5870, 91.8610), 
    (27.5890, 91.8630) # Rough box around the hotspot
])

# Also keep the cache for standard circular zones if needed
_GEOFENCE_CACHE: List[GeoFence] = []

def load_geofences():
    """
    Loads geofences from DynamoDB into memory.
    """
    global _GEOFENCE_CACHE
    table = get_table('Prahari_GeoFences')
    try:
        response = table.scan()
        items = response.get('Items', [])
        loaded = []
        for item in items:
            loaded.append(GeoFence(
                zone_id=item['zone_id'],
                name=item['name'],
                risk_level=item['risk_level'],
                center=GeoPoint(lat=float(item['center']['lat']), lng=float(item['center']['lng'])),
                radius_meters=float(item['radius_meters']),
                description=item.get('description', "")
            ))
        _GEOFENCE_CACHE = loaded
        print(f"Loaded {len(loaded)} geofences into cache.")
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
                    description="High Risk Landslide Area"
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
    1. Check Polygon (The "Shape")
    2. Check Radius (The "Legacy/Simple" Zones)
    """
    # 1. Polygon Check (The 'Shapely' Logic)
    # If inside the hardcoded polygon, return a mock HIGH risk fence
    if RED_ZONE_TAWANG.contains(location.lat, location.lng):
        return GeoFence(
            zone_id="POLY_RED_01",
            name="Restricted Border Zone (Polygon)",
            risk_level="HIGH",
            center=location, # Dynamic
            radius_meters=0.0,
            description="Geospatial Polygon Breach"
        )

    # 2. Circular Check
    if not _GEOFENCE_CACHE:
        load_geofences()

    for fence in _GEOFENCE_CACHE:
        dist = haversine_distance(location, fence.center)
        if dist <= fence.radius_meters:
            return fence
    return None
