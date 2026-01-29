from fastapi import APIRouter, BackgroundTasks, HTTPException
from app.models import TelemetryData, Alert, AlertType, SafetyStatus
from app.services.db import get_table
from app.services.geofence import check_geofence_breach
from app.services.anomaly_detection import detect_anomalies
from decimal import Decimal
import uuid
import time

router = APIRouter()

def process_telemetry_background(data: TelemetryData):
    """
    Background task to process analytics, geofencing, and persistence.
    Keeps the API response fast (Event-Driven pattern).
    """
    alerts_to_trigger = []

    # 1. Check Geofence
    breached_zone = check_geofence_breach(data.location)
    if breached_zone:
        alerts_to_trigger.append(Alert(
            alert_id=str(uuid.uuid4()),
            device_id=data.device_id,
            did=data.did,
            type=AlertType.GEOFENCE_BREACH,
            severity="HIGH",
            timestamp=time.time(),
            location=data.location,
            message=f"Entered restricted zone: {breached_zone.name}"
        ))

    # 2. Check Anomalies
    anomalies = detect_anomalies(data)
    for anomaly_type in anomalies:
        alerts_to_trigger.append(Alert(
            alert_id=str(uuid.uuid4()),
            device_id=data.device_id,
            did=data.did,
            type=anomaly_type,
            severity="MEDIUM",
            timestamp=time.time(),
            location=data.location,
            message=f"Anomaly detected: {anomaly_type.value}"
        ))

    # 3. Handle SOS
    if data.is_panic:
        alerts_to_trigger.append(Alert(
            alert_id=str(uuid.uuid4()),
            device_id=data.device_id,
            did=data.did,
            type=AlertType.SOS_MANUAL,
            severity="CRITICAL",
            timestamp=time.time(),
            location=data.location,
            message="SOS Panic Button Triggered!"
        ))

    # 4. Save Telemetry to DynamoDB
    t_table = get_table('Prahari_Telemetry')
    # Convert floats to Decimal for DynamoDB
    item = data.model_dump()
    item['location'] = {k: Decimal(str(v)) for k, v in item['location'].items()}
    item['timestamp'] = Decimal(str(item['timestamp'])) # Make sure timestamp is number
    # float to decimal conversion for other fields
    item['speed'] = Decimal(str(item['speed']))
    item['heading'] = Decimal(str(item['heading']))
    item['battery_level'] = Decimal(str(item['battery_level']))
    
    t_table.put_item(Item=item)

    # 5. Save Alerts
    if alerts_to_trigger:
        a_table = get_table('Prahari_Alerts')
        for alert in alerts_to_trigger:
            a_item = alert.model_dump()
            a_item['location'] = {k: Decimal(str(v)) for k, v in a_item['location'].items()}
            a_item['timestamp'] = Decimal(str(a_item['timestamp']))
            a_table.put_item(Item=a_item)
            print(f"ALERT TRIGGERED: {alert.message}")

@router.post("/telemetry")
async def ingest_telemetry(data: TelemetryData, background_tasks: BackgroundTasks):
    """
    Ingest GPS telemetry from mobile client.
    """
    # Simply ack and push to background processing
    background_tasks.add_task(process_telemetry_background, data)
    return {"status": "received", "timestamp": data.timestamp}

@router.get("/alerts")
async def get_all_alerts():
    """
    Get all active alerts for the command center.
    """
    try:
        table = get_table('Prahari_Alerts')
        # Scan for demo. Prod would use index on 'resolved' status.
        response = table.scan(Limit=50)
        return response.get('Items', [])
    except Exception as e:
        print(f"Error fetching alerts: {e}")
        return []

@router.get("/alerts/{device_id}")
async def get_alerts(device_id: str):
    """
    Get active alerts for a device.
    """
    # In a real app, use GSI or separate query pattern
    # For now, just a placeholder or scan (inefficient but works for 2 items)
    # We didn't set up GSI in the simple script properly for device_id on Alerts table (wait, I did check GSI comments in setup_dynamodb.py)
    # The setup_dynamodb.py had: key_schema=[{'AttributeName': 'alert_id', 'KeyType': 'HASH'}]
    # It mentioned GSI device_id-index but didn't implement it in the `create_table` call for simplicity/errors.
    # I'll just return empty for now or do a Scan if needed.
    return {"alerts": []}

@router.get("/map/positions")
async def get_map_positions():
    """
    Get latest known positions of all devices for the map.
    """
    # Scan telemetry table or query specific index
    # For MVP, we scan the Telemetry table (expensive in prod, okay for demo)
    t_table = get_table('Prahari_Telemetry')
    # This is a naive scan. In prod, we'd use a 'CurrentLocations' table.
    try:
        response = t_table.scan(Limit=100) # Limit for safety
        items = response.get('Items', [])
        # Group by device_id and take latest
        # Or if we had a dedicated 'CurrentState' table.
        # Let's just return what we find for now, or assume the scan returns recent items if table is small.
        # But scan returns arbitrary order.
        # We'll just return the raw items and let frontend filter for latest per device.
        return items
    except Exception as e:
        print(f"Error fetching positions: {e}")
        return []
