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
    
    # --- CONTEXTUAL AI RISK SCORING (Simulated Random Forest Logic) ---
    # In a real deployment, this would use sklearn/loading a .pkl model.
    # Features: [TimeOfDay, WeatherCondition, TerrainDifficulty, UserHistory]
    
    current_hour = time.localtime(data.timestamp).tm_hour
    is_night_time = current_hour < 6 or current_hour > 18
    weather_condition = "CLEAR" # Mock data source
    
    # Base Probability of Incident
    risk_score = 0.1 
    
    if is_night_time:
        risk_score += 0.4  # Night trekking significantly increases risk
    
    if data.is_panic:
        risk_score = 1.0   # Immediate Certainty
        anomalies.append(AlertType.SOS)

    # 1. Dead Man's Switch / Inactivity Logic
    # ---------------------------------------
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
            
            # Importing locally to avoid circulars
            from app.services.geofence import haversine_distance, GeoPoint
            dist = haversine_distance(data.location, GeoPoint(lat=last_lat, lng=last_lng))
            time_diff = data.timestamp - last_time

            # If user hasn't moved for X time
            if time_diff > settings.INACTIVITY_THRESHOLD_SECONDS:
                 if dist < 20.0:
                     # High Risk Context: Inactivity at NIGHT is Critical, Day is Warning
                     if risk_score > 0.4:
                         anomalies.append(AlertType.Unconscious) # Custom high severity
                     else:
                         anomalies.append(AlertType.INACTIVITY)
    except Exception as e:
        print(f"Error checking history for anomaly: {e}")

    # 2. Route Deviation with Risk Context
    # ------------------------------------
    # (Simplified: logic assumes we have a 'route' - for now we use geofence logic elsewhere)
    # If the user is in a 'High Risk Zone' (checked in geofence service) + High Risk Score
    # We escalate the alert severity.
    
    return anomalies
