import json
import time
import random

# Tawang, Arunachal Pradesh
START_LAT = 27.5861
START_LNG = 91.8594

# Red Zone (Landslide Area)
RED_ZONE_LAT = 27.5880
RED_ZONE_LNG = 91.8620

def generate_telemetry_sequence():
    data = []
    
    # User ID and DID
    device_id = "device_alpha_001"
    did = "did:eth:0x1234567890abcdef"
    
    lat = START_LAT
    lng = START_LNG
    
    ts = time.time()
    
    # 1. Normal Movement (0-10 mins)
    for i in range(10):
        ts += 60 # 1 minute steps
        lat += 0.0001
        lng += 0.0001
        data.append({
            "device_id": device_id,
            "did": did,
            "timestamp": ts,
            "location": {"lat": lat, "lng": lng},
            "speed": 1.5, # Walking speed m/s
            "heading": 45.0,
            "battery_level": 95.0 - (i * 0.1),
            "is_panic": False
        })

    # 2. Entering Red Zone (11-15 mins)
    # Move quickly towards Red Zone
    for i in range(5):
        ts += 60
        lat = RED_ZONE_LAT - 0.0002 + (i * 0.00005) # Approaching
        lng = RED_ZONE_LNG - 0.0002 + (i * 0.00005)
        data.append({
            "device_id": device_id,
            "did": did,
            "timestamp": ts,
            "location": {"lat": lat, "lng": lng},
            "speed": 1.5,
            "heading": 45.0,
            "battery_level": 93.0,
            "is_panic": False
        })
        
    # 3. Simulated Fall / Inactivity (16-45 mins)
    # Stopped moving at Red Zone edge
    lat = RED_ZONE_LAT
    lng = RED_ZONE_LNG
    for i in range(30):
        ts += 60
        # Jitter GPS noise
        jit_lat = lat + random.uniform(-0.00001, 0.00001)
        jit_lng = lng + random.uniform(-0.00001, 0.00001)
        
        data.append({
            "device_id": device_id,
            "did": did,
            "timestamp": ts,
            "location": {"lat": jit_lat, "lng": jit_lng},
            "speed": 0.0,
            "heading": 0.0,
            "battery_level": 90.0 - (i * 0.05),
            "is_panic": False
        })

    # 4. Active SOS (Panic Button)
    ts += 10
    data.append({
        "device_id": device_id,
        "did": did,
        "timestamp": ts,
        "location": {"lat": lat, "lng": lng},
        "speed": 0.0,
        "heading": 0.0,
        "battery_level": 88.0,
        "is_panic": True # SOS Triggered!
    })

    return data

if __name__ == "__main__":
    trek_data = generate_telemetry_sequence()
    with open("trek_data.json", "w") as f:
        json.dump(trek_data, f, indent=2)
    print(f"Generated {len(trek_data)} telemetry points in trek_data.json")
