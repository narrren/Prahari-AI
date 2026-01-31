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

@fastapi_app.on_event("startup")
async def startup_event():
    # Start the Dead Man Switch Monitor
    asyncio.create_task(monitor_dead_mans_switch())

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
from fastapi import Response, Header, HTTPException
from app.reports import generate_efir_pdf
from app.core.shared_state import LATEST_POSITIONS
from app.services.identity import get_permit_info, log_audit_event
import time
import hashlib

@fastapi_app.get("/api/v1/generate-efir/{device_id}")
async def generate_efir(
    device_id: str,
    x_admin_role: str = Header("RESPONDER", alias="X-Role"),
    x_admin_id: str = Header("admin-001", alias="X-Admin-ID")
):
    # 0. RBAC Governance Check
    if x_admin_role not in ["RESPONDER", "SUPER_ADMIN"]:
        raise HTTPException(status_code=403, detail="Access Denied: Viewers cannot generate legal documents.")

    # 1. Fetch data from active trackers
    tracker_state = LATEST_POSITIONS.get(device_id)
    if not tracker_state:
        # Fallback check if it's an alert? For now just fail.
        # Or mock it for demo if ID matches?
        return {"error": "Device not found in active tracking cache"}
    
    # 2. Enrich Data
    # Parse Permit ID from string "Verified Permit: #1234..."
    # A bit hacky but works for demo
    did = tracker_state.get('did', 'unknown')
    permit_str = get_permit_info(did) 
    # extract #XXXX
    import re
    match = re.search(r"Permit: (#\w+)", permit_str)
    permit_id = match.group(1) if match else "PENDING"
    
    # Mocking TXID (In real app, we would look up the TX history block)
    # We define a stable fake hash for the demo
    tx_hash = "0x" + hashlib.sha256(f"{did}{time.time()}".encode()).hexdigest()
    
    # Risk Score should be in state if SentinelAI ran
    # If missing (first ping), default to 0
    
    incident_data = {
        **tracker_state,
        "permit_id": permit_id,
        "blockchain_txid": tx_hash,
        "risk_score": tracker_state.get('risk', {}).get('score', 0),
        "factors": tracker_state.get('risk', {}).get('factors', ["Manual Request"])
    }
    
    # 3. Generate PDF
    pdf_buffer = generate_efir_pdf(incident_data)
    pdf_content = pdf_buffer.getvalue()
    
    # 4. Audit Log (Blockchain)
    # Hash the document to prove it hasn't been tampered with since generation
    doc_hash = "0x" + hashlib.sha256(pdf_content).hexdigest()
    
    # Write to Smart Contract
    audit_tx = log_audit_event(x_admin_id, did, "GENERATED_EFIR", doc_hash)
    print(f"GOVERNANCE AUDIT: Action recorded on blockchain. TXID: {audit_tx}")
    
    # 5. Return as a downloadable stream
    headers = {'Content-Disposition': f'attachment; filename="EFIR_{device_id}.pdf"'}
    return Response(content=pdf_content, media_type="application/pdf", headers=headers)

# Wrap with Socket.IO
# checking if this works with the "app:app" string in uvicorn
app = socketio.ASGIApp(sio, other_asgi_app=fastapi_app)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
