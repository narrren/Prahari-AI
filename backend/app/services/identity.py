
import hashlib

def get_permit_info(did: str) -> str:
    """
    Simulates bridging to the Blockchain Permit Registry.
    In a real app, this would call 'TouristPermitRegistry.isPermitValid(did)'.
    For the demo, we generate a deterministic Permit ID from the DID.
    """
    # Deterministic Mock Permit ID
    permit_hash = hashlib.sha256(did.encode()).hexdigest()
    permit_id = f"#{int(permit_hash[:4], 16)}" 
    
    # Mock Status (Assume Active for registered DIDs)
    status = "Active"
    
    return f"Verified Permit: {permit_id}. Status: {status}."
