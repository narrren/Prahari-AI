# PRAHARI-AI
## Sovereign-Grade Tourist Safety & Border Security System

**Status**: 🟢 **DEPLOYMENT READY** (v5.1 - Hardened Production Build)  
**Classification**: Defense-Grade Infrastructure | Zero Trust Architecture

---

## 🎯 Mission Statement

**PRAHARI-AI** is a next-generation security infrastructure designed for the North Eastern Region (NER) of India, combining **AI-driven threat detection**, **blockchain-based identity management**, and **real-time incident response** to protect tourists in sensitive border zones and difficult terrains.

This is not just a tracking system—it's a **Self-Sovereign Digital Guardian** that ensures rapid emergency response while maintaining strict privacy and data sovereignty compliance.

---

## 🚀 Quick Start (Production Deployment)

### Prerequisites
- **Python 3.10+**
- **Node.js 18+**
- **Docker** (optional, for full-stack deployment)

### Option 1: Manual Setup (Recommended for Development)

#### 1. Backend Setup
```powershell
cd backend
pip install -r requirements.txt
python -m uvicorn app.main:fastapi_app --host 0.0.0.0 --port 8000 --reload
```

#### 2. Frontend Setup
```powershell
cd frontend/dashboard
npm install
npm run dev -- --host
```

#### 3. Start Traffic Simulator
```powershell
# In project root
python traffic_generator.py
```

#### 4. Access Dashboard
- **Dashboard**: http://localhost:5173
- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/api/v1/health/metrics

### Option 2: Docker Deployment (Full Stack)
```powershell
docker-compose up -d
```

This will start:
- FastAPI Backend (Port 8000)
- React Dashboard (Port 5173)
- Ganache Blockchain (Port 8545)
- LocalStack (DynamoDB/S3 simulation, Port 4566)
- Redis Cache (Port 6379)
- Traffic Simulator

---

## 🛡️ Security Architecture (v5.1 Hardening)

### Zero Trust Enforcement
- ✅ **Hardware Fingerprinting**: Every device has a unique cryptographic identity
- ✅ **Cryptographic Attestation**: All telemetry packets are HMAC-SHA256 signed
- ✅ **Replay Protection**: Monotonic nonce validation prevents packet replay attacks
- ✅ **System Lockdown**: Automatic fail-closed mode on AI model integrity breach

### Role-Based Access Control (RBAC)
- **COMMANDER**: Full system access, can resolve incidents
- **OFFICER**: Can acknowledge alerts, dispatch resources
- **DISTRICT_SUPERVISOR**: Read-only access to regional data

### Blockchain Integration
- **Smart Contract**: `TouristPermitRegistry.sol` (Multi-sig for Red Zone permits)
- **Data Anchoring**: Merkle root of telemetry batches anchored every 60s
- **Immutable Audit Trail**: All governance actions logged on-chain

---

## 📊 Key Features

### 1. **Cryptographic Identity Layer**
- Decentralized Identity (DID) for each tourist
- Hardware-bound device authentication
- Privacy-preserving PII hashing (SHA-256 on blockchain)

### 2. **Sentinel AI Engine**
- **Anomaly Detection**: Detects bot spoofing (Zero Entropy movement)
- **Geofence Breach Detection**: Real-time alerts for Red Zone intrusions
- **Dead Man's Switch**: Auto-alerts if signal lost in high-risk areas
- **Humanity Score**: Biometric behavior analysis (0-100%)

### 3. **Cyber-Forensics HUD**
- **Node Consensus**: Multi-node attestation status
- **Ledger Health**: Real-time blockchain sync status
- **Model Integrity**: AI model hash verification
- **Audit Mode**: Time-travel replay of historical telemetry

### 4. **Incident Management**
- **Alert Lifecycle**: DETECTED → ACKNOWLEDGED → RESOLVED
- **E-FIR Generation**: Automated First Information Report filing
- **Multi-Agency Dispatch**: Blockchain-based handoff to ITBP/NDRF

### 5. **Data Privacy (DPDP Compliance)**
- **Data Shredder**: Automatic PII purge after permit expiry
- **Blockchain Hashes Only**: No raw PII stored after 30 days
- **Purpose Limitation**: Telemetry used only for safety, not surveillance

---

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    PRAHARI-AI SYSTEM                        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐ │
│  │   Tourist    │───▶│  Telemetry   │───▶│   Sentinel   │ │
│  │   Devices    │    │   Ingestion  │    │   AI Engine  │ │
│  │ (4 Profiles) │    │ (Zero Trust) │    │ (Anomaly Det)│ │
│  └──────────────┘    └──────────────┘    └──────────────┘ │
│         │                    │                    │        │
│         │                    ▼                    ▼        │
│         │            ┌──────────────┐    ┌──────────────┐ │
│         │            │   In-Memory  │    │   Alert      │ │
│         │            │   Cache      │    │   Manager    │ │
│         │            │ (500 pts/dev)│    │ (Lifecycle)  │ │
│         │            └──────────────┘    └──────────────┘ │
│         │                    │                    │        │
│         ▼                    ▼                    ▼        │
│  ┌──────────────────────────────────────────────────────┐ │
│  │          React Dashboard (Cyber-Forensics HUD)       │ │
│  │  - Live Map (4 Trackers)                             │ │
│  │  - Tactical VCR (History Replay)                     │ │
│  │  - Alert Sidebar (RBAC-enforced actions)             │ │
│  └──────────────────────────────────────────────────────┘ │
│                                                             │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐ │
│  │  Blockchain  │    │   DynamoDB   │    │    Redis     │ │
│  │  (Ganache)   │    │ (LocalStack) │    │   (Cache)    │ │
│  │ Permit Reg.  │    │  Telemetry   │    │  Fast Path   │ │
│  └──────────────┘    └──────────────┘    └──────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

