from fastapi import FastAPI, Request, Response, Header, Body, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.routers import telemetry
from app.services.websocket import sio
import socketio
from collections import defaultdict

from app.scheduler import monitor_dead_mans_switch
import asyncio
import hashlib
import time

# Initialize FastAPI regular app
fastapi_app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# Import routers
from app.routers import telemetry

# ... (Existing imports)
from app.core.shared_state import LATEST_POSITIONS, SYSTEM_METRICS, LATEST_ALERTS

# Include routers
fastapi_app.include_router(telemetry.router, prefix=settings.API_V1_STR, tags=["telemetry"])

@fastapi_app.on_event("startup")
async def startup_event():
    # 1. Integrity Monitor (V5.1 AI Provenance)
    from app.services.integrity import init_integrity_monitor
    init_integrity_monitor()

    # 2. Hydrate Cache (Fix Task A)
    # TEMPORARILY DISABLED - Blocking startup
    # from app.core.shared_state import hydrate_cache
    # hydrate_cache()
    # try:
    #    hydrate_cache()
    # except:
    #    pass
    
    # 3. Start the Dead Man Switch Monitor / Snapshot Scheduler
    # TEMPORARILY DISABLED - May be blocking event loop
    # asyncio.create_task(monitor_dead_mans_switch())

    # 4. Start Integrity Monitor Loop (Every 60s)
    # TEMPORARILY DISABLED - May be blocking startup
    # from app.services.integrity import verify_model_integrity
    # async def integrity_loop():
    #     while True:
    #         verify_model_integrity()
    #         await asyncio.sleep(60)
    #         
    # asyncio.create_task(integrity_loop())

    # 5. Start Data Shredder (Every 24h)
    # TEMPORARILY DISABLED - May be blocking startup
    # from app.services.shredder import run_data_shredder
    # async def shredder_loop():
    #     while True:
    #         await run_data_shredder()
    #         await asyncio.sleep(86400) # Daily

    # asyncio.create_task(shredder_loop())
    
    # 6. Observability Start
    SYSTEM_METRICS['start_time'] = time.time()
    
    print("OBSERVABILITY: System Health Monitor Started.")

# ... (Existing Endpoints)

@fastapi_app.get("/api/v1/integrity/model")
async def check_model_integrity():
    from app.services.integrity import verify_model_integrity
    return verify_model_integrity()

@fastapi_app.post("/api/v1/forensics/merkle-proof")
async def get_merkle_proof(data: dict = Body(...)):
    """
    Forensic Time-Traveler: Get Cryptographic Proof path for data chunk.
    """
    from app.services.integrity import generate_merkle_proof
    # In real app, we would look up the data in DB to verify existence first.
    # Here we simulate the proof path for whatever data is claimed.
    return generate_merkle_proof(data, [])

@fastapi_app.post("/api/v1/forensics/verify")
async def verify_forensics(
    file_hash: str = Body(..., embed=True),
    x_auditor_key: str = Header("AUDIT_KEY_001", alias="X-Auditor-Key")
):
    """
    Mock Verification against Blockchain Ledger.
    """
    # In real life, web3.eth.call(contract.verify(hash))
    is_valid = True # Demo assumption
    
    verification = ForensicVerification(
        doc_hash=file_hash,
        status="VERIFIED" if is_valid else "TAMPERED",
        timestamp=time.time(),
        blockchain_txid="0x" + hashlib.sha256(file_hash.encode()).hexdigest(),
        signer_did="did:eth:0xGOVERNANCE_DAO"
    )
    FORENSIC_LOGS.append(verification)
    return verification

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
    if shared_state.SYSTEM_MODE == SystemMode.CYBER_LOCKDOWN:
        SYSTEM_METRICS['mode'] = "CYBER_LOCKDOWN 🛡️"
    
    # Mock Ingestion Rate (until telemetry hook is fully wired)
    # In prod, atomic counter in telemetry.py would drive this
    if uptime > 0:
        SYSTEM_METRICS['ingestion_rate'] = round((SYSTEM_METRICS['ingestion_count'] / uptime), 2)
    
    return {
        "status": "HEALTHY" if shared_state.SYSTEM_MODE != SystemMode.CYBER_LOCKDOWN else "LOCKED",
        "uptime_seconds": int(uptime),
        "metrics": SYSTEM_METRICS,
        "services": {
            "database": "CONNECTED", # Assumed via successful reads
            "blockchain": "CONNECTED",
            "websocket": "ACTIVE"
        }
    }

