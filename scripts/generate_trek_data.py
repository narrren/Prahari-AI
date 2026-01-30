import json
import time
import random

# Tawang, Arunachal Pradesh
START_LAT = 27.5861
START_LNG = 91.8594

# Red Zone (Landslide Area)
RED_ZONE_LAT = 27.5880
RED_ZONE_LNG = 91.8620

def generate_device_data(device_id, scenario):
    data = []
    did = f"did:eth:mock:{device_id}"
    ts = time.time()
    
    # Base Position (Safe Area)
    # Scatter them slightly
    lat = START_LAT + random.uniform(-0.002, 0.002)
    lng = START_LNG + random.uniform(-0.002, 0.002)
    
    steps = 60 # 1 hour of data
    
    for i in range(steps):
        ts += 60 # 1 minute intervals
        
        # --- SCENARIO LOGIC ---
        
        # 1. SAFE TREKKER
        if scenario == "SAFE":
            # Just wanders randomly
            lat += random.uniform(-0.0001, 0.0001)
            lng += random.uniform(-0.0001, 0.0001)
            speed = 1.5
            panic = False
            
        # 2. GEOFENCE BREACHER
        elif scenario == "BREACH":
            if i < 10:
                # Move towards red zone
                target_lat = RED_ZONE_LAT
                target_lng = RED_ZONE_LNG
                lat += (target_lat - lat) * 0.1
                lng += (target_lng - lng) * 0.1
                speed = 1.5
            elif i < 30:
                # Inside Red Zone (Wander)
                lat = RED_ZONE_LAT + random.uniform(-0.00005, 0.00005)
                lng = RED_ZONE_LNG + random.uniform(-0.00005, 0.00005)
                speed = 0.5
            else:
                # Leave
                lat -= 0.0001
                lng -= 0.0001
                speed = 1.5
            panic = False

        # 3. STAGNATION (FALL)
        elif scenario == "FALL":
            if i < 15:
                lat += 0.0001
                lng += 0.0001
                speed = 1.5
            else:
                # STOP MOVING completely
                # Adds tiny GPS jitter noise
                lat += random.uniform(-0.000005, 0.000005)
                lng += random.uniform(-0.000005, 0.000005)
                speed = 0.0
            panic = False

        # 4. DEAD MAN (SIGNAL LOST)
        elif scenario == "LOST":
            if i > 20:
                break # STOP GENERATING POINTS --> LastSeen stays at T=20
            
            # Move towards High Risk before dying
            target_lat = RED_ZONE_LAT
            target_lng = RED_ZONE_LNG
            lat += (target_lat - lat) * 0.05
            lng += (target_lng - lng) * 0.05
            speed = 1.5
            panic = False

        # 5. SOS BUTTON
        elif scenario == "SOS":
            lat += random.uniform(-0.0001, 0.0001)
            lng += random.uniform(-0.0001, 0.0001)
            speed = 1.6
            
            # Trigger SOS at step 40
            if i >= 40:
                panic = True
                speed = 0.0
            else:
                panic = False
                
        # --- APPEND DATA ---
        data.append({
            "device_id": device_id,
            "did": did,
            "timestamp": ts,
            "location": {"lat": lat, "lng": lng},
            "speed": speed,
            "heading": random.uniform(0, 360),
            "battery_level": max(0, 100 - (i * 0.2)),
            "is_panic": panic
        })

    return data

def generate_full_simulation():
    all_points = []
    
    # Defne the 5 Cast Members
    cast = [
        ("T-SAFE", "SAFE"),
        ("T-BREACH", "BREACH"),
        ("T-FALL", "FALL"),
        ("T-LOST", "LOST"),
        ("T-SOS", "SOS")
    ]
    
    for device_id, scenario in cast:
        points = generate_device_data(device_id, scenario)
        all_points.extend(points)
        
    # Sort chronologically
    all_points.sort(key=lambda x: x['timestamp'])
    
    return all_points

if __name__ == "__main__":
    trek_data = generate_full_simulation()
    with open("trek_data.json", "w") as f:
        json.dump(trek_data, f, indent=2)
    print(f"Generated {len(trek_data)} points for 5 Unique Scenarios.")