---

## 🧪 Testing & Verification

### Run System Verification
```powershell
python v5_check.py
```

This runs:
- ✅ Health endpoint check
- ✅ Cyber-Forensics HUD validation
- ✅ Model integrity verification
- ✅ Security hardening tests (spoofing, RBAC)
- ✅ Bot detection validation

### Traffic Simulation Profiles
The `traffic_generator.py` simulates 4 distinct user behaviors:

1. **ALPINIST_SAFE**: Normal trekker, safe zone
2. **ALPINIST_RED**: Erratic movement, entering Red Zone (triggers alert)
3. **MECH_DRONE_01**: Perfect linear movement (triggers bot detection)
4. **SIGNAL_LOST**: Sends one packet then stops (triggers Dead Man's Switch)

---

## 📁 Project Structure

```
Prahari-AI/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI app (telemetry router registered)
│   │   ├── routers/
│   │   │   └── telemetry.py     # All telemetry/alert endpoints
│   │   ├── services/
│   │   │   ├── identities.py    # Device registry (4 authorized devices)
│   │   │   ├── integrity.py     # AI model hash verification
│   │   │   ├── shredder.py      # DPDP compliance (PII purge)
│   │   │   └── websocket.py     # Real-time broadcast
│   │   ├── contracts/
│   │   │   └── TouristPermitRegistry.sol  # Blockchain smart contract
│   │   └── core/
│   │       └── shared_state.py  # In-memory cache (TELEMETRY_HISTORY)
│   └── requirements.txt
├── frontend/
│   └── dashboard/
│       ├── src/
│       │   ├── App.jsx          # Main dashboard
│       │   ├── components/
│       │   │   ├── Map.jsx      # Leaflet map with 4 trackers
│       │   │   ├── TacticalOverlay.jsx  # VCR replay
│       │   │   ├── AlertSidebar.jsx     # Cyber-Forensics HUD
│       │   │   └── SecurityHUD.jsx      # Integrity indicators
│       │   └── utils/
│       └── package.json
├── traffic_generator.py         # Simulates 4 device profiles
├── v5_check.py                  # System verification script
├── docker-compose.yml           # Full-stack orchestration
├── DEPLOYMENT_READINESS_CERTIFICATE.md  # Audit report
└── README.md                    # This file
```

---

## 🔧 Troubleshooting

### Issue: No trackers visible on map
**Solution**: Ensure all services are running:
```powershell
# Check backend
curl http://localhost:8000/api/v1/map/positions

# Should return 4 devices (after traffic generator runs for 10s)
```

### Issue: Telemetry ingestion fails (401 errors)
**Cause**: Missing or invalid cryptographic signatures  
**Solution**: Verify device secrets match in `identities.py` and `traffic_generator.py`

### Issue: VCR history is empty
**Cause**: In-memory buffer not populated  
**Solution**: Wait 30s after starting traffic generator, then click tracker

---

## 📜 Deployment Readiness

✅ **Security Audit**: Passed Red Team testing (spoofing, replay, RBAC)  
✅ **Integrity Verification**: AI model hash anchored on blockchain  
✅ **RBAC Enforcement**: All administrative endpoints require role headers  
✅ **Data Privacy**: DPDP-compliant data shredder scheduled  
✅ **Fail-Safe**: System lockdown on integrity breach (503 response)

See [`DEPLOYMENT_READINESS_CERTIFICATE.md`](./DEPLOYMENT_READINESS_CERTIFICATE.md) for full audit report.

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| **Backend** | FastAPI, Python 3.10+, Uvicorn |
| **Frontend** | React 19, Vite, Tailwind CSS, Leaflet |
| **AI Engine** | Custom SentinelAI (Anomaly Detection) |
| **Blockchain** | Ganache (Ethereum), Solidity, Web3.py |
| **Database** | DynamoDB (LocalStack), Redis (Cache) |
| **Security** | HMAC-SHA256, mTLS simulation, Zero Trust |
| **Protocols** | WebSocket (real-time), REST API, Protobuf |

---

## 📝 License

This project is developed as a **Pinnacle Project (6th Semester, 2025-26)** to address real-world tourism safety challenges in India's North Eastern Region.

**Developed by**: Naren Dey  
**Institution**: Techno Main Salt Lake  
**Purpose**: Academic Research & Social Impact

---

## 🙏 Acknowledgments

- **Ministry of Tourism, Govt. of India** - For highlighting NER safety challenges
- **ITBP (Indo-Tibetan Border Police)** - For operational insights
- **Blockchain Research Lab, TMSL** - For technical guidance

---

## 📞 Support

For deployment assistance or security inquiries:
- **Email**: naren.dey@example.com
- **GitHub Issues**: [Report a bug](https://github.com/narrren/Prahari-AI/issues)

---

**⚠️ IMPORTANT**: This system is designed for **authorized government use only**. Unauthorized deployment or misuse may violate privacy laws and border security regulations.
