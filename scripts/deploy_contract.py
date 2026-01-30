import json
import os
from web3 import Web3
from solcx import compile_standard, install_solc

# 1. Connect to Ganache
GANACHE_URL = "http://127.0.0.1:8545"
w3 = Web3(Web3.HTTPProvider(GANACHE_URL))

if not w3.is_connected():
    print("FATAL: Cannot connect to Ganache. Ensure it is running on port 8545.")
    exit(1)

print(f"Connected to Ganache. Block Number: {w3.eth.block_number}")

# 2. Compile Solidity Contract
print("Installing solc compiler (0.8.19)...")
install_solc("0.8.19")

contract_path = "backend/blockchain/contracts/TouristPermitRegistry.sol"
with open(contract_path, "r") as file:
    contract_source_code = file.read()

print("Compiling contract...")
compiled_sol = compile_standard(
    {
        "language": "Solidity",
        "sources": {"TouristPermitRegistry.sol": {"content": contract_source_code}},
        "settings": {
            "outputSelection": {
                "*": {
                    "*": ["abi", "metadata", "evm.bytecode", "evm.sourceMap"]
                }
            }
        },
    },
    solc_version="0.8.19",
)

bytecode = compiled_sol["contracts"]["TouristPermitRegistry.sol"]["TouristPermitRegistry"]["evm"]["bytecode"]["object"]
abi = compiled_sol["contracts"]["TouristPermitRegistry.sol"]["TouristPermitRegistry"]["abi"]

# 3. Deploy Contract
# Use the first account as the deployer (Government Authority)
deployer_account = w3.eth.accounts[0]
print(f"Deploying from account: {deployer_account}")

# Instantiate Contract
TouristPermitRegistry = w3.eth.contract(abi=abi, bytecode=bytecode)

# Submit Transacton
tx_hash = TouristPermitRegistry.constructor().transact({'from': deployer_account})
tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)

contract_address = tx_receipt.contractAddress
print(f"✅ Contract Deployed at: {contract_address}")

# 4. Save Config for Backend
config_data = {
    "contract_address": contract_address,
    "abi": abi,
    "network_url": GANACHE_URL
}

output_path = "backend/app/core/contract_config.json"
with open(output_path, "w") as f:
    json.dump(config_data, f, indent=4)

print(f"Configuration saved to {output_path}")

# 5. (Optional) Issue Mock Permits for the Demo Tourists
# Issue permits for T-SAFE, T-BREACH, T-FALL, T-LOST, T-SOS
# Mock DIDs matching generate_trek_data.py
mock_dids = [
    f"did:eth:mock:T-{suffix}" for suffix in ["SAFE", "BREACH", "FALL", "LOST", "SOS"]
]
# For Ethereum address compatibility, we usually need real hex addresses.
# But our Identity Service mock might treat strings loosley. 
# However, Solidity expects `address`.
# The current simulation sends `did` as a string.
# To allow the contract to work, we need real eth addresses for these tourists.
# We will use accounts[1] to accounts[5] from Ganache for them.

print("\n--- Issuing Mock Permits ---")
contract_instance = w3.eth.contract(address=contract_address, abi=abi)

tourist_map = {}
for i, suffix in enumerate(["SAFE", "BREACH", "FALL", "LOST", "SOS"]):
    tourist_addr = w3.eth.accounts[i+1] # Skip deployer
    did_string = f"did:eth:mock:T-{suffix}" 
    
    # Store mapping for the backend to look up? 
    # Or purely rely on the fact that existing code passes "did" string.
    # The Identity Service `get_permit_info(did)` takes the `did` string.
    # It needs to map `did string` -> `eth address` to Query the Chain.
    # We will save this mapping in the config too.
    
    tourist_map[did_string] = tourist_addr
    
    # Issue Permit (Hash of "Passport data")
    id_hash = w3.keccak(text=f"PASSPORT_{suffix}")
    duration = 30 # days
    
    print(f"Issuing Permit for T-{suffix} ({tourist_addr})")
    contract_instance.functions.issuePermit(
        tourist_addr, 
        id_hash, 
        duration
    ).transact({'from': deployer_account})

# Update config with tourist mapping
config_data["tourist_mapping"] = tourist_map
with open(output_path, "w") as f:
    json.dump(config_data, f, indent=4)
print("Updated config with Tourist Address Mappings.")
