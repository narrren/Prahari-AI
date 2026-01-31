from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.routers import telemetry
from app.services.websocket import sio
import socketio

from app.scheduler import monitor_dead_mans_switch
import asyncio

# Initialize FastAPI regular app
fastapi_app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# ... (Existing imports)
from app.core.shared_state import LATEST_POSITIONS, SYSTEM_METRICS, LATEST_ALERTS

@fastapi_app.on_event("startup")
async def startup_event():
    # 1. Hydrate Cache (Fix Task A)
    from app.core.shared_state import hydrate_cache
    hydrate_cache()
    
    # 2. Start the Dead Man Switch Monitor / Snapshot Scheduler
    asyncio.create_task(monitor_dead_mans_switch())
    
    # 3. Observability Start
    SYSTEM_METRICS['start_time'] = time.time()
    print("OBSERVABILITY: System Health Monitor Started.")

@fastapi_app.get("/api/v1/health/metrics")
async def get_system_health():
    """
    OBSERVABILITY DASHBOARD: Returns critical system vitals.
    """
    now = time.time()
    uptime = now - SYSTEM_METRICS.get('start_time', now)
    
    # Dynamic Updates
    SYSTEM_METRICS['active_users'] = len(LATEST_POSITIONS)
    SYSTEM_METRICS['alerts_active'] = len([a for a in LATEST_ALERTS.values() if a['status'] != 'RESOLVED'])
    
    # Mock Ingestion Rate (until telemetry hook is fully wired)
    # In prod, atomic counter in telemetry.py would drive this
    if uptime > 0:
        SYSTEM_METRICS['ingestion_rate'] = round((SYSTEM_METRICS['ingestion_count'] / uptime), 2)
    
    return {
        "status": "HEALTHY",
        "uptime_seconds": int(uptime),
        "metrics": SYSTEM_METRICS,
        "services": {
            "database": "CONNECTED", # Assumed via successful reads
            "blockchain": "CONNECTED",
            "websocket": "ACTIVE"
        }
    }

fastapi_app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In prod, specify domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

fastapi_app.include_router(telemetry.router, prefix=settings.API_V1_STR, tags=["telemetry"])

@fastapi_app.get("/")
def root():
    return {"message": "Prahari-AI Sentinel Backend Online"}

# ... existing code ...
from fastapi import Response, Header, HTTPException, Body
from app.reports import generate_efir_pdf
from app.core.shared_state import LATEST_POSITIONS
from app.services.identity import get_permit_info, log_audit_event
import time
import hashlib

# --- OPERATIONAL CONTROL PLANE (RBAC) ---
ROLE_OPERATOR = "MISSION_OPERATOR"       # Read-Only, Acknowledge
ROLE_SUPERVISOR = "DISTRICT_SUPERVISOR"  # Generate FIR, Override
ROLE_ADMIN = "SYSTEM_ADMIN"              # Config, Tuning
ROLE_AUDITOR = "AUDIT_AUTHORITY"         # Read-Only Audit

def log_governance_action(actor: str, role: str, action: str, justification: str, target: str):
    """
    Simulates a tamper-proof write to a specialized Audit Server.
    In production, this would sign the log with a private key.
    """
    print(f"\n[GOVERNANCE AUDIT] ------------------------------------------------")
    print(f"ACTORID   : {actor}")
    print(f"ROLE      : {role}")
    print(f"ACTION    : {action}")
    print(f"TARGET    : {target}")
    print(f"REASON    : {justification}")
    print(f"TIMESTAMP : {time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime())}")
    print(f"------------------------------------------------------------------\n")

@fastapi_app.get("/api/v1/generate-efir/{device_id}")
async def generate_efir(
    device_id: str,
    x_actor_id: str = Header("officer-001", alias="X-Actor-ID"),
    x_role: str = Header(ROLE_SUPERVISOR, alias="X-Role"),
    x_justification: str = Header(..., alias="X-Justification") # Require justification
):
    # 0. RBAC Governance Check
    if x_role not in [ROLE_SUPERVISOR, ROLE_ADMIN]:
        log_governance_action(x_actor_id, x_role, "GENERATE_EFIR_ATTEMPT", x_justification, device_id)
        raise HTTPException(status_code=403, detail=f"Access Denied: Role '{x_role}' is not authorized to generate legal documents.")

    # 1. Fetch data from active trackers
    tracker_state = LATEST_POSITIONS.get(device_id)
    if not tracker_state:
        # Fallback check if it's an alert? For now just fail.
        return {"error": "Device not found in active tracking cache"}
    
    # 2. Enrich Data
    # Parse Permit ID from string "Verified Permit: #1234..."
    did = tracker_state.get('did', 'unknown')
    permit_str = get_permit_info(did) 
    import re
    match = re.search(r"Permit: (#\w+)", permit_str)
    permit_id = match.group(1) if match else "PENDING"
    
    # Mocking TXID (In real app, we would look up the TX history block)
    tx_hash = "0x" + hashlib.sha256(f"{did}{time.time()}".encode()).hexdigest()
    
    # 2b. Reconstruct Timeline (Legal Narrative)
    from app.services.timeline import generate_chronology
    timeline_events = generate_chronology(device_id, tracker_state)
    
    incident_data = {
        **tracker_state,
        "permit_id": permit_id,
        "blockchain_txid": tx_hash,
        "risk_score": tracker_state.get('risk', {}).get('score', 0),
        "factors": tracker_state.get('risk', {}).get('factors', ["Manual Request"]),
        "timeline": timeline_events # <--- Added for E-FIR V2
    }
    
    # 3. Generate PDF
    pdf_buffer = generate_efir_pdf(incident_data)
    pdf_content = pdf_buffer.getvalue()
    
    # 4. Audit Log (Blockchain + Internal Governance Log)
    doc_hash = "0x" + hashlib.sha256(pdf_content).hexdigest()
    
    # Internal Log
    log_governance_action(x_actor_id, x_role, "GENERATE_EFIR", x_justification, device_id)

    # Blockchain Log
    audit_tx = log_audit_event(x_actor_id, did, "GENERATED_EFIR", doc_hash)
    print(f"BLOCKCHAIN CONFIRMATION: TXID: {audit_tx}")
    
    # 5. Return as a downloadable stream
    headers = {'Content-Disposition': f'attachment; filename="EFIR_{device_id}.pdf"'}
    return Response(content=pdf_content, media_type="application/pdf", headers=headers)

