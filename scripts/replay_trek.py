import json
import requests
import time
import sys

# URL
API_URL = "http://localhost:8000/api/v1/telemetry"

def replay_trek():
    try:
        with open("trek_data.json", "r") as f:
            data = json.load(f)
    except FileNotFoundError:
        print("trek_data.json not found. Run generate_trek_data.py first.")
        return

    print(f"Replaying {len(data)} points to {API_URL}...")
    
    # Sort by timestamp just in case
    data.sort(key=lambda x: x['timestamp'])
    
    start_time = data[0]['timestamp']
    real_start_time = time.time()
    
    # Speed factor (e.g. 10x speed, or 0 for instant push, or 1 for realtime)
    # Let's do huge speed for demo to see movement quickly
    SPEED_FACTOR = 50.0 
    
    for point in data:
        # Calculate when this point should be sent relative to start
        offset = point['timestamp'] - start_time
        target_real_time = real_start_time + (offset / SPEED_FACTOR)
        
        current_time = time.time()
        wait_time = target_real_time - current_time
        
        if wait_time > 0:
            time.sleep(wait_time)
            
        # Send
        try:
            # Current real timestamp for the app to see it as "now"
            # Or keep original? The backend rule uses "timestamp" from payload.
            # But duplicate timestamps might be an issue if DynamoDB key is unique.
            # No, Key is (device_id, timestamp).
            # If we replay the SAME data multiple times, we might overwrite.
            # Let's update timestamp to NOW to simulate live stream.
            point['timestamp'] = time.time() 
            
            res = requests.post(API_URL, json=point, headers={"x-api-key": "prahari-sec-key-123"})
            if res.status_code == 200:
                print(f"Sent: {point['location']} - Panic: {point.get('is_panic')}")
            else:
                print(f"Error {res.status_code}: {res.text}")
        except Exception as e:
            print(f"Request failed: {e}")

if __name__ == "__main__":
    replay_trek()
