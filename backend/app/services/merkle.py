import hashlib
from typing import List

class MerkleTree:
    def __init__(self):
        self.leaves = []
        self.root = None

    def add_leaf(self, data: str):
        """Adds a data string to the tree (hashes it first)."""
        data_hash = hashlib.sha256(data.encode()).hexdigest()
        self.leaves.append(data_hash)

    def build(self) -> str:
        """
        Builds the Merkle Tree and returns the Root Hash.
        """
        if not self.leaves:
            return None
            
        current_layer = self.leaves
        
        while len(current_layer) > 1:
            next_layer = []
            for i in range(0, len(current_layer), 2):
                node1 = current_layer[i]
                if i + 1 < len(current_layer):
                    node2 = current_layer[i+1]
                else:
                    node2 = node1 # Duplicate last node if odd number
                
                # Combine and Hash
                combined = hashlib.sha256((node1 + node2).encode()).hexdigest()
                next_layer.append(combined)
            current_layer = next_layer
            
        self.root = current_layer[0]
        return self.root

def generate_telemetry_merkle_root(telemetry_batch: List[dict]) -> str:
    """
    Takes a batch of telemetry objects, serializes them canonically, 
    and produces a Merkle Root for Blockchain Anchoring.
    """
    tree = MerkleTree()
    for packet in telemetry_batch:
        # Canonical string representation for consistency
        # e.g. "device_id|timestamp|lat|lng"
        canonical = f"{packet['device_id']}|{packet['timestamp']}|{packet['location']['lat']}|{packet['location']['lng']}"
        tree.add_leaf(canonical)
    
    return tree.build()
