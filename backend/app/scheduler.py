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
    Detects dropped signals (>1800s aka 30 min) in High Risk Zones.
    For Demo purposes, we might shorten this timeout.
    """
    print("SCHEDULER: Starting Dead Man's Switch Monitor...")
    
    # Check every 60 seconds
    while True:
        try:
            now = time.time()
            # Iterate over a COPY of values to avoid concurrent modification issues
            for device_id, state in list(LATEST_POSITIONS.items()):
                
                # Check 1: Time Drift
                # "last_seen" could be 'timestamp' key in our schema
                last_seen = state.get('timestamp', 0)
                elapsed = now - last_seen
                
                # Check 2: Zone Risk
                from app.services.geofence import check_geofence_breach, GeoPoint
                gp = GeoPoint(lat=state['location']['lat'], lng=state['location']['lng'])
                zone = check_geofence_breach(gp)
                
                is_high_risk = zone and zone.risk_level == "HIGH"
                
                # Threshold: 30 minutes (1800s) default, or 60s for DEMO
                THRESHOLD = 60 if True else 1800 # Using 60s for immediate demo effect
                
                if elapsed > THRESHOLD and is_high_risk:
                    # Alert Generation
                    did = state.get('did', 'unknown')
                    print(f"DEAD MAN ALERT: {did} silent for {int(elapsed)}s in RED ZONE")
                    
                    alert = {
                        "alert_id": str(uuid.uuid4()),
                        "device_id": device_id,
                        "did": did,
                        "type": "SIGNAL_LOST_CRITICAL",
                        "severity": "CRITICAL",
                        "timestamp": now,
                        "location": state['location'],
                        "message": f"CRITICAL: Signal Lost for DID {did} in HIGH RISK ZONE ({zone.name}). Last contact: {int(elapsed/60)} min ago. Initiate Search."
                    }
                    
                    # Broadcast
                    await notify_alert(alert)
                    
        except Exception as e:
            print(f"Scheduler Error: {e}")
            
        await asyncio.sleep(60)
