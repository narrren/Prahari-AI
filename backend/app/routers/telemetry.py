from fastapi import APIRouter, BackgroundTasks, HTTPException, Header
from app.models import TelemetryData, Alert, AlertType, SafetyStatus
from app.services.db import get_table
from app.services.geofence import check_geofence_breach
from app.services.anomaly_detection import detect_anomalies
from app.services.websocket import notify_alert, broadcast_telemetry
from decimal import Decimal
import uuid
import time
from app.core.shared_state import LATEST_POSITIONS, KALMAN_STATES, LATEST_ALERTS
from app.services.identity import get_permit_info

from app.engine import SentinelAI
from fastapi import Depends, Security
from fastapi.security.api_key import APIKeyHeader
from app.core.config import settings

router = APIRouter()

# --- ALERT LIFECYCLE HELPERS ---
def upsert_alert(device_id: str, alert_type: AlertType, severity: str, msg: str, location: dict):
    """
    Stateful Alert Logic: Prevent fatigue by updating existing active alerts instead of spanning new ones.
    """
    alert_key = f"{device_id}_{alert_type.value}"
    existing = LATEST_ALERTS.get(alert_key)
    
    current_time = time.time()
    
    if existing and existing['status'] != 'RESOLVED':
        # UPDATE EXISTING
        existing['timestamp'] = current_time # refresh last seen
        existing['location'] = location # update location
        # If severity increases?
        if severity == 'CRITICAL' and existing['severity'] != 'CRITICAL':
            existing['severity'] = 'CRITICAL'
            existing['message'] = msg
            # Notify again if escalated
            return existing, True 
        return existing, False # No new notification needed
        
    else:
        # CREATE NEW
        new_alert = Alert(
            alert_id=str(uuid.uuid4()),
            device_id=device_id,
            did="unknown", # Filled by caller
            type=alert_type,
            severity=severity,
            timestamp=current_time,
            location=location,
            message=msg,
            status="DETECTED" # Initial State
        )
        alert_dict = new_alert.model_dump()
        LATEST_ALERTS[alert_key] = alert_dict
        return alert_dict, True

