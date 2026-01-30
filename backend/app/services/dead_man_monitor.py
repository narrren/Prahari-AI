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
from app.services.identity import get_permit_info

# --- STEP 2: CLOUD-SIDE DEAD MAN'S LOGIC ---

# 60s for Demo (Real world: 3600s / 1 hour)
DEAD_MAN_TIMEOUT = 60 

async def trigger_dead_man_alert(device_id, zone_name, elapsed_time, device_data):
    """
    Helper to generate and dispatch the CRITICAL ALERT.
    """
    print(f"DEAD MAN TRIGGER: {device_id} lost for {elapsed_time:.1f}s in {zone_name}")
    
    did = device_data.get('did', 'unknown')
    permit_str = get_permit_info(did)
    
    alert = Alert(
        alert_id=str(uuid.uuid4()),
        device_id=device_id,
        did=did,
        type=AlertType.INACTIVITY, 
        severity="CRITICAL",
        timestamp=time.time(),
        location=GeoPoint(**device_data['location']),
        message=f"Alert: DID {did} has gone silent in restricted zone: {zone_name}. {permit_str} Last signal {int(elapsed_time/60)} min ago."
    )
    
    # 1. Notify Frontend (Socket)
    await notify_alert(alert.model_dump())
    
    # 2. Persist to DB
    try:
        a_table = get_table('Prahari_Alerts')
        a_item = alert.model_dump()
        a_item['location'] = {k: Decimal(str(v)) for k, v in a_item['location'].items()}
        a_item['timestamp'] = Decimal(str(a_item['timestamp']))
        a_table.put_item(Item=a_item)
    except Exception as e:
        print(f"Failed to persist Dead Man Alert: {e}")

async def dead_mans_switch_check(device_data):
    """
    The Core Logic as per Step 2 Requirement.
    Checks if a tourist has 'gone dark' in a dangerous area.
    """
    tourist_id = device_data['device_id']
    last_seen_timestamp = device_data['timestamp']
    
    # Get Current Zone Status
    location = GeoPoint(**device_data['location'])
    zone = check_geofence_breach(location)
    current_zone_risk = zone.risk_level if zone else "SAFE"
    
    # Check Timeout
    elapsed = time.time() - last_seen_timestamp
    
    # Logic: "if elapsed > timeout and current_zone == HighRisk"
    if elapsed > DEAD_MAN_TIMEOUT and current_zone_risk == "HIGH":
        await trigger_dead_man_alert(tourist_id, zone.name, elapsed, device_data)

async def run_dead_man_switch_loop():
    """
    Background Task (Lambda Pattern).
    Polls every 60s.
    """
    print("DEAD MAN SWITCH: Cloud Monitor Activated...")
    while True:
        try:
            # Snapshot of active devices
            active_devices = list(LATEST_POSITIONS.values())
            
            for device_data in active_devices:
                await dead_mans_switch_check(device_data)

        except Exception as e:
            print(f"DeadManMonitor Error: {e}")
            
        await asyncio.sleep(60) 
