# PRAHARI-AI: Technical Digest & Architectural Reference

**Version:** 2.1.0 "Production Candidate"  
**Status:** Feature Complete & Securitized  
**Context:** MoDoNER Pinnacle Project (Smart Tourist Safety System)

---

## 1. Executive Summary
**PRAHARI-AI** is a comprehensive "Sentinel" system designed for the Ministry of Development of North Eastern Region (MoDoNER). Its primary objective is to ensure the safety of tourists trekking in remote, sensitive border areas (like Tawang, Arunachal Pradesh) using a blend of **Decentralized Identity (SSI)**, **Real-Time Geofencing**, and **AI-driven Anomaly Detection**.

Unlike traditional databases, PRAHARI uses a privacy-first blockchain layer for issuing digital travel permits, ensuring that government checkpoints can verify legality without exposing a tourist's full personal history (Zero-Trust architecture).

---

## 2. System Architecture (Production Grade)
The system follows a modern **Event-Driven, Serverless-First** architecture, optimized for high throughput and fail-safety.

### **2.1. Dual-Path Backbone**
To handle high-frequency telemetry without blocking, the backend implements a "Dual-Path" strategy:
*   **Fast Path (Hot Logic)**: 
    *   **In-Memory Cache (Redis Pattern)**: Stores the latest state of every tracker.
    *   **Kalman Filter**: Smooths GPS jitter and predicts velocity in real-time (<5ms latency).
    *   **WebSocket Broadcast**: Pushes updates to the Dashboard immediately.
*   **Slow Path (Cold Logic)**:
    *   **Background Workers**: Asynchronous tasks handle heavy lifting (DynamoDB persistence, Geofence Ray-Casting, Blockchain Verification).
    *   **Dead Man's Switch**: Usage of periodic tasks to detect silent failures.

### **2.2. Infrastructure Layer**
*   **AWS Cloud Simulator (LocalStack)**: DynamoDB for persistence.
*   **Blockchain Network (Ganache)**: Ethereum Testnet hosting `TouristPermitRegistry.sol`.
*   **API Security**: Endpoint protection via API Key (`x-api-key`) authentication.

---

## 3. Module Breakdown (Implemented Status)

### **Module 1: The Immutable Identity (Blockchain Core)**
*   **Status: LIVE**
*   **Smart Contract**: `TouristPermitRegistry.sol` (Deployed).
    *   **Features**: Time-locked permits, Identity Hashing (SHA-256), Emergency Flagging.
    *   **Privacy**: Only hashes are stored on-chain. PII remains off-chain.
*   **Bridge**: `identity.py` service resolves DIDs to real-time Blockchain Permit status.

### **Module 2: High-Fidelity Telemetry & AI Engine**
*   **Status: LIVE**
*   **Ingestion**: `telemetry.py` processes raw GPS data via the **Fast Path**.
*   **Smoothing**: Implemented **Kalman Filters** (4-state) to reduce GPS jitter.
*   **The Brain**: `SentinelAI` class calculates a real-time risk score (0-100) based on:
    *   **Spatial**: Red Zone entry (+50).
    *   **Temporal**: Night-time operations (+20).
    *   **Behavioral**: Stagnation/Drift (+20).
    *   **SOS Override**: Immediate Critical Status.

### **Module 3: "Dead Man's Switch" (Fail-Safe)**
*   **Status: LIVE**
*   **Component**: `scheduler.py` (Background Task).
*   **Logic**:
    *   Polls active trackers every 60s.
    *   **Trigger**: IF `TimeSinceLastPing > Threshold` AND `Zone == HighRisk` -> **CRITICAL ALERT**.
    *   **Output**: "Signal Lost in Danger Zone" alert broadcasted to Mission Control.

### **Module 4: Sentinel Mission Control (Dashboard)**
*   **Status: LIVE**
*   **Visuals**: 
    *   V2 Dashboard with "Mission Control" Sidebar.
    *   Visual priority for Alerts (Red/Amber) with Audio Feedback.
    *   Standard OSM Light Mode for high visibility.
*   **E-FIR Generator**: 
    *   One-click "Generate E-FIR" modal.
    *   Backend service (`reports.py`) generates a PDF with **Blockchain TXID** and **QR Code** for legal admissibility.

---

## 4. Security & Compliance
1.  **API Security**: All ingestion endpoints are secured with `x-api-key` validation. Secrets are managed via `.env` files (gitignored).
2.  **Zero-Trust Identity**: Verification relies on decentralized ledger proofs, not centralized trust.
3.  **Tamper-Proof Logs**: Critical incidents are anchored to the blockchain (simulated hash integration).

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

# 3. Start Backend (with Background Tasks)
uvicorn backend.app.main:app --reload

# 4. Start Dashboard
cd frontend/dashboard && npm run dev
```

### **Run Production Simulation (Stress Test)**
```bash
# Simulates 4 Concurrent Scenarios:
# 1. Safe Tourist
# 2. Red Zone Breacher
# 3. Accident (Stagnation)
# 4. SOS Panic
python scripts/simulation.py
```

---

## 6. Viva Preparation: Advanced Q&A

### **7.1. "Why Blockchain for Identity?"**
**Answer:** "Prahari uses Blockchain as a **Trust Anchor**. Remote check-posts often have poor connectivity to a central database. A decentralized ledger allows local nodes to verify signatures (hashes) offline or async, and ensures that a corrupt official cannot retroactively delete a permit record."

### **7.2. "How do you handle system latency?"**
**Answer:** "We implemented a **Dual-Path Architecture**. Critical data (Location, Risk Score) travels via a 'Fast Path' (In-Memory Cache -> WebSocket) with <50ms latency for real-time tracking. Heavy processing (DB writes, detailed analytics) is offloaded to background workers ('Slow Path'), ensuring the ingestion API never blocks."

### **7.3. "What if the Tracker stops working?"**
**Answer:** "That is exactly why we built the **Dead Man's Switch**. Prahari inverts the monitoring logic: instead of waiting for an SOS signal (which requires a working device), the Cloud monitors for the *absence* of a signal ('Heartbeat Loss') in high-risk zones, triggering an automatic rescue protocol."
