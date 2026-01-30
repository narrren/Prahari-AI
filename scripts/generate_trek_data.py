import json
import time
import random

# Tawang, Arunachal Pradesh
START_LAT = 27.5861
START_LNG = 91.8594

# Red Zone (Landslide Area)
RED_ZONE_LAT = 27.5880
RED_ZONE_LNG = 91.8620

def generate_device_path(device_id, start_offset, scenario="SAFE"):
    data = []
    did = f"did:eth:mock:{device_id}"
    
    # Randomized Start
    lat = START_LAT + start_offset[0]
    lng = START_LNG + start_offset[1]
    
    ts = time.time()
    
    # 1. Normal Movement (0-10 mins)
    steps = 15 if scenario == "SAFE" else 10
    
    for i in range(steps):
        ts += 60 # 1 minute steps
        # Random Walk Vector
        d_lat = 0.0001 + random.uniform(-0.00005, 0.00005)
        d_lng = 0.0001 + random.uniform(-0.00005, 0.00005)
        
        # If 'SAFE', maybe wander differently
        if scenario == "SAFE":
            d_lat = random.uniform(-0.0001, 0.0002)
            d_lng = random.uniform(-0.0002, 0.0002)

        lat += d_lat
        lng += d_lng
        
        data.append({
            "device_id": device_id,
            "did": did,
            "timestamp": ts,
            "location": {"lat": lat, "lng": lng},
            "speed": random.uniform(1.2, 1.8),
            "heading": random.uniform(0, 360),
            "battery_level": 95.0 - (i * 0.1),
            "is_panic": False
        })

    # 2. Scenario Branch
    if scenario == "DANGER":
        # Entering Red Zone (11-15 mins)
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
            
        # Simulated Fall / Inactivity
        lat = RED_ZONE_LAT
        lng = RED_ZONE_LNG
        for i in range(30):
            ts += 60
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

        # SOS
        ts += 10
        data.append({
            "device_id": device_id,
            "did": did,
            "timestamp": ts,
            "location": {"lat": lat, "lng": lng},
            "speed": 0.0,
            "heading": 0.0,
            "battery_level": 88.0,
            "is_panic": True
        })
        
    return data

def generate_multi_trek():
    # Device Configs
    devices = [
        # The Victim
        {"id": "T-ALPHA", "offset": (0, 0), "scenario": "DANGER"},
        # The Safe Trekkers (Scattered)
        {"id": "T-BRAVO", "offset": (0.001, 0.001), "scenario": "SAFE"},
        {"id": "T-CHARLIE", "offset": (0.001, -0.001), "scenario": "SAFE"},
        {"id": "T-DELTA", "offset": (-0.001, 0.001), "scenario": "SAFE"},
        {"id": "T-ECHO", "offset": (-0.001, -0.001), "scenario": "SAFE"},
    ]
    
    all_points = []
    
    for dev in devices:
        points = generate_device_path(dev["id"], dev["offset"], dev["scenario"])
        all_points.extend(points)
        
    # Sort by timestamp to simulate real-time interleaved stream
    all_points.sort(key=lambda x: x['timestamp'])
    
    return all_points

if __name__ == "__main__":
    trek_data = generate_multi_trek()
    with open("trek_data.json", "w") as f:
        json.dump(trek_data, f, indent=2)
    print(f"Generated {len(trek_data)} telemetry points for {set(p['device_id'] for p in trek_data)}")