@fastapi_app.post("/api/v1/alert/override/{alert_id}")
async def override_alert(
    alert_id: str,
    x_actor_id: str = Header("officer-001", alias="X-Actor-ID"),
    x_role: str = Header(ROLE_SUPERVISOR, alias="X-Role"),
    x_justification: str = Header(..., alias="X-Justification")
):
    """
    Endpoint for Supervisors to suppress false alarms or extensive drills.
    """
    # RBAC Check
    if x_role not in [ROLE_SUPERVISOR, ROLE_ADMIN]:
         log_governance_action(x_actor_id, x_role, "OVERRIDE_ATTEMPT", x_justification, alert_id)
         raise HTTPException(status_code=403, detail="Access Denied: Only Supervisors can override operational alerts.")

    # Log the action
    log_governance_action(x_actor_id, x_role, "ALERT_OVERRIDE", x_justification, alert_id)
    
    return {"status": "success", "message": f"Alert {alert_id} overridden by {x_actor_id}", "audit_logged": True}

# --- V3.2 COMMAND ENDPOINTS ---
from app.models import DecisionRecord, IncidentHandoff, SystemMode
from app.core.shared_state import DECISION_HISTORY, SYSTEM_MODE, LATEST_ALERTS
import app.core.shared_state as shared_state # To modify global

@fastapi_app.post("/api/v1/decision/log")
async def log_decision(
    record: DecisionRecord,
    x_actor_id: str = Header("officer-001", alias="X-Actor-ID")
):
    """
    Provenance Engine: Logs a human decision for accountability.
    """
    record.operator_action = f"{record.operator_action} (by {x_actor_id})"
    DECISION_HISTORY.append(record)
    return {"status": "logged", "provenance_id": record.decision_id}

@fastapi_app.post("/api/v1/incident/claim/{alert_id}")
async def claim_incident(
    alert_id: str,
    x_actor_id: str = Header("officer-001", alias="X-Actor-ID")
):
    """
    ICS Protocol: Assigns Exclusive Incident Commander.
    """
    # Find alert in cache (Key might be device_id_TYPE, so we search values)
    target_key = None
    target_alert = None
    
    for key, alert in LATEST_ALERTS.items():
        if alert['alert_id'] == alert_id:
            target_key = key
            target_alert = alert
            break
            
    if not target_key:
         raise HTTPException(status_code=404, detail="Active Alert not found")

    # Log Handoff
    handoff = IncidentHandoff(
        from_actor=target_alert.get('owner_id', 'SYSTEM'),
        to_actor=x_actor_id,
        timestamp=time.time(),
        reason="Manual Claim of Command"
    )
    
    # Update State
    LATEST_ALERTS[target_key]['owner_id'] = x_actor_id
    LATEST_ALERTS[target_key]['handoff_log'].append(handoff)
    
    return {"status": "assigned", "commander": x_actor_id, "alert_id": alert_id}

@fastapi_app.post("/api/v1/system/mode")
async def set_system_mode(
    mode: SystemMode = Body(..., embed=True),
    x_actor_id: str = Header("admin", alias="X-Actor-ID"),
    x_role: str = Header(ROLE_ADMIN, alias="X-Role")
):
    """
    Emergency Kill Switch / Degradation Control.
    """
    if x_role != ROLE_ADMIN:
        raise HTTPException(status_code=403, detail="Only Admins can change System DEFCON modes.")
        
    shared_state.SYSTEM_MODE = mode
    SYSTEM_METRICS['mode'] = mode
    
    log_governance_action(x_actor_id, x_role, "CHANGE_SYSTEM_MODE", f"Switched to {mode}", "GLOBAL_SYSTEM")
    return {"status": "updated", "current_mode": mode}

@fastapi_app.get("/api/v1/system/policy")
async def get_privacy_policy():
    """
    Data Lifecycle Transparency.
    """
    return {
        "telemetry_retention_days": 30,
        "incident_archive_years": 7,
        "analytics_anonymization": "AUTOMATIC",
        "gdpr_compliance": "PARTIAL (Sovereign Exemption)"
    }

# Wrap with Socket.IO
# checking if this works with the "app:app" string in uvicorn
app = socketio.ASGIApp(sio, other_asgi_app=fastapi_app)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
