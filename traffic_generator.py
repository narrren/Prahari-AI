import requests
import random
import time
import json
import logging
import sys
import hmac
import hashlib

# Configure logging
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

API_URL = "http://localhost:8000/api/v1/telemetry"
API_KEY = "dev-secret"

# 4 DISTINCT USER PROFILES
DEVICES = [
    {
        "id": "ALPINIST_SAFE", 
        "did": "did:eth:0xSAFE...001", 
        "fingerprint": "hw:safe:01",
        "secret": "sk_safe",
        "type": "HUMAN_SAFE"
    },
    {
        "id": "ALPINIST_RED", 
        "did": "did:eth:0xRED...002", 
        "fingerprint": "hw:red:02",
        "secret": "sk_red",
        "type": "HUMAN_DANGER"
    },
    {
        "id": "MECH_DRONE_01", 
        "did": "did:eth:0xBOT...999", 
        "fingerprint": "hw:bot:01",
        "secret": "sk_bot",
        "type": "BOT_SPOOF"
    },
    {
        "id": "SIGNAL_LOST", 
        "did": "did:eth:0xDEAD...666", 
        "fingerprint": "hw:dead:01",
        "secret": "sk_dead",
        "type": "DEAD_MAN"
    }
]

# Tawang Coordinates
BASE_LAT = 27.5861
BASE_LNG = 91.8594

# Simulation State
STATE = {}

def init_state(device_id):
    STATE[device_id] = {
        "lat": BASE_LAT + random.uniform(-0.005, 0.005),
        "lng": BASE_LNG + random.uniform(-0.005, 0.005),
        "heading": random.uniform(0, 360),
        "speed": 1.5,
        "nonce": int(time.time() * 1000),
        "active": True
    }

def get_next_position(device, current):
    # PROFILE LOGIC
    profile = device["type"]

    if profile == "BOT_SPOOF":
        # ZERO ENTROPY: Perfect Straight Line, Constant Speed
        current["lat"] += 0.0005
        current["lng"] += 0.0005
        current["speed"] = 15.0 # Fast drone
        current["heading"] = 45.0 # Locked heading
        
    elif profile == "HUMAN_SAFE":
        # NATURAL MOVEMENT: Random Walk + Jitter
        current["lat"] += random.uniform(-0.0002, 0.0002)
        current["lng"] += random.uniform(-0.0002, 0.0002)
        current["speed"] = max(0, current["speed"] + random.uniform(-0.5, 0.5))
        current["heading"] = (current["heading"] + random.uniform(-15, 15)) % 360
        
    elif profile == "HUMAN_DANGER":
        # RED ZONE ENTRY: Move North-East towards Danger + Panic Jitter
        current["lat"] += 0.0003 # Drift North
        current["lng"] += 0.0003 # Drift East
        current["speed"] = random.uniform(2, 8) # Erratic running?
        
    elif profile == "DEAD_MAN":
        # STOP UPDATING check handled in main loop
        pass
        
    current["nonce"] += 1
    return current

def send_telemetry(device):
    # Initialize if needed
    if device["id"] not in STATE:
        init_state(device["id"])
    
    current = STATE[device["id"]]
    
    # DEAD MAN LOGIC: Only send once
    if device["type"] == "DEAD_MAN":
        if not current.get("sent_once"):
            current["sent_once"] = True
            logging.warning("SIGNAL_LOST: Sending final packet before silence...")
        else:
            return # Silent
            
    # Update Position
    get_next_position(device, current)
    
    # Construct Payload
    payload = {
        "device_id": device["id"],
        "did": device["did"],
        "timestamp": time.time(),
        "location": {"lat": current["lat"], "lng": current["lng"]},
        "speed": current["speed"],
        "heading": current["heading"],
        "battery_level": 15.0 if device["type"] == "HUMAN_DANGER" else 85.0,
        "is_panic": (device["type"] == "HUMAN_DANGER" and random.random() < 0.1)
    }
    
    # Sign Payload
    payload_string = f"{payload['device_id']}:{payload['timestamp']}:{payload['location']['lat']}:{payload['location']['lng']}"
    signature = hmac.new(
        device['secret'].encode(), 
        payload_string.encode(), 
        hashlib.sha256
    ).hexdigest()
    
    headers = {
        "x-api-key": API_KEY,
        "Content-Type": "application/json",
        "X-Device-Fingerprint": device["fingerprint"],
        "X-Client-Cert": f"CERT_{device['id']}",
        "X-Signature": signature,
        "X-Nonce": str(current["nonce"])
    }
    
    try:
        resp = requests.post(API_URL, json=payload, headers=headers, timeout=5)
        if resp.status_code == 200:
            logging.info(f"[{device['id']}] SENT OK. Risk: {resp.json().get('risk',{}).get('score',0)}")
        else:
            logging.error(f"[{device['id']}] FAILED: {resp.status_code} {resp.text}")
    except Exception as e:
        logging.error(f"[{device['id']}] ERROR: {str(e)}")

def main():
    logging.info("--- PRAHARI-AI TRAFFIC SIMULATION V5.0 ---")
    logging.info("1. ALPINIST_SAFE (Human)")
    logging.info("2. ALPINIST_RED (Danger/RedZone)")
    logging.info("3. MECH_DRONE_01 (Bot Spoof)")
    logging.info("4. SIGNAL_LOST (Dead Man Test)")
    logging.info("------------------------------------------")
    
    while True:
        for device in DEVICES:
            send_telemetry(device)
            time.sleep(0.2) # High frequency demo
        time.sleep(1)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass
