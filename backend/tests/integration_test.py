import requests
import time
import sys
import os
import random

# Add project root to path for imports if needed, 
# but we will try to use the generated file directly if possible or just use independent proto definition logic
# For simplicity, we assume the server is running on localhost:8000

BASE_URL = "http://127.0.0.1:8002/api/v1"

# We need the generated protobuf class to serialize the binary payload.
# Assuming we run this from project root, path is backend/app/core
sys.path.append(os.path.abspath("backend"))
from app.core import telemetry_pb2

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
    print(f"\n[TEST] Sending JSON Telemetry...")
    payload = {
        "device_id": "TEST_DEVICE_001",
        "did": "did:eth:0xTESTUSER",
        "timestamp": time.time(),
        "location": {"lat": 27.5861, "lng": 91.8594}, # Tawang
        "speed": 1.5,
        "heading": 90.0,
        "battery_level": 85.0,
        "is_panic": True # Trigger Alert for Governance Test
    }
    headers = {"x-api-key": "dev-secret"} # From config.py
    try:
        res = requests.post(f"{BASE_URL}/telemetry", json=payload, headers=headers)
        if res.status_code == 200:
            print(f"✅ JSON Ingest Validated: {res.json()}")
        else:
            print(f"❌ JSON Ingest Failed: {res.text}")
            with open("test_metrics.log", "w") as f: f.write(res.text)
    except Exception as e:
        print(f"❌ JSON Request Error: {e}")

def test_proto_ingest():
    print(f"\n[TEST] Sending PROTOBUF (High Density) Telemetry...")
    
    # 1. Create Packet
    packet = telemetry_pb2.TelemetryPacket()
    packet.device_id = "TEST_DEVICE_PROTO_002"
    packet.did = "did:eth:0xPROTOUSER"
    packet.timestamp = time.time()
    packet.location.lat = 27.5900
    packet.location.lng = 91.8600
    packet.speed = 2.0
    packet.heading = 180.0
    packet.battery_level = 99.9
    packet.is_panic = True 
    
    # 2. Serialize
    binary_data = packet.SerializeToString()
    
    # 3. Send
    headers = {
        "x-api-key": "dev-secret",
        "Content-Type": "application/x-protobuf"
    }
    
    try:
        res = requests.post(f"{BASE_URL}/telemetry/proto", data=binary_data, headers=headers)
        if res.status_code == 200:
            print(f"✅ PROTOBUF Ingest Validated: {res.json()}")
        else:
            print(f"❌ PROTOBUF Ingest Failed: {res.text}")
            with open("test_metrics.log", "a") as f: f.write(f"\nPROTO_FAIL: {res.text}")
    except Exception as e:
        print(f"❌ PROTOBUF Request Error: {e}")

def test_governance():
    print(f"\n[TEST] Governance: Claiming Incident & Logging Decision...")
    
    # 1. First, fetch alerts to find one to claim
    # Allow time for async processing
    time.sleep(2) 
    res = requests.get(f"{BASE_URL}/alerts")
    alerts = res.json()
    if not alerts:
        print("⚠️ No alerts found to claim. Skipping.")
        return

    target_alert = alerts[0]['alert_id']
    print(f"   Targeting Alert: {target_alert}")
    
    # 2. Claim
    headers = {"X-Actor-ID": "TEST_COMMANDER", "X-Role": "DISTRICT_SUPERVISOR"}
    res = requests.post(f"{BASE_URL}/incident/claim/{target_alert}", headers=headers)
    if res.status_code == 200:
        print(f"✅ Claim Successful: {res.json()}")
    else:
        print(f"❌ Claim Failed: {res.text}")

    # 3. Log Decision
    decision_payload = {
        "decision_id": f"DEC_{int(time.time())}",
        "alert_id": target_alert,
        "ai_recommendation": "Dispatch Team",
        "operator_action": "Authorized Dispatch",
        "divergence_flag": False,
        "justification": "Standard Protocol",
        "timestamp": time.time()
    }
    res = requests.post(f"{BASE_URL}/decision/log", json=decision_payload, headers=headers)
    if res.status_code == 200:
        print(f"✅ Decision Logged: {res.json()}")
    else:
        print(f"❌ Log Decision Failed: {res.text}")


if __name__ == "__main__":
    if test_health():
        time.sleep(1)
        test_json_ingest()
        time.sleep(1)
        test_proto_ingest()
        test_governance()
    else:
        print("CRITICAL: Backend is offline. Cannot proceed.")
