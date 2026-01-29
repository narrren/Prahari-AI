from app.models import TelemetryData, AlertType
from app.services.db import get_table
from app.core.config import settings
import boto3
import time
from decimal import Decimal

def detect_anomalies(data: TelemetryData) -> list[AlertType]:
    """
    Analyzes telemetry for anomalies.
    Returns a list of detected AlertTypes.
    """
    anomalies = []
    
    anomalies = []
    
    # --- PHASE 3: WEIGHTED AI RISK ENGINE (The "Brain") ---
    # Formula: Risk = (Static * 0.3) + (Env * 0.4) + (Behavior * 0.3)
    
    # 1. Static Risk (Geofence Context)
    # Check if inside a High Risk Zone
    from app.services.geofence import check_geofence_breach, _GEOFENCE_CACHE
    # We re-check here or assume caller did? Let's check to get the Risk Level.
    zone = check_geofence_breach(data.location)
    static_risk = 0.0
    if zone:
        if zone.risk_level == "HIGH": static_risk = 100.0
        elif zone.risk_level == "MEDIUM": static_risk = 50.0
        else: static_risk = 10.0
    else:
        static_risk = 0.0 # Green Zone
        
    # 2. Environmental Risk (Time + Weather)
    current_hour = time.localtime(data.timestamp).tm_hour
    is_night = current_hour < 6 or current_hour > 18
    # Mock Weather: Random storm in Tawang?
    # Let's assume CLEAR for now, unless Risk Engine script injects it.
    env_risk = 80.0 if is_night else 20.0
    
    # 3. Behavioral Anomaly (Velocity / Stagnation)
    behavioral_anomaly = 0.0
    
    # Check Inactivity (Simulating "0 velocity for > 20 mins")
    table = get_table('Prahari_Telemetry')
    try:
        response = table.query(
            KeyConditionExpression=boto3.dynamodb.conditions.Key('device_id').eq(data.device_id),
            Limit=1,
            ScanIndexForward=False 
        )
        items = response.get('Items', [])
        if items:
            last_item = items[0]
            last_time = float(last_item['timestamp'])
            last_lat = float(last_item['location']['lat'])
            last_lng = float(last_item['location']['lng'])
            
            from app.services.geofence import haversine_distance, GeoPoint
            dist = haversine_distance(data.location, GeoPoint(lat=last_lat, lng=last_lng))
            time_diff = data.timestamp - last_time

            if time_diff > settings.INACTIVITY_THRESHOLD_SECONDS: # > 1200 normally
                 if dist < 20.0:
                     behavioral_anomaly = 100.0 # High Probability of Injury
            
            # Additional Velo check
            if hasattr(data, 'speed') and data.speed > 80.0: # Impossible human speed
                behavioral_anomaly = 90.0
                
    except Exception as e:
        print(f"Error checking history: {e}")

    if data.is_panic:
        behavioral_anomaly = 100.0

    # --- THE ALGORITHM ---
    final_risk_score = (static_risk * 0.3) + (env_risk * 0.4) + (behavioral_anomaly * 0.3)
    
    # print(f"AI BRAIN: Device {data.device_id} | Risk Score: {final_risk_score:.2f} | Context: [S:{static_risk}, E:{env_risk}, B:{behavioral_anomaly}]")
    
    # Thresholding Logic
    if final_risk_score > 80.0:
        anomalies.append(AlertType.SOS) # or CRITICAL_RISK 
    elif final_risk_score > 60.0:
        anomalies.append(AlertType.GEOFENCE_BREACH) # General Danger
    elif behavioral_anomaly >= 100.0:
        anomalies.append(AlertType.INACTIVITY)

    return anomalies
