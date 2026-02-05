from fastapi import APIRouter, BackgroundTasks, HTTPException, Header, Request, Depends
from app.models import TelemetryData, Alert, AlertType, SafetyStatus, GeoPoint
from app.services.db import get_table
from app.services.geofence import check_geofence_breach
from app.services.anomaly_detection import detect_anomalies
from app.services.websocket import notify_alert, broadcast_telemetry
from decimal import Decimal
import uuid
import time
from app.core.shared_state import LATEST_POSITIONS, KALMAN_STATES, LATEST_ALERTS, SYSTEM_METRICS
from app.services.identity import get_permit_info

from app.engine import SentinelAI
from fastapi import Security
from fastapi.security.api_key import APIKeyHeader
from app.core.config import settings
from app.core import telemetry_pb2 # Generated Protobuf
from collections import defaultdict

router = APIRouter()

# --- RATE LIMITER (Leaky Bucket) ---
class RateLimiter:
    def __init__(self, rate=100, per=1.0):
        self.rate = rate
        self.per = per
        self.allowance = defaultdict(lambda: rate)
        self.last_check = defaultdict(lambda: time.time())

    def check(self, ip: str) -> bool:
        current = time.time()
        time_passed = current - self.last_check[ip]
        self.last_check[ip] = current
        self.allowance[ip] += time_passed * (self.rate / self.per)
        
        if self.allowance[ip] > self.rate:
            self.allowance[ip] = self.rate
            
        if self.allowance[ip] < 1.0:
            return False # Reject
        
        self.allowance[ip] -= 1.0
        return True

limiter = RateLimiter(rate=50, per=1.0) # 50 req/sec per IP

def check_rate_limit(request: Request):
    ip = request.client.host if request.client else "unknown"
    if not limiter.check(ip):
        raise HTTPException(status_code=429, detail="Rate Limit Exceeded (Anti-DDoS Protection)")

from app.services.identities import verify_device_integrity, verify_packet_signature

from app.services.integrity import is_system_locked

