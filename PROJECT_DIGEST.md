# PRAHARI-AI: Technical Digest & Architectural Reference

**Version:** 1.0.0  
**Status:** Alpha / Prototype (LocalStack + Ganache)  
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
    *   **DynamoDB**: Stores hot state (current location) and cold storage (historical paths).
    *   **IoT Core (Simulated)**: Ingests high-frequency GPS telemetry via MQTT/HTTP.
*   **Blockchain Network (Ganache)**:
    *   Runs a local Ethereum testnet (Chain ID: 1337).
    *   Hosts the `TouristPermitRegistry` smart contract.

### **2.2. Backend Services (Python/FastAPI)**
*   **API Gateway**: REST API managing frontend communication.
*   **Anomaly Engine**: Processing pipeline that analyzes incoming telemetry against safety rules.
*   **Database Service**: Abstraction layer connecting to LocalStack DynamoDB.

### **2.3. Frontend Applications**
*   **Command Centre (React + Vite)**: A high-fidelity dashboard for Police/Tourism authorities.
*   **Field Unit (React Native Skeleton)**: Mobile app logic for tourists (GPS tracking & SOS).

---

## 3. Module Breakdown

### **Module 1: Decentralized Identity (SSI) & Permitting**
*   **Objective**: Replace physical paper permits with Verifiable Credentials (VCs).
*   **Components**:
    *   `TouristPermitRegistry.sol`: Solidity smart contract for issuing/revoking permits.
    *   **Issuer Portal**: React UI (`PermitIssuer.jsx`) allowing authorities to mint permits to a tourist's DID (Wallet Address).
    *   **Verification**: "Verify without Reveal" logic using cryptographic hashes.

### **Module 2: Real-Time Geo-Fencing & Tracking**
*   **Data Flow**: Mobile App -> AWS IoT Core -> Lambda -> DynamoDB -> Dashboard.
*   **Geofences**: Defined polygons (e.g., "zone_id: ZONE_001") representing restricted or high-risk areas.
*   **Alert Generation**:
    *   **Entry/Exit Events**: Immediate alerts when a tourist crosses a geofence boundary.

### **Module 3: AI Anomaly Detection Engine**
*   **Logic**: A heuristic-based Python service (`anomaly_detection.py`) that monitors tourist behavior.
*   **Detection Rules**:
    1.  **Inactivity**: Stationary for > 30 minutes in a remote zone.
    2.  **Route Deviation**: Straying > 500m from the assigned trekking path.
    3.  **Velocity Anomaly**: Sudden deceleration (simulating a fall or accident).
    4.  **SOS**: Panic button triggers high-priority "CRITICAL" alerts.

### **Module 4: Sentinel Command Dashboard**
*   **UI/UX**: Dark-mode, "Glassmorphism" design tailored for a high-tech control room.
*   **Features**:
    *   **Live Map**: Leaflet.js-based visualization of all active tourists.
    *   **Incident Feed**: Real-time sidebar processing alert priority (Red = Critical, Orange = Warning).
    *   **Dual-View**: Toggles between "Live Monitor" and "Permit Issuer" modes.

### **Module 5: Mobile App (Field Unit)**
*   **Tech**: React Native / Expo.
*   **Capabilities**:
    *   **Background GPS**: Polls location every 5 seconds (simulated).
    *   **Panic Button**: "Hold-to-trigger" interface with haptic feedback.
    *   **Offline Logic**: Queues telemetry when network connectivity is lost.

---

## 4. Key Security Features (CISSP Standards)
1.  **Zero-Trust Model**: Authorities verify *permits*, not *people*. Personal data is not stored in the central DB, only hashes.
2.  **Immutable Logs**: Every permit issuance or revocation is a transaction on the Blockchain, creating a tamper-proof audit trail.
3.  **Encrypted Telemetry**: Location data in transit is encrypted (TLS 1.2+ standard).
4.  **Role-Based Access**: The Smart Contract creates an `onlyAuthority` modifier, preventing unauthorized nodes from minting permits.

---

## 5. Deployment Guide (Quick Reference)

### **Prerequisites**
*   Docker & Docker Compose
*   Node.js 18+ & Python 3.9+

### **Start Infrastructure**
```bash
docker-compose up -d
# (Starts LocalStack on ports 4566, Ganache on 8545)
```

### **Initialize Systems**
```bash
# 1. Setup DB Schema
python backend/database/setup_dynamodb.py

# 2. Run Simulation (Optional)
python scripts/generate_trek_data.py
python scripts/replay_trek.py
```

### **Run Applications**
```bash
# Backend
uvicorn backend.app.main:app --reload

# Frontend
cd frontend/dashboard
npm run dev
```

---

## 6. Future Roadmap
*   **Integration**: Connect the `blockchain.js` service to a live testnet (Polygon Amoy).
*   **AI Models**: Replace heuristics with an LSTM (Long Short-Term Memory) neural network for predictive path analysis.
*   **Mobile**: Build full APK/IPA with offline map caching (Mapbox).
