# PRAHARI-AI: The Sentinel System (Master Guide)

## 1. How It Works: The "Sentinel Loop"
Understanding the data flow is key to operating the system.

1.  **Generation (The Source)**: The `simulation.py` script acts as GPS trackers on 4 virtual tourists. It sends encrypted JSON packets (Telemetry) to the Cloud API every second.
2.  **Ingestion (The Backbone)**:
    *   **Fast Path**: The API immediately caches the location (Redis pattern) and broadcasts it via WebSocket to the Dashboard for <50ms latency.
    *   **AI Processing**: Concurrently, the `SentinelAI` engine evaluates the packet against Geofences, Time of Day, and Weather.
    *   **Slow Path**: Background workers persist the data to DynamoDB and check for "Dead Man" signals (silence).
3.  **Visualization (The Command Centre)**: The React Dashboard listens to the WebSocket.
    *   **Context Awareness**: If the AI flags a High Risk (score > 50), the Map automatically switches to **Satellite Mode**.
    *   **Mission Control**: The Sidebar prioritizes "Critical" alerts (SOS/Red Zone) over "Warnings" (Stagnation).
4.  **Action (The Governance)**:
    *   The Admin clicks **"GEN E-FIR"** on an alert.
    *   The system generates a PDF, hashes it, and logs the action on the **Blockchain** (Audit Trail).
    *   A legally admissible document is downloaded.

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
This script simulates the 4 concurrent scenarios (Safe, Breach, Fall, SOS).
```bash
# In terminal 3
python scripts/simulation.py
```

---

## 3. What To Look For (Demo Highlights)

### 🔴 The Red Zone Breach
*   **Watch**: The "Breach Tourist" (T-BREACH-99) moves into the red polygon.
*   **Effect**: The Map automatically flips to **Satellite Mode**. The Sidebar flashes RED.

### ⚡ The Dead Man's Switch (Stagnation)
*   **Watch**: The "Accident Tourist" (T-FALL-22) stops moving.
*   **Effect**: After a few seconds, the AI flags "STAGNATION". The risk score creeps up.

### ⛈️ The Weather Engine
*   **Watch**: Notice the Risk Score jump by +30 points when a tourist enters the "Storm Micro-Climate" near the border.
*   **Log**: Check the backend terminal to see "SEVERE_WEATHER_WARNING" logs.

### ⚖️ The E-FIR (Governance)
*   **Action**: Click the "GEN E-FIR" button on any alert card.
*   **Result**: Download a PDF. Notice the **QR Code** and the **Blockchain TXID** at the top. This proves the system is tamper-proof.
