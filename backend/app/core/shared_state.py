from app.models import SystemMode, CyberHudState
from collections import defaultdict

# Shared In-Memory State for Prahari-AI Backend
# This acts as a localized Redis replacement for the demo.

# Latest known positions of all devices. 
# Format: { "device_id": { ...TelemetryData... } }
LATEST_POSITIONS = {}

# Kalman Filter states
KALMAN_STATES = {}
# Biometric History for "Turing Test"
BIOMETRIC_HISTORY = defaultdict(list)

# Active Alerts Cache (Stateful Lifecycle)
# Format: { "device_id_TYPE": { ...AlertData... } }
LATEST_ALERTS = {}

# Governance & Accountability Logs (V3.2)
DECISION_HISTORY = [] # List[DecisionRecord]

# Forensic Verification Logs (V5.0)
FORENSIC_LOGS = []

# Demo Resilience: In-Memory Telemetry History (For VCR when DB offline)
# Format: { "device_id": [ ...TelemetryData... ] }
TELEMETRY_HISTORY = defaultdict(list)

# Global System State (V3.2 Resilience)
SYSTEM_MODE = SystemMode.NORMAL

# V5.0 SOAR HUD State
CYBER_HUD = CyberHudState(
    threat_level="LOW",
    active_countermeasures=[],
    blacklisted_ips=[]
)

# System Health Metrics (Observability)
SYSTEM_METRICS = {
    "ingestion_count": 0,    # Total packets since boot
    "ingestion_rate": 0.0,   # Packets/sec
    "start_time": 0.0,       # Initialized at boot
    "active_users": 0,       
    "alerts_active": 0,
    "last_db_latency": 0.0,
    "kalman_failures": 0,
    "mode": "NORMAL", # V3.2
    "merkle_root": "PENDING", # V4.1
    "chain_height": 150000,   # V4.1
    "consensus_status": "LOCKED (2/3)" # V4.1
}

def hydrate_cache():
    """
    On cold boot, fetch the latest known state of all trackers from DynamoDB.
    This fixes the 'Persistence Gap' (Task A).
    """
    from app.services.db import get_table
    try:
        print("BOOTSTRAP: Hydrating Cache from DynamoDB...")
        t_table = get_table('Prahari_Telemetry')
        # Scan last 2000 items (demo logic)
        response = t_table.scan(Limit=2000) 
        items = response.get('Items', [])
        
        count = 0
        for item in items:
            try:
                dev_id = item['device_id']
                ts = float(item['timestamp'])
                
                native_item = {
                    "device_id": dev_id,
                    "did": item.get('did', 'unknown'),
                    "timestamp": ts,
                    "location": {
                        "lat": float(item['location']['lat']),
                        "lng": float(item['location']['lng'])
                    },
                    "speed": float(item.get('speed', 0)),
                    "heading": float(item.get('heading', 0)),
                    "battery_level": float(item.get('battery_level', 100)),
                    "is_panic": item.get('is_panic', False),
                    "risk": {"score": 0, "status": "SAFE", "factors": ["RESTORED"]} 
                }
                
                # Keep newest
                if dev_id not in LATEST_POSITIONS or ts > LATEST_POSITIONS[dev_id]['timestamp']:
                    LATEST_POSITIONS[dev_id] = native_item
                    count += 1
            except:
                continue
                
        print(f"BOOTSTRAP: Hydrated {len(LATEST_POSITIONS)} active devices into memory.")
        
    except Exception as e:
        print(f"BOOTSTRAP FAILED: {e}")
