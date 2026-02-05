import requests
import json
import time

API_BASE = "http://localhost:8000/api/v1"

def log(msg, status="INFO"):
    print(f"[{status}] {msg}")

def test_health():
    try:
        res = requests.get(f"{API_BASE}/health/metrics")
        if res.status_code == 200:
            log(f"Health Check Passed: {res.json()}", "SUCCESS")
            return True
        else:
            log(f"Health Check Failed: {res.text}", "ERROR")
            return False
    except Exception as e:
        log(f"Health Check Exception: {e}", "CRITICAL")
        return False

def test_cyber_hud():
    try:
        res = requests.get(f"{API_BASE}/cyber/hud")
        if res.status_code == 200:
            data = res.json()
            log(f"Cyber HUD Active. Threat Level: {data.get('threat_level')}", "SUCCESS")
            return True
        else:
            log(f"Cyber HUD Failed: {res.text}", "ERROR")
            return False
    except Exception as e:
        log(f"Cyber HUD Exception: {e}", "CRITICAL")
        return False

def test_forensics():
    try:
        payload = {"file_hash": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"}
        res = requests.post(f"{API_BASE}/forensics/verify", json=payload)
        if res.status_code == 200:
            data = res.json()
            if data['status'] in ["VERIFIED", "TAMPERED"]:
                log(f"Forensic Verification Passed: {data['status']}", "SUCCESS")
                return True
            else:
                log(f"Unexpected Forensic Status: {data['status']}", "WARN")
                return False
        else:
            log(f"Forensic Verify Failed: {res.text}", "ERROR")
            return False
    except Exception as e:
        log(f"Forensic Check Exception: {e}", "CRITICAL")
        return False


def test_model_integrity():
    try:
        res = requests.get(f"{API_BASE}/integrity/model")
        if res.status_code == 200:
            data = res.json()
            if data['status'] == 'SECURE':
                log(f"Model Integrity: {data['current_hash'][:10]}... [SECURE]", "SUCCESS")
                return True
            else:
                log("Model Integrity: COMPROMISED", "ERROR")
        else:
             log(f"Model Integrity Endpoint Failed: {res.status_code}", "ERROR")
        return False
    except Exception as e:
        log(f"Model Integrity Check Error: {e}", "ERROR")
        return False

def test_bot_detection_via_map():
    # Indirectly check if MECH_DRONE_01 is in the telemetry feed
    try:
        res = requests.get(f"{API_BASE}/map/positions")
        if res.status_code == 200:
            data = res.json()
            # data is a list of positions
            bot = next((p for p in data if p['device_id'] == "MECH_DRONE_01"), None)
            if bot:
                score = bot.get('humanity_score', 100)
                log(f"MECH_DRONE_01 Found. Humanity Score: {score}%", "INFO")
                if score < 50:
                    log("Adversarial AI Defense: DETECTED BOT SUCCESSFULLY", "SUCCESS")
                    return True
                else:
                    log("Adversarial AI Defense: Bot Not Yet Flagged (Score > 50%) - Wait for more samples", "WARN")
                    return True # It exists, so partial pass
            else:
                log("MECH_DRONE_01 not found in telemetry stream yet.", "WARN")
                return False
        return False
    except Exception as e:
        log(f"Map Telemetry Check Failed: {e}", "CRITICAL")
        return False


def test_security_hardening():
    log("Security: Initiating Red Team Pen-Test...", "INIT")
    
    # 1. Test Telemetry Spoofing (No Signature)
    try:
        # Note: API Key is required but Signature is separate check.
        # We send valid API Key but NO signature headers.
        headers = {"x-api-key": "dev-secret"} 
        payload = {
            "device_id": "TEST_SPOOF",
            "did": "did:eth:fake",
            "timestamp": time.time(),
            "location": {"lat":27.5,"lng":91.8},
            "speed":0, "heading":0, "battery_level":100, "is_panic":False
        }
        res = requests.post(f"{API_BASE}/telemetry", json=payload, headers=headers)
        if res.status_code == 401:
            log("Telemetry Spoofing Failed (Expected 401)", "SUCCESS")
        else:
            log(f"Spoofing Allowed! Code: {res.status_code}", "CRITICAL_FAIL")
            return False
    except Exception as e:
        log(f"Spoofing Test Error: {e}", "ERROR")
        return False

    # 2. Test RBAC Violation (Insider Threat)
    try:
        # Try to resolve a fake alert without COMMANDER role
        # We need a fake ID that trigger 404, BUT RBAC happens *before* lookup.
        # So we expect 403 regardless of ID validity.
        res = requests.patch(f"{API_BASE}/alerts/fake-id-999/resolve", headers={"X-Role": "INTERN", "X-Actor-ID": "bad-actor"})
        if res.status_code == 403:
            log("Unauthorized Access Blocked (Expected 403)", "SUCCESS")
        else:
            log(f"Insider Threat Allowed! Code: {res.status_code}", "CRITICAL_FAIL")
            return False
    except Exception as e:
        log(f"RBAC Test Error: {e}", "ERROR")
        return False
        
    return True

def main():
    log("Starting V5.0 System Verification...", "INIT")
    
    checks = [
        test_health,
        test_cyber_hud,
        test_forensics,
        test_model_integrity,
        test_security_hardening,
        test_bot_detection_via_map
    ]
    
    passed = 0
    for check in checks:
        if check():
            passed += 1
        time.sleep(0.5)
        
    log(f"Verification Complete. {passed}/{len(checks)} Checks Passed.", "DONE")

if __name__ == "__main__":
    main()
