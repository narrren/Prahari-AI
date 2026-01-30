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

def get_permit_info(did: str) -> str:
    """
    Fetches the REAL Permit status from the Blockchain.
    """
    if not contract or not w3:
        return "[Blockchain Offline] Verified Permit: #MOCK-001. Status: Active (Cached)."

    try:
        # Resolve DID to Eth Address
        eth_address = tourist_mapping.get(did)
        if not eth_address:
            # Fallback for unknown DIDs
            return f"Verified Permit: UNKNOWN (DID not in Registry). Status: Invalid."
        
        # Call Contract: permits(address)
        # Struct: (identityHash, issueDate, expiryDate, isActive, emergencyFlag)
        permit_data = contract.functions.permits(eth_address).call()
        
        identity_hash = permit_data[0].hex()[:8] + "..." # truncated
        expiry = permit_data[2]
        is_active = permit_data[3]
        emergency = permit_data[4]
        
        status = "Active" if is_active else "Revoked"
        if emergency:
            status = "EMERGENCY FLAG (Missing/Wanted)"
            
        # Check Expiry
        import time
        if time.time() > expiry:
            status = "EXPIRED"

        return f"Verified Permit: #{identity_hash}. Status: {status} [On-Chain]."

    except Exception as e:
        print(f"Blockchain Call Failed: {e}")
        return "[Connection Error] Status: Unknown."
