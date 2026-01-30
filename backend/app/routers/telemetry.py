from fastapi import APIRouter, BackgroundTasks, HTTPException
from app.models import TelemetryData, Alert, AlertType, SafetyStatus
from app.services.db import get_table
from app.services.geofence import check_geofence_breach
from app.services.anomaly_detection import detect_anomalies
from app.services.websocket import notify_alert
from decimal import Decimal
import uuid
import time
from app.core.shared_state import LATEST_POSITIONS, KALMAN_STATES
from app.services.identity import get_permit_info

router = APIRouter()

from app.services.websocket import notify_alert, broadcast_telemetry

router = APIRouter()

async def process_risk_and_db(data: TelemetryData):
    """
    SLOW PATH: Background task for heavy analytics, geofencing checks, and persistence.
    Alerts generated here are pushed via WS separately.
    """
    alerts_to_trigger = []
    
    # Identity Verification (Blockchain Bridge)
    permit_str = get_permit_info(data.did)

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
            message=f"Alert: DID {data.did} has entered restricted zone: {breached_zone.name}. {permit_str}"
        ))

    # 2. Check Anomalies (Requires DB History often)
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
            message=f"Alert: DID {data.did} anomaly detected: {anomaly_type.value}. {permit_str}"
        )
        alerts_to_trigger.append(new_alert)

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
            message=f"Alert: DID {data.did} SOS Panic Button Triggered! {permit_str}"
        ))

    # 4. Save Telemetry to DynamoDB (Persistence)
    try:
        t_table = get_table('Prahari_Telemetry')
        item = data.model_dump()
        item['location'] = {k: Decimal(str(v)) for k, v in item['location'].items()}
        item['timestamp'] = Decimal(str(item['timestamp'])) 
        item['speed'] = Decimal(str(item['speed']))
        item['heading'] = Decimal(str(item['heading']))
        item['battery_level'] = Decimal(str(item['battery_level']))
        t_table.put_item(Item=item)
    except Exception as e:
        print(f"DB Error (Telemetry): {e}")

    # 5. Save Alerts
    if alerts_to_trigger:
        try:
            a_table = get_table('Prahari_Alerts')
            for alert in alerts_to_trigger:
                a_item = alert.model_dump()
                a_item['location'] = {k: Decimal(str(v)) for k, v in a_item['location'].items()}
                a_item['timestamp'] = Decimal(str(a_item['timestamp']))
                a_table.put_item(Item=a_item)
                print(f"ALERT TRIGGERED: {alert.message}")
        except Exception as e:
            print(f"DB Error (Alerts): {e}")

from app.engine import SentinelAI
from app.services.websocket import notify_alert, broadcast_telemetry

# ... (Previous imports and functions)

from fastapi import Depends, Security, HTTPException
from fastapi.security.api_key import APIKeyHeader
from app.core.config import settings

api_key_header = APIKeyHeader(name="x-api-key", auto_error=False)

async def verify_api_key(api_key: str = Security(api_key_header)):
    """
    Production Security: Enforce API Key on Critical Endpoints.
    """
    if api_key == settings.AUTH_API_KEY:
        return api_key
    else:
        # Allow dev mode bypass if needed, or fail hard
        raise HTTPException(status_code=403, detail="Could not validate credentials")


@router.post("/telemetry", dependencies=[Depends(verify_api_key)])
async def ingest_telemetry(data: TelemetryData, background_tasks: BackgroundTasks):
    """
    FAST PATH: Production-grade ingestion.
    1. Kalman Smoothing.
    2. Cache Update.
    3. AI Risk Calculation (Inline/Fast).
    4. WS Broadcast (Smart Payload).
    5. Persistence (Async).
    """
    
    # --- 1. KALMAN FILTERING (Signal Smoothing) ---
    if data.device_id not in KALMAN_STATES:
        KALMAN_STATES[data.device_id] = {
            'x': [data.location.lat, data.location.lng, 0, 0], 
            'P': [[1,0,0,0], [0,1,0,0], [0,0,1000,0], [0,0,0,1000]],
            'last_ts': data.timestamp
        }
    
    kf = KALMAN_STATES[data.device_id]
    dt = data.timestamp - kf['last_ts']
    if dt <= 0: dt = 0.01 
    
    # Predict & Update (Standard EKF Logic simplification)
    kf['x'][0] += kf['x'][2] * dt
    kf['x'][1] += kf['x'][3] * dt
    
    z = [data.location.lat, data.location.lng]
    y = [z[0] - kf['x'][0], z[1] - kf['x'][1]]
    K = 0.6 
    
    kf['x'][0] += K * y[0]
    kf['x'][1] += K * y[1]
    
    kf['x'][2] = (kf['x'][0] - (kf['x'][0] - K*y[0])) / dt
    kf['x'][3] = (kf['x'][1] - (kf['x'][1] - K*y[1])) / dt

    kf['last_ts'] = data.timestamp
    
    # Overwrite data location with Smoothed Coordinates
    data.location.lat = kf['x'][0]
    data.location.lng = kf['x'][1]
    
    # --- 2. UPDATE CACHE (Fast Read) ---
    LATEST_POSITIONS[data.device_id] = data.model_dump()
    
    # --- 3. AI RISK CALCULATION (Real-Time Brain) ---
    # Now part of the Fast Path
    risk_report = SentinelAI.calculate_risk(data.model_dump(), LATEST_POSITIONS)
    
    # --- 4. BROADCAST (Real-Time + AI Insight) ---
    payload = data.model_dump()
    payload['risk'] = risk_report # Attach the AI score
    await broadcast_telemetry(payload)
    
    # --- 5. OFFLOAD SLOW TASKS ---
    background_tasks.add_task(process_risk_and_db, data)
    
    return {"status": "accepted", "timestamp": data.timestamp, "risk": risk_report}

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
    Hydrates from DynamoDB if cache is empty (server restart).
    """
    # 1. Hydrate Cache if Empty (Persistence reliability)
    if not LATEST_POSITIONS:
        try:
            print("CACHE HYDRATION: Fetching latest state from DynamoDB...")
            t_table = get_table('Prahari_Telemetry')
            response = t_table.scan(Limit=2000)
            items = response.get('Items', [])
            
            for item in items:
                try:
                    dev_id = item['device_id']
                    ts = float(item['timestamp'])
                    
                    # Convert DynamoDB Decimals to Native Types
                    native_item = {
                        "device_id": dev_id,
                        "did": item.get('did', 'unknown'),
                        "timestamp": ts,
                        "location": {
                            "lat": float(item['location']['lat']),
                            "lng": float(item['location']['lng'])
                        },
                        "speed": float(item.get('speed', 0)),
                        "heading": float(item.get('heading', 0)),
                        "battery_level": float(item.get('battery_level', 100)),
                        "is_panic": item.get('is_panic', False)
                    }
                    
                    # Store only if newer than what we have (or if we have nothing)
                    if dev_id not in LATEST_POSITIONS or ts > LATEST_POSITIONS[dev_id]['timestamp']:
                        LATEST_POSITIONS[dev_id] = native_item
                        
                except Exception as inner_e:
                    continue # Skip malformed items
                    
            print(f"CACHE HYDRATION: Restored {len(LATEST_POSITIONS)} active devices.")
            
        except Exception as e:
            print(f"Cache Hydration Failed: {e}")
            return []

    return list(LATEST_POSITIONS.values())

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
