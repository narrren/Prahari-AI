import hashlib
import json
import time

# Simulation of a decentralized IPFS Node
# In production, this would connect to Infura IPFS or a local Go-IPFS node

IPFS_STORE = {}

def upload_to_ipfs(file_bytes: bytes, explicit_mime_type: str = "application/pdf") -> str:
    """
    Uploads bytes to the IPFS Mock Network.
    Returns: CID (Content Identifier) - effectively a hash starting with 'Qm'.
    """
    # 1. Simulate CID generation (SHA256 usually, IPFS uses multihash)
    # We use a mock 'Qm' prefix to look like real IPFS
    content_hash = hashlib.sha256(file_bytes).hexdigest()
    cid = f"Qm{content_hash[:44]}" # IPFS CIDs are usually 46 chars
    
    # 2. Store in "Network"
    IPFS_STORE[cid] = {
        "content": file_bytes,
        "mime": explicit_mime_type,
        "timestamp": time.time(),
        "replicas": 3 # Simulated replication on 3 nodes
    }
    
    print(f"[IPFS_NODE] Content Pinned. CID: {cid} | Size: {len(file_bytes)} bytes")
    return cid

def get_from_ipfs(cid: str):
    return IPFS_STORE.get(cid)
