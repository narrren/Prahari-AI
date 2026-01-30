from fastapi import APIRouter, BackgroundTasks, HTTPException
from app.models import TelemetryData, Alert, AlertType, SafetyStatus
from app.services.db import get_table
from app.services.geofence import check_geofence_breach
from app.services.anomaly_detection import detect_anomalies
from app.services.websocket import notify_alert
from decimal import Decimal
import uuid
import time

router = APIRouter()

async def process_telemetry_background(data: TelemetryData):
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
        severity = "MEDIUM"
        if anomaly_type == AlertType.SOS: severity = "CRITICAL"
        if anomaly_type == AlertType.Unconscious: severity = "CRITICAL"
        
        new_alert = Alert(
            alert_id=str(uuid.uuid4()),
            device_id=data.device_id,
            did=data.did,
            type=anomaly_type,
            severity=severity,
            timestamp=time.time(),
            location=data.location,
            message=f"Anomaly detected: {anomaly_type.value}"
        )
        alerts_to_trigger.append(new_alert)

        # TRIGGER WEBSOCKET ALARM IF CRITICAL
        if severity == "CRITICAL" or anomaly_type == AlertType.SOS:
            await notify_alert(new_alert.model_dump())


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

    # --- KALMAN FILTERING (Signal Smoothing) ---
    # In a real serverless architecture, this state would be stored in Redis/ElastiCache.
    # For this localized demo, we use an in-memory dictionary.
    global _kalman_states
    if '_kalman_states' not in globals():
        _kalman_states = {}
    
    # Initialize state for this device if new
    if data.device_id not in _kalman_states:
        # State: [lat, lng, lat_v, lng_v]
        # P: Covariance matrix (uncertainty)
        _kalman_states[data.device_id] = {
            'x': [data.location.lat, data.location.lng, 0, 0], 
            'P': [[1,0,0,0], [0,1,0,0], [0,0,1000,0], [0,0,0,1000]],
            'last_ts': data.timestamp
        }
    
    kf = _kalman_states[data.device_id]
    dt = data.timestamp - kf['last_ts']
    if dt <= 0: dt = 0.01 # Avoid zero division or stale timestamps
    
    # 1. Predict (Process Model)
    # New Position = Old Position + Velocity * dt
    kf['x'][0] += kf['x'][2] * dt
    kf['x'][1] += kf['x'][3] * dt
    # Covariance increases/dilutes over time (Entropy)
    # Simple addition for demo purposes
    
    # 2. Update (Measurement)
    # Innovation (Observed - Predicted)
    z = [data.location.lat, data.location.lng]
    y = [z[0] - kf['x'][0], z[1] - kf['x'][1]]
    
    # Kalman Gain (Simplified for GPS: ~0.5 means trust sensor 50%, model 50%)
    # Dynamic gain based on 'is_panic' or velocity could be cool.
    # Let's use a static high-smoothing factor for a "Cinematic" track.
    K = 0.6 
    
    # New Estimate = Predicted + Gain * Innovation
    kf['x'][0] += K * y[0]
    kf['x'][1] += K * y[1]
    
    # Update Velocity estimates for next prediction
    kf['x'][2] = (kf['x'][0] - (kf['x'][0] - K*y[0])) / dt # Rough velocity inference
    kf['x'][3] = (kf['x'][1] - (kf['x'][1] - K*y[1])) / dt

    kf['last_ts'] = data.timestamp
    
    # ... (After Kalman Logic) ...
    # OVERWRITE Payload with Smoothed Data
    # accurate for Geofencing/Display
    original_data = data.model_copy()
    data.location.lat = kf['x'][0]
    data.location.lng = kf['x'][1]
    
    # --- REAL-TIME CACHE UPDATE (Redis Pattern) ---
    # Update the cache immediately so the Map sees it NOW.
    global _LATEST_POSITIONS
    if '_LATEST_POSITIONS' not in globals():
        _LATEST_POSITIONS = {}
    
    # Store with native types (FastAPI handles JSON serialization)
    _LATEST_POSITIONS[data.device_id] = data.model_dump()
    
    # log difference for demo
    # print(f"Raw: {original_data.location} -> Smoothed: {data.location}")

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
    return {"alerts": []}

@router.get("/map/positions")
async def get_map_positions():
    """
    Get latest known positions of all devices for the map.
    Serves from In-Memory Cache (Redis equivalent) for real-time performance.
    """
    global _LATEST_POSITIONS
    if '_LATEST_POSITIONS' not in globals():
        _LATEST_POSITIONS = {}
    
    return list(_LATEST_POSITIONS.values())

@router.get("/telemetry/history/{device_id}")
async def get_device_history(device_id: str, hours: int = 4):
    """
    Fetch historical telemetry for 'Breadcrumbs' (last N hours).
    Efficiently queries DynamoDB partition key.
    """
    import boto3 
    from boto3.dynamodb.conditions import Key
    
    t_table = get_table('Prahari_Telemetry')
    cutoff_time = Decimal(str(time.time() - (hours * 3600)))
    
    try:
        response = t_table.query(
            KeyConditionExpression=Key('device_id').eq(device_id) & Key('timestamp').gte(cutoff_time),
            ScanIndexForward=True # Ascending (oldest first)
        )
        return response.get('Items', [])
    except Exception as e:
        print(f"Error fetching history for {device_id}: {e}")
        return []
