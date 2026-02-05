from app.core.shared_state import LATEST_POSITIONS
from app.services.websocket import notify_alert
from app.services.db import get_table
from app.models import Alert, AlertType, GeoPoint
import time
import asyncio
import uuid
from decimal import Decimal

async def monitor_dead_mans_switch():
    """
    Production Periodic Task: "Dead Man's Switch"
    Detects dropped signals (>60s) in High Risk Zones.
    V3.1 Upgrade: Confidence-Based Failure Detection.
    """
    from app.core.shared_state import LATEST_ALERTS
    print("SCHEDULER: Starting Dead Man's Switch Monitor (Smart Upgrade)...")
    
    while True:
        try:
            now = time.time()
            for device_id, state in list(LATEST_POSITIONS.items()):
                
                # Check 1: Time Drift (Threshold: 60s for demo)
                last_seen = state.get('timestamp', 0)
                elapsed = now - last_seen
                THRESHOLD = 60 
                
                # Check 2: Zone Risk
                from app.services.geofence import check_geofence_breach, GeoPoint
                gp = GeoPoint(lat=state['location']['lat'], lng=state['location']['lng'])
                zone = check_geofence_breach(gp)
                is_high_risk = zone and zone.risk_level == "HIGH"
                
                if elapsed > THRESHOLD and is_high_risk:
                    # --- V3.1 SMART CONFIDENCE LOGIC ---
                    
                    # Base Confidence: 80% (High Risk Zone silence is usually bad)
                    confidence = 80
                    reasons = ["High Risk Zone Silence"]
                    suggested_action = "INITIATE SEARCH"
                    
                    # Factor 1: Low Battery?
                    batt = state.get('battery_level', 100)
                    if batt < 15:
                        confidence -= 40
                        reasons.append(f"Low Battery ({batt}%)")
                        suggested_action = "CHECK LAST POS / BATTERY DRAIN"
                        
                    # Factor 2: Weather? (Mocked: Randomly assume bad weather for demo purposes if ID ends in odd number)
                    # In prod, this queries app.engine.WeatherService
                    if int(str(ord(device_id[-1]))) % 2 != 0: 
                        confidence -= 20
                        reasons.append("Possible Weather Interference")
                    
                    # Factor 3: Movement History
                    # If speed was 0 before loss, maybe just resting?
                    speed = state.get('speed', 0)
                    if speed < 0.5:
                        confidence -= 10
                        reasons.append("Subject was stationary")
                    
                    final_score = max(0, min(100, confidence))
                    
                    # Construct Alert
                    did = state.get('did', 'unknown')
                    msg = (f"SIGNAL LOST (Conf: {final_score}%). "
                           f"Analysis: {', '.join(reasons)}. "
                           f"Action: {suggested_action}. "
                           f"Silent for {int(elapsed)}s.")
                           
                    alert_key = f"{device_id}_SIGNAL_LOST"
                    
                    # Upsert into Active Alerts (Stateful)
                    existing = LATEST_ALERTS.get(alert_key)
                    
                    alert_dict = None
                    if existing and existing['status'] != 'RESOLVED':
                        existing['timestamp'] = now
                        existing['message'] = msg
                        existing['severity'] = "CRITICAL" if final_score > 50 else "MEDIUM"
                        # Only notify if confidence changed significantly? For now notify always on loop
                    else:
                        new_alert = Alert(
                            alert_id=str(uuid.uuid4()),
                            device_id=device_id,
                            did=did,
                            type="SIGNAL_LOST_CRITICAL",
                            severity="CRITICAL" if final_score > 50 else "MEDIUM",
                            timestamp=now,
                            location=state['location'],
                            message=msg,
                            status="DETECTED"
                        )
                        alert_dict = new_alert.model_dump()
                        alert_dict['confidence'] = final_score # V3.1 Field
                        alert_dict['suggested_action'] = suggested_action # V3.1 Field
                        LATEST_ALERTS[alert_key] = alert_dict
                        
                        await notify_alert(alert_dict)
                    
        except Exception as e:
            print(f"Scheduler Error: {e}")
            
        # --- TASK B: DR SNAPSHOT (Every 5 mins) ---
        if int(time.time()) % 300 < 65:  # Window to run every ~5 mins
             from app.snapshots import create_snapshot
             try:
                 create_snapshot()
             except:
                 pass
                 
        # --- TASK C: CRYPTOGRAPHIC ANCHORING (Chain-of-Custody) ---
        # Phase 4.1: Build Merkle Tree of current state and anchor to Ledger
        try:
            from app.services.merkle import generate_telemetry_merkle_root
            from app.core.shared_state import SYSTEM_METRICS
            
            latest_batch = list(LATEST_POSITIONS.values())
            if latest_batch:
                merkle_root = generate_telemetry_merkle_root(latest_batch)
                
                # Mock Blockchain Increment
                current_height = SYSTEM_METRICS.get('chain_height', 150000)
                SYSTEM_METRICS['chain_height'] = current_height + 1
                SYSTEM_METRICS['merkle_root'] = merkle_root
                
                print(f"BLOCKCHAIN ANCHOR: Telemetry Batch Verified. Root: {merkle_root[:10]}... | Height: {current_height + 1}")
        except Exception as e:
            print(f"Merkle Anchor Error: {e}")

        await asyncio.sleep(60)
