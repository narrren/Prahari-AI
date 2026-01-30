# PRAHARI-AI: Technical Digest & Architectural Reference

**Version:** 2.0.0 "Pinnacle"  
**Status:** Beta / Feature Complete (Live Simulation)  
**Context:** MoDoNER Pinnacle Project (Smart Tourist Safety System)

---

## 1. Executive Summary
**PRAHARI-AI** is a comprehensive "Sentinel" system designed for the Ministry of Development of North Eastern Region (MoDoNER). Its primary objective is to ensure the safely of tourists trekking in remote, sensitive border areas (like Tawang, Arunachal Pradesh) using a blend of **Decentralized Identity (SSI)**, **Real-Time Geofencing**, and **AI-driven Anomaly Detection**.

Unlike traditional databases, PRAHARI uses a privacy-first blockchain layer for issuing digital travel permits, ensuring that government checkpoints can verify legality without exposing a tourist's full personal history (Zero-Trust architecture).

---

## 2. System Architecture
The system follows a modern **Event-Driven, Serverless-First** architecture, currently fully simulated locally using Docker.

### **2.1. Infrastructure Layer (Dockerized)**
*   **AWS Cloud Simulator (LocalStack)**:
    *   **DynamoDB**: Stores hot state (current location) and historical path data.
    *   **IoT Core (Simulated)**: Ingests high-frequency GPS telemetry via HTTP/MQTT.
*   **Blockchain Network (Ganache)**:
    *   Runs a local Ethereum testnet (Chain ID: 1337).
    *   Hosts the **TouristPermitRegistry** smart contract (Single Source of Truth).

### **2.2. Backend Intelligence (Python/FastAPI)**
*   **Sentinel Engine ("The Brain")**:
    *   **Weighted Risk Scorer**: Calculates cumulative risk (0-100) based on Spatial (Polygon Zones), Temporal (Night), and Behavioral (Inactivity) factors.
    *   **Dead Man Monitor**: Independent background service scanning for "Signal Loss" in High-Risk Zones.
*   **Identity Bridge**: Connects backend alerts to Blockchain Permit status (`web3.py`).

### **2.3. Frontend Applications**
*   **Sentinel Dashboard (React + Vite)**: A high-fidelity Control Room interface.
    *   **WebSockets**: Delivers sub-second alerts with audio feedback.
    *   **Live Map**: Leaflet.js with Custom GeoJSON Layers (Red Zones).
    *   **Digital E-FIR**: Generates PDF reports with Blockchain Proofs.

---

## 3. Module Breakdown (Implemented Status)

### **Module 1: The Immutable Identity (Blockchain Core)**
*   **Status: LIVE**
*   **Smart Contract**: `TouristPermitRegistry.sol` (Deployed).
    *   **Features**: Time-locked permits, Identity Hashing (SHA-256), Emergency Flagging.
    *   **Privacy**: Only hashes are stored on-chain. PII remains off-chain.
*   **Bridge**: `identity.py` service resolves DIDs to real-time Blockchain Permit status.

### **Module 2: High-Fidelity Telemetry & Kalman Filtering**
*   **Status: LIVE**
*   **Ingestion**: `telemetry.py` processes raw GPS data.
*   **Smoothing**: Implemented **Kalman Filters** (4-state) to reduce GPS jitter and predict velocity.
*   **Persistence**: In-Memory Cache with DynamoDB Hydration ensures no data loss on restarts.

### **Module 3: The "Brain" (Weighted AI Risk Engine)**
*   **Status: LIVE**
*   **Logic**: `anomaly_detection.py` implements a weighted formula:
    > **Risk Score = (Spatial * 0.5) + (Env * 0.2) + (Behavior * 0.3)**
*   **Factors**:
    1.  **Spatial**: Ray-Casting Algorithm checks for Polygon Geofence breaches (`Tawang Red Zone`).
    2.  **Temporal**: Higher risk weighting during night hours (18:00 - 05:00).
    3.  **Behavioral**: Velocity drop (<0.1m/s) triggers "Stagnation" warnings.

### **Module 4: "Dead Man's Switch" (Fail-Safe)**
*   **Status: LIVE**
*   **Component**: `dead_man_monitor.py` (Background Task).
*   **Logic**:
    *   Polls active trackers every 60s.
    *   **Trigger**: IF `TimeSinceLastPing > Threshold` AND `Zone == HighRisk` -> **CRITICAL ALERT**.
    *   **Output**: "Signal Lost in Danger Zone" alert sent to Dashboard.

### **Module 5: Sentinel Dashboard & E-FIR**
*   **Status: LIVE**
*   **Visuals**: Real-time "Dot" tracking with breadcrumb history trails.
*   **Alerts**: Instant WebSocket notifications with "Siren" audio.
*   **Exports**: One-click "Generate E-FIR" modal displaying the TX Hash and Permit ID.

---

## 4. Key Security Features (Pinnacle Standards)
1.  **Zero-Trust Identity**: Dashboards verify tourists via Blockchain (`get_permit_info`) without querying a centralized admin DB.
2.  **Tamper-Proof Logging**: Critical Incidents are linked to immutable Blockchain Transactions (TXIDs).
3.  **Fail-Safe Design**: The "Dead Man Switch" ensures safety even if the *device* fails or is destroyed.

---

## 5. Deployment Guide (Quick Reference)

### **Prerequisites**
*   Docker & Docker Compose
*   Node.js 18+ & Python 3.9+
*   Ganache (CLI or GUI)

### **Start Infrastructure**
```bash
docker-compose up -d
# (Starts LocalStack on 4566, Ganache on 8545)
```

### **Initialize Systems (Automated)**
```bash
# 1. Deploy Smart Contract & Issue Mock Permits
python scripts/deploy_contract.py

# 2. Setup DB Schema
python backend/database/setup_dynamodb.py

# 3. Start Backend
uvicorn backend.app.main:app --reload
```

### **Run Demo Simulation**
```bash
# Generates & Replays 5 Scenarios (Safe, Breach, Fall, Lost, SOS)
python scripts/generate_trek_data.py
python scripts/replay_trek.py
```

---

## 6. Advanced Architectural Defenses (Viva Preparation)

### **7.1. "Why Blockchain for Identity?"**
**Answer:** "Prahari uses Blockchain as a **Trust Anchor**. Remote check-posts often have poor connectivity to a central database. A decentralized ledger allows local nodes to verify signatures (hashes) offline or async, and ensures that a corrupt official cannot retroactively delete a permit record."

### **7.2. "How does the AI handle false positives?"**
**Answer:** "We use a **Weighted Risk Score** (0-100) rather than binary triggers. A user stepping 1 meter inside a geofence (Risk 50) is a 'Warning'. A user stopping inside a Red Zone at night (Risk 80+) is an 'Emergency'. This gradation reduces operator fatigue."

### **7.3. "What if the Tracker stops working?"**
**Answer:** "That is exactly why we built the **Dead Man's Switch**. Prahari inverts the monitoring logic: instead of waiting for an SOS signal (which requires a working device), the Cloud monitors for the *absence* of a signal ('Heartbeat Loss') in high-risk zones, triggering an automatic rescue protocol."
