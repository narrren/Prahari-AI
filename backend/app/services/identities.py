from pydantic import BaseModel
from typing import Dict, List, Optional
import hashlib
import time

# --- Mock Hardware Registry ---
# In production, this syncs with the MDM (Mobile Device Management) server.

import hmac

class DeviceIdentity(BaseModel):
    device_id: str
    did: str
    allowed_fingerprint: str # The expected hardware hash
    cert_thumbprint: str     # The expected mTLS cert thumbprint
    status: str = "ACTIVE"
    secret_key: str = "default-secret" # Burned-in Private Key (Simulated)
    last_nonce: int = 0 # Replay Protection State

# Registry of Authorized Hardware
AUTHORIZED_DEVICES = {
    # 1. Safe Trekker
    "ALPINIST_SAFE": DeviceIdentity(
        device_id="ALPINIST_SAFE", 
        did="did:eth:0xSAFE...001", 
        allowed_fingerprint="hw:safe:01", 
        cert_thumbprint="CERT_ALPINIST_SAFE",
        secret_key="sk_safe"
    ),
    # 2. Red Zone Intruder
    "ALPINIST_RED": DeviceIdentity(
        device_id="ALPINIST_RED", 
        did="did:eth:0xRED...002", 
        allowed_fingerprint="hw:red:02", 
        cert_thumbprint="CERT_ALPINIST_RED",
        secret_key="sk_red"
    ),
    # 3. Bot/Drone
    "MECH_DRONE_01": DeviceIdentity(
        device_id="MECH_DRONE_01",
        did="did:eth:0xBOT...999",
        allowed_fingerprint="hw:bot:01",
        cert_thumbprint="CERT_MECH_DRONE_01",
        secret_key="sk_bot"
    ),
    # 4. Dead Man Signal
    "SIGNAL_LOST": DeviceIdentity(
        device_id="SIGNAL_LOST",
        did="did:eth:0xDEAD...666",
        allowed_fingerprint="hw:dead:01",
        cert_thumbprint="CERT_SIGNAL_LOST",
        secret_key="sk_dead"
    )
}

def verify_device_integrity(device_id: str, presented_fingerprint: str, cert_header: str) -> bool:
    """
    ZERO TRUST LOGIC:
    Verifies that the telemetry is coming from the SPECIFIC registered hardware,
    not just a valid API Key holder.
    """
    identity = AUTHORIZED_DEVICES.get(device_id)
    
    if not identity:
        print(f"ZERO_TRUST_FAIL: Device {device_id} not in MDM Registry.")
        return False
        
    if identity.status != "ACTIVE":
        print(f"ZERO_TRUST_FAIL: Device {device_id} is REVOKED/SUSPENDED.")
        return False
        
    # Check Hardware Fingerprint
    if identity.allowed_fingerprint != presented_fingerprint:
        print(f"ZERO_TRUST_FAIL: HW Mismatch for {device_id}. Expected {identity.allowed_fingerprint}, Got {presented_fingerprint}")
        return False
        
    # Check Cert Thumbprint (Application Layer mTLS Simulation)
    if identity.cert_thumbprint != cert_header:
        print(f"ZERO_TRUST_FAIL: Cert Mismatch for {device_id}.")
        return False
        
    return True

def verify_packet_signature(device_id: str, payload_string: str, signature: str, nonce: int) -> bool:
    """
    CRYPTOGRAPHIC ATTESTATION & REPLAY PROTECTION:
    1. Checks Nonce Monotonicity (Anti-Replay).
    2. Verifies HMAC-SHA256 Signature (Attestation).
    """
    identity = AUTHORIZED_DEVICES.get(device_id)
    if not identity: return False
    
    # 1. Replay Protection
    if nonce <= identity.last_nonce:
        print(f"REPLAY ATTACK DETECTED: Device {device_id} sent nonce {nonce} <= last {identity.last_nonce}")
        return False
        
    # 2. Verify Signature
    expected = hmac.new(
        identity.secret_key.encode(), 
        payload_string.encode(), 
        hashlib.sha256
    ).hexdigest()
    
    if not hmac.compare_digest(expected, signature):
        print(f"SIGNATURE FAIL: Device {device_id}. Forged Packet?")
        return False
        
    # 3. Update State
    identity.last_nonce = nonce
    return True
