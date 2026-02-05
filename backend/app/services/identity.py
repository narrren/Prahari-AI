import json
import os
from web3 import Web3

# Load Contract Configuration
CONFIG_PATH = os.path.join(os.path.dirname(__file__), "../core/contract_config.json")

w3 = None
contract = None
tourist_mapping = {}

try:
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, "r") as f:
            config = json.load(f)
            
        w3 = Web3(Web3.HTTPProvider(config["network_url"]))
        contract = w3.eth.contract(address=config["contract_address"], abi=config["abi"])
        tourist_mapping = config.get("tourist_mapping", {})
        print("Identity Service: Connected to Blockchain.")
    else:
        print("Identity Service: No contract config found. Using Mock.")
except Exception as e:
    print(f"Identity Service Error: {e}")

# ... (imports)
import time
from app.core.shared_state import SYSTEM_METRICS

# ... (setup)

# Resilience: In-Memory Cache for Permits
PERMIT_CACHE = {}

def get_permit_info(did: str) -> str:
    """
    Fetches Permit status with FAILURE MODE HANDLING.
    Logic: Chain -> Cache (24h Grace) -> Fail
    """
    global PERMIT_CACHE
    
    # 1. Fast Path: Check if Circuit Breaker is active (mocked by w3 check)
    if not contract or not w3:
        # Mock specific response for resiliency demo if setup failed
        return "[Blockchain Offline] Verified Permit: #MOCK-001. Status: Active (Cached/SafeMode)."

    try:
        # 2. Try Real-Time Chain Verification
        eth_address = tourist_mapping.get(did)
        if not eth_address:
             # Logic for unregistered DIDs
             return f"Verified Permit: UNKNOWN (DID not in Registry). Status: Invalid."

        start_ts = time.time()
        permit_data = contract.functions.permits(eth_address).call()
        latency = (time.time() - start_ts) * 1000
        
        # Parse
        identity_hash = permit_data[0].hex()[:8] + "..."
        expiry = permit_data[2]
        is_active = permit_data[3]
        emergency = permit_data[4]
        
        status = "Active" if is_active else "Revoked"
        if emergency: status = "EMERGENCY FLAG"
        if time.time() > expiry: status = "EXPIRED"
        
        result_str = f"Verified Permit: #{identity_hash}. Status: {status} [On-Chain]"
        
        # 3. Update Cache & Health
        PERMIT_CACHE[did] = {
            "data": result_str,
            "timestamp": time.time(),
            "raw_status": status
        }
        SYSTEM_METRICS['services']['blockchain'] = 'CONNECTED' # Heal
        
        return result_str

    except Exception as e:
        print(f"BLOCKCHAIN FAILURE: {e}")
        
        # 4. Failure Mode Handling
        SYSTEM_METRICS['services']['blockchain'] = 'DEGRADED/OFFLINE'
        
        cached = PERMIT_CACHE.get(did)
        if cached:
            # Grace Window Validation (e.g., 24 hours)
            age = time.time() - cached['timestamp']
            if age < 86400: # 24 hours
                return f"{cached['data']} (Source: Offline Cache, Age: {int(age/60)}m). Confidence: MEDIUM."
            else:
                return f"{cached['data']} (Source: STALE CACHE). Confidence: LOW."
        
        return "[CRITICAL] Blockchain Unreachable & No Cache. Manual Verify Required."

import hashlib

# Hash Chain State for Forensic Readiness
LAST_LOG_HASH = "00000000000000000000000000000000" # Genesis Hash

def log_audit_event(admin_id: str, tourist_did: str, action: str, doc_hash: str) -> str:
    """
    Writes an immutable Audit Log to the Blockchain using Forensic Hash Chaining.
    Returns the Transaction Hash (TXID).
    """
    global LAST_LOG_HASH
    
    # Forensic Hash Chaining (Local Tamper Evidence)
    timestamp = time.time()
    current_entry = f"{admin_id}:{tourist_did}:{action}:{doc_hash}:{timestamp}"
    
    # New Hash = SHA256(Previous Hash + Current Content)
    chain_hash = hashlib.sha256(f"{LAST_LOG_HASH}{current_entry}".encode()).hexdigest()
    
    print(f"FORENSIC_LOG: Chained Entry {chain_hash[:10]}... <-- Parent {LAST_LOG_HASH[:10]}...")
    
    # Update Chain Tip
    LAST_LOG_HASH = chain_hash

    if not contract or not w3:
        return f"0xMOCK_TXID_CHAIN_{chain_hash[:8]}"

    try:
        # Resolve DID
        tourist_addr = tourist_mapping.get(tourist_did)
        if not tourist_addr:
             # Use a dummy address if DID is unknown, just to log *something*
             tourist_addr = "0x0000000000000000000000000000000000000000"

        # Authority Account (Deployer)
        authority_acc = w3.eth.accounts[0] 
        
        # Send Transaction
        # We embed the forensic hash in the log message itself
        log_message = f"ADMIN:{admin_id} ACT:{action} LINK:{chain_hash[:8]}"
        
        tx_hash = contract.functions.logIncidentAction(
            tourist_addr, 
            log_message, 
            doc_hash
        ).transact({'from': authority_acc})
        
        return w3.to_hex(tx_hash)
        
    except Exception as e:
        print(f"Audit Log Failed: {e}")
        return "0xFAIL"