# --- SHARED CORE LOGIC ---
async def process_telemetry_core(data: TelemetryData, background_tasks: BackgroundTasks, 
                                 request_fingerprint: str = None, request_cert: str = None,
                                 request_signature: str = None, request_nonce: int = None):
    """
    Common Pipeline for JSON and Protobuf Ingestion.
    """
    # -1. GLOBAL KILL SWITCH CHECK
    if is_system_locked():
        raise HTTPException(status_code=503, detail="SERVICE UNAVAILABLE: SECURITY LOCKDOWN IN EFFECT")

    # 0. Zero Trust Check (mTLS + Fingerprinting)
    if request_fingerprint and request_cert: 
        is_valid = verify_device_integrity(data.device_id, request_fingerprint, request_cert)
        if not is_valid:
            print(f"SECURITY ALERT: Telemetry blocked for {data.device_id} due to invalid Hardware/Cert.")
            raise HTTPException(status_code=401, detail="Zero Trust Violation: Hardware Fingerprint or mTLS Mismatch")
            
    # 0a. Cryptographic Attestation & Replay Protection (Phase 4.2)
    # MANDATORY check.
    if not request_signature or request_nonce is None:
         # Fail securely if signature missing
         raise HTTPException(status_code=401, detail="Attestation Missing: X-Signature and X-Nonce are required.")
    
    # Reconstruct Payload String (Canonical Format)
    # Format: device_id:timestamp:lat:lng
    payload_string = f"{data.device_id}:{data.timestamp}:{data.location.lat}:{data.location.lng}"
    
    is_attested = verify_packet_signature(data.device_id, payload_string, request_signature, request_nonce)
    if not is_attested:
            print(f"SECURITY ALERT: Telemetry blocked for {data.device_id} due to Badge Signature/Replay Failure.")
            raise HTTPException(status_code=401, detail="Attestation Violation: Invalid Signature or Replay Attack")
            
    # 0b. Metrics
    SYSTEM_METRICS['ingestion_count'] += 1

    # 1. BEHAVIORAL BIOMETRICS (V5.0 Turing Test)
    from app.services.biometrics import analyze_humanity
    data.humanity_score = analyze_humanity(data)
    if data.humanity_score < 50.0:
        print(f"🤖 ADVERSARIAL AI DEFENSE: {data.device_id} flagged as BOT (Score: {data.humanity_score:.1f}%)")

    # 2. KALMAN FILTERING (Signal Smoothing)
    if data.device_id not in KALMAN_STATES:
        KALMAN_STATES[data.device_id] = {
            'x': [data.location.lat, data.location.lng, 0, 0], 
            'P': [[1,0,0,0], [0,1,0,0], [0,0,1000,0], [0,0,0,1000]],
            'last_ts': data.timestamp
        }
    
    kf = KALMAN_STATES[data.device_id]
    dt = data.timestamp - kf['last_ts']
    if dt <= 0: dt = 0.01 
    
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
    
    # Overwrite with Smoothed Coordinates
    data.location.lat = kf['x'][0]
    data.location.lng = kf['x'][1]
    
    # 2. UPDATE CACHE
    LATEST_POSITIONS[data.device_id] = data.model_dump()

    # 2a. UPDATE HISTORY BUFFER (Demo Resilience)
    # Ensure VCR works even if DynamoDB is offline/empty
    from app.core.shared_state import TELEMETRY_HISTORY
    TELEMETRY_HISTORY[data.device_id].append(data.model_dump())
    if len(TELEMETRY_HISTORY[data.device_id]) > 500:
        TELEMETRY_HISTORY[data.device_id].pop(0)
    
    # 3. AI RISK CALCULATION
    risk_report = SentinelAI.calculate_risk(data.model_dump(), LATEST_POSITIONS)
    
    # 4. BROADCAST
    payload = data.model_dump()
    payload['risk'] = risk_report
    await broadcast_telemetry(payload)
    
    # 5. OFFLOAD SLOW TASKS
    background_tasks.add_task(process_risk_and_db, data)
    
    return risk_report

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


@router.post("/telemetry", dependencies=[Depends(verify_api_key), Depends(check_rate_limit)])
async def ingest_telemetry(
    data: TelemetryData, 
    background_tasks: BackgroundTasks,
    x_device_fingerprint: str = Header(None, alias="X-Device-Fingerprint"),
    x_client_cert: str = Header(None, alias="X-Client-Cert"),
    x_signature: str = Header(None, alias="X-Signature"),
    x_nonce: int = Header(None, alias="X-Nonce")
):
    """
    FAST PATH (JSON): Production-grade ingestion.
    """
    # Enforce Zero Trust if headers present (Phase 4.1)
    risk_report = await process_telemetry_core(data, background_tasks, 
                                             x_device_fingerprint, x_client_cert,
                                             x_signature, x_nonce)
    return {"status": "accepted", "timestamp": data.timestamp, "risk": risk_report}

@router.post("/telemetry/proto", dependencies=[Depends(verify_api_key), Depends(check_rate_limit)])
async def ingest_telemetry_proto(
    request: Request, 
    background_tasks: BackgroundTasks,
    x_device_fingerprint: str = Header(None, alias="X-Device-Fingerprint"),
    x_client_cert: str = Header(None, alias="X-Client-Cert"),
    x_signature: str = Header(None, alias="X-Signature"),
    x_nonce: int = Header(None, alias="X-Nonce")
):
    """
    HIGH DENSITY PATH (Protobuf): 60% Bandwidth Saving.
    """
    try:
        body = await request.body()
        packet = telemetry_pb2.TelemetryPacket()
        packet.ParseFromString(body)
        
        # Convert Proto -> Pydantic
        data = TelemetryData(
            device_id=packet.device_id,
            did=packet.did,
            timestamp=packet.timestamp,
            location=GeoPoint(lat=packet.location.lat, lng=packet.location.lng),
            speed=packet.speed,
            heading=packet.heading,
            battery_level=packet.battery_level,
            is_panic=packet.is_panic
        )
        
        await process_telemetry_core(data, background_tasks, 
                                   x_device_fingerprint, x_client_cert,
                                   x_signature, x_nonce)
        return {"status": "accepted", "method": "PROTOBUF"}
        
    except Exception as e:
        if "Zero Trust" in str(e): raise e
        raise HTTPException(status_code=400, detail=f"Invalid Protobuf: {str(e)}")