async def process_risk_and_db(data: TelemetryData):
    """
    SLOW PATH: Background task for heavy analytics, geofencing checks, and persistence.
    Alerts generated here are pushed via WS separately.
    """
    affected_alerts = []
    
    # Identity Verification (Blockchain Bridge)
    permit_str = get_permit_info(data.did)

    # 1. Check Geofence
    breached_zone = check_geofence_breach(data.location)
    if breached_zone:
         alert, is_new = upsert_alert(
             data.device_id, 
             AlertType.GEOFENCE_BREACH, 
             "HIGH", 
             f"Alert: DID {data.did} restricted zone breach: {breached_zone.name}. {permit_str}",
             data.location.model_dump()
         )
         alert['did'] = data.did
         if is_new: affected_alerts.append(alert)

    # 2. Check Anomalies (Requires DB History often)
    anomalies = detect_anomalies(data)
    for anomaly_type in anomalies:
        severity = "MEDIUM"
        if anomaly_type == AlertType.SOS: severity = "CRITICAL"
        if anomaly_type == AlertType.Unconscious: severity = "CRITICAL"
        
        alert, is_new = upsert_alert(
            data.device_id,
            anomaly_type,
            severity,
            f"Alert: DID {data.did} anomaly: {anomaly_type.value}. {permit_str}",
            data.location.model_dump()
        )
        alert['did'] = data.did
        if is_new: affected_alerts.append(alert)

    # 3. Handle SOS
    if data.is_panic:
         alert, is_new = upsert_alert(
            data.device_id,
            AlertType.SOS_MANUAL,
            "CRITICAL",
            f"Alert: DID {data.did} SOS Panic Button Triggered! {permit_str}",
            data.location.model_dump()
        )
         alert['did'] = data.did
         if is_new: affected_alerts.append(alert)

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

    # 5. Notify & Save Alerts
    for alert_dict in affected_alerts:
        await notify_alert(alert_dict)
        # We can also persist to DB here if needed
        # For simplicity, we persist mostly on resolved in the lifecycle, or periodical snapshot

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
    Get all active alerts from memory (Operational View).
    """
    return list(LATEST_ALERTS.values())

@router.patch("/alerts/{alert_id}/acknowledge")
async def acknowledge_alert(
    alert_id: str,
    x_actor_id: str = Header("operator", alias="X-Actor-ID")
):
    # Find alert in cache (by ID)
    target_key = None
    for k, v in LATEST_ALERTS.items():
        if v['alert_id'] == alert_id:
            target_key = k
            break
            
    if target_key:
        LATEST_ALERTS[target_key]['status'] = 'ACKNOWLEDGED'
        LATEST_ALERTS[target_key]['ack_by'] = x_actor_id
        LATEST_ALERTS[target_key]['ack_time'] = time.time()
        print(f"ALERT_OP: Alert {alert_id} ACKNOWLEDGED by {x_actor_id}")
        return {"status": "success", "alert": LATEST_ALERTS[target_key]}
    
    raise HTTPException(status_code=404, detail="Alert not found active")

@router.patch("/alerts/{alert_id}/resolve")
async def resolve_alert(
    alert_id: str,
    x_actor_id: str = Header("supervisor", alias="X-Actor-ID")
):
    target_key = None
    for k, v in LATEST_ALERTS.items():
        if v['alert_id'] == alert_id:
            target_key = k
            break
            
    if target_key:
        LATEST_ALERTS[target_key]['status'] = 'RESOLVED'
        LATEST_ALERTS[target_key]['resolved_by'] = x_actor_id
        LATEST_ALERTS[target_key]['resolved_time'] = time.time()
        
        # Move to History / Delete from Active Cache to clear clutter
        resolved_alert = LATEST_ALERTS.pop(target_key)
        
        # Persist final state to DB (Todo)
        print(f"ALERT_OP: Alert {alert_id} RESOLVED by {x_actor_id}")
        return {"status": "success", "message": "Alert Resolved and Archived"}
        
    raise HTTPException(status_code=404, detail="Alert not found active")

@router.get("/alerts/{device_id}")
async def get_alerts(device_id: str):
    """
    Get active alerts for a device.
    """
    # Filter LATEST_ALERTS for the specific device_id
    device_alerts = [alert for alert in LATEST_ALERTS.values() if alert['device_id'] == device_id]
    return {"alerts": device_alerts}

@router.get("/map/positions")
async def get_map_positions():
    """
    Get latest known positions of all devices for the map.
    Serves from In-Memory Cache (Redis equivalent) for real-time performance.
    Hydrates from DynamoDB if cache is empty (server restart).
    """
    if not LATEST_POSITIONS:
        from app.core.shared_state import hydrate_cache
        hydrate_cache()

    return list(LATEST_POSITIONS.values())

@router.get("/telemetry/history/{device_id}")
async def get_device_history(device_id: str, hours: int = 4):
    """
    Fetch historical telemetry for 'Breadcrumbs' (last N hours).
    Efficiently queries DynamoDB partition key.
    """
    from boto3.dynamodb.conditions import Key
    
    t_table = get_table('Prahari_Telemetry')
    cutoff_time = Decimal(str(time.time() - (hours * 3600)))
    
    try:
        response = t_table.query(
            KeyConditionExpression=Key('device_id').eq(device_id) & Key('timestamp').gte(cutoff_time),
            ScanIndexForward=True # Ascending (oldest first)
        )
        items = response.get('Items', [])
        
        # Serialization Fix: Convert Decimals to Float/Int
        cleaned_items = []
        for item in items:
            cleaned = {
                "device_id": item['device_id'],
                "timestamp": float(item['timestamp']),
                "location": {
                    "lat": float(item['location']['lat']),
                    "lng": float(item['location']['lng'])
                },
                "speed": float(item.get('speed', 0)),
                "heading": float(item.get('heading', 0)),
                "battery_level": float(item.get('battery_level', 0)),
                "is_panic": item.get('is_panic', False)
            }
            cleaned_items.append(cleaned)
            
        return cleaned_items
        
    except Exception as e:
        print(f"Error fetching history for {device_id}: {e}")
        return []
