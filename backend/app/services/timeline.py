from typing import List, Dict
import time
from app.core.shared_state import LATEST_ALERTS
from app.services.identity import get_permit_info

def generate_chronology(device_id: str, tracker_state: dict) -> List[Dict]:
    """
    Reconstructs the Incident Timeline for Legal Defense.
    Aggregates: Permit, History, Alerts, and Operator Actions.
    """
    timeline = []
    
    # 1. PERMIT ISSUANCE (Origin)
    # In real app, we'd parse the issue date from blockchain. Mocking it relative to now.
    # Assuming the user started 4 hours ago.
    now = time.time()
    did = tracker_state.get('did', 'unknown')
    permit_str = get_permit_info(did)
    
    timeline.append({
        "time": now - 14400, # -4 hours
        "event": "PERMIT_VALIDATED",
        "actor": "PRAHARI_GATE_A",
        "details": permit_str
    })
    
    # 2. SIGNIFICANT MOVEMENTS (Route History)
    # Mocking a few breadcrumbs
    timeline.append({
        "time": now - 10800, # -3 hours
        "event": "CHECKPOINT_CROSSING",
        "actor": "SENSOR_NET_04",
        "details": "Crossed Tawang Main Gate. Speed: 45km/h"
    })
    
    timeline.append({
        "time": now - 7200, # -2 hours
        "event": "ZONE_ENTRY",
        "actor": "GEOFENCE_ENGINE",
        "details": "Entered Caution Zone (Yellow)"
    })
    
    # 3. ALERT HISTORY (The Escalation)
    # Scan LATEST_ALERTS for this device
    # Keys like "{device_id}_{TYPE}"
    for key, alert in LATEST_ALERTS.items():
        if alert['device_id'] == device_id:
            # Creation
            timeline.append({
                "time": alert['timestamp'],
                "event": f"ALERT_TRIGGERED: {alert['severity']}",
                "actor": "ANOMALY_DETECTION",
                "details": f"{alert['type']} - {alert['message']}"
            })
            
            # Acknowledge
            if alert.get('ack_by'):
                timeline.append({
                    "time": alert.get('ack_time', alert['timestamp'] + 60),
                    "event": "ALERT_ACKNOWLEDGED",
                    "actor": alert['ack_by'],
                    "details": "Operator took cognizance."
                })
                
            # Resolution
            if alert.get('resolved_by'):
                timeline.append({
                    "time": alert.get('resolved_time', alert['timestamp'] + 300),
                    "event": "ALERT_RESOLVED",
                    "actor": alert['resolved_by'],
                    "details": "Incident marked as Resolved."
                })

    # Sort Chronologically
    timeline.sort(key=lambda x: x['time'])
    
    return timeline