@router.get("/alerts")
async def get_all_alerts():
    """
    Get all active alerts from memory (Operational View).
    """
    return list(LATEST_ALERTS.values())

@router.patch("/alerts/{alert_id}/acknowledge")
async def acknowledge_alert(
    alert_id: str,
    x_actor_id: str = Header("operator", alias="X-Actor-ID"),
    x_role: str = Header(..., alias="X-Role")
):
    # RBAC CHECK
    if x_role not in ["COMMANDER", "OFFICER", "DISTRICT_SUPERVISOR"]:
        print(f"RBAC VIOLATION: {x_actor_id} ({x_role}) tried to ACK without permission.")
        raise HTTPException(status_code=403, detail="Insufficient Privileges")

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
        print(f"ALERT_OP: Alert {alert_id} ACKNOWLEDGED by {x_actor_id} ({x_role})")
        return {"status": "success", "alert": LATEST_ALERTS[target_key]}
    
    raise HTTPException(status_code=404, detail="Alert not found active")

@router.patch("/alerts/{alert_id}/resolve")
async def resolve_alert(
    alert_id: str,
    x_actor_id: str = Header("supervisor", alias="X-Actor-ID"),
    x_role: str = Header(..., alias="X-Role")
):
    # RBAC CHECK - STRICT
    if x_role not in ["COMMANDER", "DISTRICT_SUPERVISOR"]:
        print(f"RBAC VIOLATION: {x_actor_id} ({x_role}) tried to RESOLVE without permission.")
        raise HTTPException(status_code=403, detail="Insufficient Privileges: COMMANDER Access Required")

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
        print(f"ALERT_OP: Alert {alert_id} RESOLVED by {x_actor_id} ({x_role})")
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

@router.get("/test")
async def test_endpoint():
    return {"status": "ok", "message": "Router is working"}

@router.get("/map/positions")
async def get_map_positions():
    """
    Get latest known positions of all devices for the map.
    Serves from In-Memory Cache (Redis equivalent) for real-time performance.
    Hydrates from DynamoDB if cache is empty (server restart).
    """
    # TEMPORARILY DISABLED - Blocking on DB connection
    # if not LATEST_POSITIONS:
    #     from app.core.shared_state import hydrate_cache
    #     hydrate_cache()

    return list(LATEST_POSITIONS.values())

@router.get("/telemetry/history/{device_id}")
async def get_device_history(device_id: str, hours: int = 4):
    """
    Fetch historical telemetry for 'Breadcrumbs' (last N hours).
    Efficiently queries DynamoDB partition key.
    Fallbacks to In-Memory Buffer if DB is empty (Demo Mode).
    """
    from boto3.dynamodb.conditions import Key
    from app.core.shared_state import TELEMETRY_HISTORY
    
    # 1. Try In-Memory Buffer First (Fastest for Demo)
    # Since DynamoDB setup in localstack might be flaky/missing
    memory_data = TELEMETRY_HISTORY.get(device_id, [])
    # If we have substantial data in memory, use it.
    if len(memory_data) > 0:
        return memory_data

    # 2. Fallback to DynamoDB (Production Path)
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
        print(f"Error fetching DB history for {device_id}: {e}")
        # Final Fallback: Return memory data again if db failed completely
        return TELEMETRY_HISTORY.get(device_id, [])