# --- CYBER SAFETY SENTINEL ---
class CyberGuard:
    def __init__(self):
        self.failures = defaultdict(int)
        self.threshold = 5
        self.protected_paths = ["/api/v1/generate-efir", "/api/v1/alert/override", "/api/v1/system/mode"]

    def record_failure(self, ip: str):
        self.failures[ip] += 1
        print(f"CYBER_WATCH: Login Failure from {ip}. Count: {self.failures[ip]}")
        if self.failures[ip] >= self.threshold:
            self.trigger_lockdown(ip)

    def is_locked_out(self, path: str) -> bool:
        # Blocks sensitive write actions during cyber attack
        if shared_state.SYSTEM_MODE == SystemMode.CYBER_LOCKDOWN:
            # Check if path is one of the protected prefixes
            return any(path.startswith(p) for p in self.protected_paths)
        return False

    def trigger_lockdown(self, ip: str):
        if shared_state.SYSTEM_MODE != SystemMode.CYBER_LOCKDOWN:
            print(f"🚨 CYBER INCIDENT DETECTED from {ip}! ENGAGING LOCKDOWN MODE.")
            shared_state.SYSTEM_MODE = SystemMode.CYBER_LOCKDOWN
            SYSTEM_METRICS['mode'] = "CYBER_LOCKDOWN"
            
            # V5.0 SOAR Response
            from app.core.shared_state import CYBER_HUD
            CYBER_HUD.threat_level = "CRITICAL"
            CYBER_HUD.active_countermeasures.append(f"Null Route (Blackhole) for {ip}")
            CYBER_HUD.active_countermeasures.append("MFA Enforced for Admin")
            CYBER_HUD.blacklisted_ips.append(ip)
            CYBER_HUD.last_attack_timestamp = time.time()
            
            log_governance_action("SYSTEM", "SENTINEL", "TRIGGER_LOCKDOWN", f"Too many auth failures from {ip}", "GLOBAL")

# --- V5.0 SOVEREIGN GRADE ENDPOINTS ---
from app.models import ForensicVerification, CyberHudState
from app.core.shared_state import CYBER_HUD, FORENSIC_LOGS

@fastapi_app.get("/api/v1/cyber/hud", response_model=CyberHudState)
async def get_cyber_hud():
    return CYBER_HUD
    
@fastapi_app.post("/api/v1/alert/attest/{alert_id}")
async def attest_alert(alert_id: str, x_node_id: str = Header("CHECKPOST_ALPHA", alias="X-Node-ID")):
    """
    Decentralized Alert Attestation (DAA)
    """
    target = None
    for alert in LATEST_ALERTS.values():
        if alert['alert_id'] == alert_id:
            target = alert
            break
    if not target: raise HTTPException(404, "Alert not found")
    
    if x_node_id not in target['attestors']:
        target['attestors'].append(x_node_id)
        
    # Consensus Logic (BFT-Lite)
    if len(target['attestors']) >= 1: # For demo, 1 external node is enough
        target['attestation_status'] = "ATTESTED"
        
    return {"status": "attested", "total_signatures": len(target['attestors'])}





cyber_guard = CyberGuard()

@fastapi_app.middleware("http")
async def cyber_defense_layer(request: Request, call_next):
    client_ip = request.client.host if request.client else "unknown"
    
    # 1. Pre-Check: Are we in Lockdown?
    if cyber_guard.is_locked_out(request.url.path):
         return Response(content="SYSTEM LOCKED DOWN DUE TO CYBER THREAT DETECTED.", status_code=503)

    # 2. Process Request
    response = await call_next(request)
    
    # 3. Post-Check: Did Auth Fail?
    if response.status_code in [401, 403]:
        cyber_guard.record_failure(client_ip)
        
    return response

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
    
    # 4. Decentralized Evidence Vault (IPFS + Blockchain)
    from app.services.ipfs import upload_to_ipfs
    
    # Upload to "Decentralized Web"
    ipfs_cid = upload_to_ipfs(pdf_content)
    print(f"DECENTRALIZED STORAGE: E-FIR Uploaded to IPFS. CID: {ipfs_cid}")
    
    # Internal Log
    log_governance_action(x_actor_id, x_role, "GENERATE_EFIR", x_justification, device_id)

    # Blockchain Log (Anchoring the IPFS CID)
    audit_tx = log_audit_event(x_actor_id, did, "GENERATED_EFIR", ipfs_cid)
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
