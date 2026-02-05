import requests
import time
import sys
import os
import random
import hmac
import hashlib

# Add project root to path
sys.path.append(os.path.abspath("backend"))
from app.core import telemetry_pb2

BASE_URL = "http://localhost:8000/api/v1"

def sign_payload(secret: str, payload_string: str) -> str:
    return hmac.new(
        secret.encode(), 
        payload_string.encode(), 
        hashlib.sha256
    ).hexdigest()

def test_health():
    print(f"[TEST] Checking System Health...")
    try:
        res = requests.get(f"{BASE_URL}/health/metrics", timeout=5)
        if res.status_code == 200:
            print(f"✅ Health OK: {res.json()}")
            return True
        else:
            print(f"❌ Health Failed: {res.status_code}")
            return False
    except Exception as e:
        print(f"❌ Health Unreachable: {e}")
        return False

def test_json_ingest():
    print(f"\n[TEST] Sending JSON Telemetry (Signed & Attested)...")
    timestamp = time.time()
    payload = {
        "device_id": "ALPINIST_01",
        "did": "did:eth:0xTESTUSER",
        "timestamp": timestamp,
        "location": {"lat": 27.5861, "lng": 91.8594}, 
        "speed": 1.5,
        "heading": 90.0,
        "battery_level": 85.0,
        "is_panic": True 
    }
    
    # 1. Sign
    secret = "sk_alp_01"
    nonce = int(time.time() * 1000)
    payload_string = f"ALPINIST_01:{timestamp}:27.5861:91.8594"
    signature = sign_payload(secret, payload_string)

    headers = {
        "x-api-key": "dev-secret",
        "X-Device-Fingerprint": "aa:bb:cc:dd:01", 
        "X-Client-Cert": "CERT_SHA_001",
        "X-Signature": signature,
        "X-Nonce": str(nonce)
    }
    
    try:
        res = requests.post(f"{BASE_URL}/telemetry", json=payload, headers=headers)
        if res.status_code == 200:
            print(f"✅ JSON Ingest Validated: {res.json()}")
            return nonce, headers # Return for replay test
        else:
            print(f"❌ JSON Ingest Failed: {res.text}")
            return None, None
    except Exception as e:
        print(f"❌ JSON Request Error: {e}")
        return None, None

def test_replay_attack(old_nonce, old_headers):
    print(f"\n[TEST] Simulating Replay Attack (Resending valid packet)...")
    if not old_nonce:
        print("⏭️  Skipping Replay Test (Integration failed)")
        return

    # Payload is same, Headers are same (same nonce)
    # Backend should reject because nonce <= last_nonce
    timestamp = time.time() # This timestamp doesn't verify replay, the Signature does. 
                            # Reusing exact same packet means exact same timestamp.
                            # But wait, logic computes signature on payload. If we change TS, sig fails.
                            # If we use old payload + old headers, it is a perfect replay.
    
    # We must match the PREVIOUS payload exactly for signature to be valid
    # But for this test, we just care that the NONCE is stale.
    # The backend checks Nonce BEFORE Signature? Actually inside verify_packet_signature:
    # 1. Replay Check (Nonce)
    # 2. Signature Check
    # So if we send SAME headers, it fails Replay Check. Perfect.
    
    payload = {
        "device_id": "ALPINIST_01",
        "did": "did:eth:0xTESTUSER",
        # We dummy this, backend checks header Nonce vs State
        "timestamp": 0, 
        "location": {"lat": 0, "lng": 0},
    }
    
    try:
        res = requests.post(f"{BASE_URL}/telemetry", json=payload, headers=old_headers)
        if res.status_code == 401 and "Replay" in res.text:
             print(f"✅ Replay Attack Blocked: {res.status_code}")
        else:
             print(f"❌ Replay Protection Failed: Code {res.status_code} (Expected 401)")
    except Exception as e:
        print(f"❌ Replay Test Error: {e}")

def test_zero_trust_block():
    print(f"\n[TEST] Verifying Zero Trust Block (Unauthorized Device)...")
    payload = {
        "device_id": "ALPINIST_01", 
        "location": {"lat":0,"lng":0}, 
        "is_panic": False,
        "did": "did:eth:ATTACKER",
        "timestamp": time.time()
    }
    headers_bad = {
        "x-api-key": "dev-secret",
        "X-Device-Fingerprint": "BAD_FINGERPRINT", 
        "X-Client-Cert": "BAD_CERT"
    }
    try:
        res = requests.post(f"{BASE_URL}/telemetry", json=payload, headers=headers_bad)
        if res.status_code == 401:
            print(f"✅ Zero Trust Block Validated.")
        else:
            print(f"❌ Zero Trust Failed: Code {res.status_code}")
    except: pass

def test_proto_ingest():
    print(f"\n[TEST] Sending PROTOBUF Telemetry (Signed)...")
    packet = telemetry_pb2.TelemetryPacket()
    packet.device_id = "ALPINIST_02"
    packet.did = "did:eth:0xPROTOUSER"
    ts = time.time()
    packet.timestamp = ts
    packet.location.lat = 27.5900
    packet.location.lng = 91.8600
    packet.speed = 2.0; packet.heading = 180.0
    packet.battery_level = 99.9; packet.is_panic = True 
    binary_data = packet.SerializeToString()
    
    # Sign
    secret = "sk_alp_02"
    nonce = int(time.time() * 1000)
    # Match backend reconstruction exactly
    payload_string = f"ALPINIST_02:{packet.timestamp}:{packet.location.lat}:{packet.location.lng}"
    signature = sign_payload(secret, payload_string)
    
    headers = {
        "x-api-key": "dev-secret",
        "Content-Type": "application/x-protobuf",
        "X-Device-Fingerprint": "aa:bb:cc:dd:02",
        "X-Client-Cert": "CERT_SHA_002",
        "X-Signature": signature,
        "X-Nonce": str(nonce)
    }
    
    try:
        res = requests.post(f"{BASE_URL}/telemetry/proto", data=binary_data, headers=headers)
        if res.status_code == 200:
            print(f"✅ PROTOBUF Ingest Validated: {res.json()}")
        else:
            print(f"❌ PROTOBUF Ingest Failed: {res.text}")
    except Exception as e:
        print(f"❌ PROTOBUF Request Error: {e}")

def test_cyber_lockdown():
    print(f"\n[TEST] CYBER-SENTINEL: Provoking System Lockdown...")
    # Trigger bad auth repeatedly
    for i in range(10):
        headers = {"X-Role": "INVALID", "X-Justification": "Testing Lockdown"}
        res = requests.get(f"{BASE_URL}/generate-efir/ALPINIST_01", headers=headers)
        
        print(f"   Attempt {i+1}: Code {res.status_code}")
        
        if res.status_code == 503:
            print(f"✅ LOCKDOWN ENGAGED at Attempt {i+1}: {res.text}")
            return
            
        time.sleep(0.2) # Allow async processing
        
    print(f"❌ Cyber Lockdown Failed to Engage after 10 bad attempts.")


if __name__ == "__main__":
    if test_health():
        time.sleep(1)
        nonce, headers = test_json_ingest()
        time.sleep(1)
        test_replay_attack(nonce, headers)
        time.sleep(1)
        test_zero_trust_block()
        time.sleep(1)
        test_proto_ingest()
        time.sleep(1)
        test_cyber_lockdown()
    else:
        print("CRITICAL: Backend is offline. Cannot proceed.")
