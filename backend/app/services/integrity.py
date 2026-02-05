import hashlib
import json
import time
from typing import List, Dict

# Mock Blockchain State
BLOCKCHAIN_ANCHOR = {
    "model_hash": None, # Will be set on init
    "last_merkle_root": "0xAB7...99",
    "pqc_enabled": True
}
SYSTEM_LOCKDOWN = False

MODEL_PATH = "ai_model_weights.bin"

def calculate_file_hash(filepath: str) -> str:
    try:
        hasher = hashlib.sha256()
        with open(filepath, 'rb') as f:
            buf = f.read()
            hasher.update(buf)
        return hasher.hexdigest()
    except FileNotFoundError:
        return "MISSING_FILE"

def init_integrity_monitor():
    """Hashes the 'clean' model at startup to establish Ground Truth on Blockchain"""
    current_hash = calculate_file_hash(MODEL_PATH)
    BLOCKCHAIN_ANCHOR["model_hash"] = current_hash
    print(f"INTEGRITY: AI Model Anchored on Blockchain. Hash: {current_hash[:10]}...")

def verify_model_integrity() -> Dict:
    global SYSTEM_LOCKDOWN
    current_hash = calculate_file_hash(MODEL_PATH)
    expected_hash = BLOCKCHAIN_ANCHOR["model_hash"]
    
    match = (current_hash == expected_hash)
    
    if not match:
        SYSTEM_LOCKDOWN = True
        print(f"CRITICAL: CODE_COMPROMISE DETECTED. SYSTEM LOCKDOWN INITIATED. Expected {expected_hash}, Got {current_hash}")
    
    return {
        "status": "SECURE" if match else "COMPROMISED",
        "current_hash": current_hash,
        "expected_hash": expected_hash,
        "checked_at": time.time()
    }

def is_system_locked():
    return SYSTEM_LOCKDOWN

def generate_merkle_proof(target_data: Dict, all_data: List[Dict]) -> Dict:
    """
    Simulates a Merkle Proof generation for the 'Forensic Time-Traveler'.
    In a real system, this walks the tree. Here we simulate the path.
    """
    # 1. Leaf Hash
    target_str = json.dumps(target_data, sort_keys=True)
    leaf_hash = hashlib.sha256(target_str.encode()).hexdigest()
    
    # 2. Simulate Siblings (Mocking the tree structure for demo)
    # We provide 3 dummy sibling hashes to prove the path to the Root
    siblings = [
        {"hash": hashlib.sha256(b"sibling_1").hexdigest(), "position": "left"},
        {"hash": hashlib.sha256(b"sibling_2").hexdigest(), "position": "right"},
        {"hash": hashlib.sha256(b"sibling_3").hexdigest(), "position": "left"}
    ]
    
    # Calculate expected root based on this path
    current_hash = leaf_hash
    for sibling in siblings:
        if sibling["position"] == "left":
            combined = sibling["hash"] + current_hash
        else:
            combined = current_hash + sibling["hash"]
        current_hash = hashlib.sha256(combined.encode()).hexdigest()
        
    return {
        "target_leaf_hash": leaf_hash,
        "siblings": siblings,
        "calculated_root": current_hash,
        "blockchain_root": current_hash # In a valid proof, these match
    }
