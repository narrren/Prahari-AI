import requests
import time
import random
import os
from dotenv import load_dotenv

# Load env for API Key
load_dotenv()
API_KEY = os.getenv("AUTH_API_KEY", "prahari-sec-key-123")

# Config
API_URL = "http://localhost:8000/api/v1/telemetry" # Updated to correct endpoint
HEADERS = {"x-api-key": API_KEY}

# North East Coordinates (Tawang Area) - Safe Path
SAFE_PATH = [
    (27.581, 91.881), (27.582, 91.882), (27.583, 91.883),
    (27.5815, 91.8815), (27.5825, 91.8825)
]

# Inside the geofence (Tawang Landslide Zone)
RED_ZONE_PATH = [
    (27.5880, 91.8620), (27.5882, 91.8618), (27.5878, 91.8622)
]

def send_ping(t_id, p_id, lat, lng, speed=5.0, sos=False):
    payload = {
        "device_id": t_id,      # My schema uses device_id
        "did": p_id,            # My schema maps 'did' to permit usually, but let's use p_id here as DID
        "location": { "lat": lat, "lng": lng },
        "speed": speed,
        "heading": random.randint(0, 360),
        "battery_level": 85.0,
        "is_panic": sos,
        "timestamp": time.time()
    }
    
    # Note: My backend expects TelemetryData model structure:
    # { device_id, did, timestamp, location: {lat, lng}, speed, heading, battery_level, is_panic }
    
    try:
        response = requests.post(API_URL, json=payload, headers=HEADERS)
        if response.status_code == 200:
             data = response.json()
             risk = data.get('risk', {}).get('score', 'N/A')
             print(f"[{t_id}] Risk: {risk} | Status: {response.status_code} | SOS: {sos}")
        else:
             print(f"[{t_id}] Failed: {response.status_code} - {response.text}")
             
    except Exception as e:
        print(f"Connection Error: {e}")

def run_simulation():
    print("🚀 Starting PRAHARI-AI Production Simulation (Stress Test)...")
    print(f"Target: {API_URL}")
    print("Press Ctrl+C to stop.")
    
    while True:
        # 1. THE SAFE TOURIST (Green Status)
        pos = random.choice(SAFE_PATH)
        # Adding jitter
        lat = pos[0] + random.uniform(-0.0001, 0.0001)
        lng = pos[1] + random.uniform(-0.0001, 0.0001)
        send_ping("T-SAFE-01", "did:polygon:safe01", lat, lng)

        # 2. THE TRESPASSER (Triggers RED_ZONE_BREACH)
        pos = random.choice(RED_ZONE_PATH)
        lat = pos[0] + random.uniform(-0.0001, 0.0001)
        lng = pos[1] + random.uniform(-0.0001, 0.0001)
        send_ping("T-BREACH-99", "did:polygon:intruder", lat, lng)

        # 3. THE ACCIDENT (Speed = 0, triggers STAGNATION)
        # Sitting at a random spot in safe zone but not moving
        send_ping("T-FALL-22", "did:polygon:fallen", 27.582, 91.882, speed=0.0)

        # 4. THE SOS (Immediate Critical Alert)
        send_ping("T-SOS-SOS", "did:polygon:sos", 27.581, 91.881, sos=True)

        print("-" * 30)
        time.sleep(3) # Faster than 5s for demo responsiveness

if __name__ == "__main__":
    run_simulation()
