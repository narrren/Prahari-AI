# PRAHARI-AI: The Sentinel System (V4.1 Defense-Grade)

## 1. How It Works: The "Sentinel Loop"
Understanding the data flow is key to operating the system.

1.  **Generation (The Source)**: The `traffic_generator.py` script acts as GPS trackers. It sends **Signed & Encrypted** JSON packets to the Cloud API every second.
2.  **Ingestion (The Backbone)**:
    *   **Zero Trust Check**: Validates Device Fingerprint, mTLS Cert, and **HMAC Signature** before accepting data.
    *   **Fast Path**: Caches location (Redis pattern) and broadcasts via WebSocket.
    *   **AI Processing**: Evaluates packet against Geofences (Red Zones) and Anomaly Models.
    *   **Slow Path**: Persists data to DynamoDB and anchors hashes to the Blockchain.
3.  **Visualization (The Command Centre)**: The React Dashboard listens to the WebSocket.
    *   **Security HUD**: Displays Blockchain health and Merkle Root status.
    *   **Mission Control**: Prioritizes "Critical" alerts (SOS) over warnings.
4.  **Action (The Governance)**:
    *   The Admin clicks **"GEN E-FIR"**.
    *   The system generates a PDF, uploads it to **IPFS**, and logs the CID on the **Blockchain**.

---

## 2. Quick Start Guide

### Step 1: Start Infrastructure (Docker)
Spin up the AWS Simulator (LocalStack) and Blockchain Testnet (Ganache).
```bash
docker-compose up -d
```
*Wait 10 seconds for services to initialize.*

### Step 2: Initialize Systems
We need to deploy the Smart Contract, issue mock permits, and create DB tables.
```bash
# Deploys contract & issues permits to the 4 simulation DIDs
python scripts/deploy_contract.py

# Creates the 'Prahari_Telemetry' and 'Prahari_Alerts' tables
python backend/database/setup_dynamodb.py
```

### Step 3: Start the Brain (Backend)
This runs the FastAPI service, AI Engine, and WebSocket Server.
```bash
# In terminal 1
uvicorn backend.app.main:app --reload
```

### Step 4: Launch Mission Control (Frontend)
```bash
# In terminal 2
cd frontend/dashboard
npm run dev
```
👉 **Open Browser**: [http://localhost:5173](http://localhost:5173)

### Step 5: Trigger the "Stress Test" (Simulation)
This script simulates 5 concurrent units with **Cryptographic Attestation**.
```bash
# In terminal 3
python traffic_generator.py
```

### Step 6: System Verification
Run the integration suite to verify the full governance loop.
```bash
python backend/tests/integration_test.py
```

### Step 7: Cybersecurity Simulations (Defense Demo)
Demonstrate the system's resilience against active attacks.
1.  **Replay Attack**: The integration test captures a valid packet and re-sends it. Watch the logs for: `✅ Replay Attack Blocked: 401`.
2.  **Cyber Lockdown**: The test floods the auth endpoint with invalid tokens. Watch the backend enter **Defense Mode**, rejecting requests with `503 Service Unavailable`.

### Step 8: Forensic Audit
Check the terminal output for **Hash Chaining**:
```text
FORENSIC_LOG: Chained Entry 8f2a... matched to Parent 3b1c...
```
This proves that the audit trail is strictly sequenced and tamper-evident.

---

## 3. Important: Security Credentials
*   **API Key**: `dev-secret` (Configured in `.env`)
*   **Device Secrets**: Hardcoded in `backend/app/services/identities.py` for simulation (e.g., `sk_alp_01`).
*   **Blockchain**: Uses local Ganache accounts (Account 0 = Admin).

