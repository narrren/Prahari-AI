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
    
    # 1. Fall Detection / Sudden Velocity Drop (Simulated Rule)
    # If speed drops from > 10m/s to 0 instantly (hard to detect without history in this payload)
    # But if client sends is_panic, that's SOS.
    # We will trust the ML model running on the Edge (Mobile) or this mock.
    # For now, let's assume if speed is anomalously high (e.g. GPS drift) or we can implement more complex logic later.
    
    # 2. Inactivity Detection
    # Fetch last known state
    table = get_table('Prahari_Telemetry')
    
    # Query for the LAST telemetry item.
    # Since we use composite key (device_id, timestamp), we can query "Limit=1, ScanIndexForward=False"
    try:
        response = table.query(
            KeyConditionExpression=boto3.dynamodb.conditions.Key('device_id').eq(data.device_id),
            Limit=1,
            ScanIndexForward=False # Descending order
        )
        items = response.get('Items', [])
        if items:
            last_item = items[0]
            last_time = float(last_item['timestamp'])
            last_lat = float(last_item['location']['lat'])
            last_lng = float(last_item['location']['lng'])
            
            # check inactivity
            time_diff = data.timestamp - last_time
            
            # Simple distance check to see if they haven't moved
            # (In a real app, we'd use haversine)
            # If time diff > threshold AND distance is negligible
            if time_diff > settings.INACTIVITY_THRESHOLD_SECONDS:
                 # Calculate distance... if < 10 meters, it's inactivity.
                 # Importing locally to avoid circulars if any (though clear here)
                 from app.services.geofence import haversine_distance, GeoPoint
                 dist = haversine_distance(data.location, GeoPoint(lat=last_lat, lng=last_lng))
                 if dist < 20.0:
                     anomalies.append(AlertType.INACTIVITY)

    except Exception as e:
        print(f"Error checking history for anomaly: {e}")
        pass

    return anomalies
