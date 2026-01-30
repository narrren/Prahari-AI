import time
import asyncio
import uuid
from decimal import Decimal
from app.core.shared_state import LATEST_POSITIONS
from app.services.db import get_table
from app.models import Alert, AlertType, GeoPoint
from app.services.geofence import check_geofence_breach
from app.services.websocket import notify_alert
from app.core.config import settings

# If no signal for X seconds, define as LOST.
# Using settings threshold or a custom shorter one for demo
LOITERING_THRESHOLD = 60 # 60 seconds for Dead Man Demo
DEAD_MAN_THRESHOLD = settings.INACTIVITY_THRESHOLD_SECONDS # 30 mins default

async def run_dead_man_switch_loop():
    """
    Simulated Lambda running on a schedule (every 2 mins in prompt, every 30s here for demo).
    """
    print("DEAD MAN SWITCH: Monitor Activated...")
    while True:
        try:
            current_time = time.time()
            
            # Iterate through all known live trackers
            # We copy keys to avoid runtime error if dict changes size
            active_devices = list(LATEST_POSITIONS.values())
            
            for device_data in active_devices:
                device_id = device_data['device_id']
                last_seen = device_data['timestamp']
                
                # Time Delta
                delta = current_time - last_seen
                
                # Check 1: Is it stale?
                if delta > DEAD_MAN_THRESHOLD:
                    # Check 2: Is it in High Risk Zone?
                    # We need to construct GeoPoint from dict
                    location = GeoPoint(**device_data['location'])
                    zone = check_geofence_breach(location)
                    
                    if zone and zone.risk_level == "HIGH":
                        # CRITICAL: DEAD MAN SWITCH TRIGGERED
                        # "Signal Lost in Restricted Zone"
                        
                        # Generate Alert
                        print(f"DEAD MAN TRIGGER: {device_id} lost for {delta}s in {zone.name}")
                        
                        alert = Alert(
                            alert_id=str(uuid.uuid4()),
                            device_id=device_id,
                            did=device_data.get('did', 'unknown'),
                            type=AlertType.INACTIVITY, # Or create a new SIGNAL_LOST type
                            severity="CRITICAL",
                            timestamp=current_time,
                            location=location,
                            message=f"DEAD MAN SWITCH: Signal Lost in High Risk Zone ({zone.name}). Last seen {int(delta/60)} mins ago."
                        )
                        
                        # Notify FE
                        await notify_alert(alert.model_dump())
                        
                        # Save to DB
                        a_table = get_table('Prahari_Alerts')
                        a_item = alert.model_dump()
                        a_item['location'] = {k: Decimal(str(v)) for k, v in a_item['location'].items()}
                        a_item['timestamp'] = Decimal(str(a_item['timestamp']))
                        a_table.put_item(Item=a_item)
                        
                        # Optional: Mark as "Processed" to avoid spamming alerts every loop?
                        # For now, simplistic loop.

        except Exception as e:
            print(f"DeadManMonitor Error: {e}")
            
        # Run every 2 minutes (120s) as per prompt, or shorter for debugging
        await asyncio.sleep(60) 
