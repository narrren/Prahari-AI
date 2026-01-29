# Prahari-AI
## Smart Tourist Safety Monitoring & Incident Response System

---

### Overview

**Prahari-AI** is a comprehensive security infrastructure designed to address the unique safety challenges faced by tourists in the North Eastern Region (NER) of India. By integrating Artificial Intelligence, Geo-Fencing, and Blockchain-based Digital Identity, Prahari-AI provides a proactive safety net that ensures rapid incident response, secure identity verification, and real-time monitoring without compromising user privacy.

This project moves beyond simple tracking to offer a **Self-Sovereign Identity (SSI)** solution and an **AI-driven safety ecosystem**, acting as a digital guardian for travelers in difficult terrains and sensitive border zones.

---

### The Problem

The North Eastern Region is beautiful but poses specific risks for tourists:
- **Difficult Terrain:** High mountains and dense forests increase the risk of getting lost or accidents.
- **Restricted Zones:** Proximity to international borders and protected areas requires special permits (RAP/PAP). Accidental trespass can lead to severe legal and security consequences.
- **Identity Loss:** Loss of physical documents (Aadhaar/Passport) in remote areas makes identity verification nearly impossible.
- **Slow Response:** In "zero-population" zones, lack of immediate location data delays rescue operations during emergencies.

---

### The Solution

Prahari-AI implements a three-pronged technical solution:

1. **Blockchain-based Digital ID (DID):** 
   - Replaces physical papers with a tamper-proof Decentralized Identity. 
   - Allows authorities to verify permits and identity offline or in low-connectivity areas using Zero-Knowledge Proofs (ZKPs).
   
2. **Smart Geo-Fencing:** 
   - Establishes "Virtual Fences" around landslide zones, restricted border areas, and high-risk terrains.
   - Triggers automated alerts to both the tourist and the nearest police outpost if a boundary is crossed.

3. **AI Incident Response:** 
   - Analyzes real-time movement patterns.
   - Detects anomalies such as prolonged inactivity in a moving zone or sudden signal loss, flagging them as potential accidents to dispatch rescue teams proactively.

---

### Key Features

#### Digital Tourist ID Platform
- Secure blockchain issuance of digital IDs at entry points (Airports, Hotels).
- IDs encapsulate KYC details, trip itinerary, and emergency contacts.
- Valid strictly for the duration of the visit.

#### Tourist Mobile Application
- **Safety Score:** Auto-assigned score based on current location sensitivity and travel patterns.
- **Panic Button:** One-touch SOS sending live location to the nearest police unit.
- **Multilingual Support:** Interface available in 10+ Indian languages and English.
- **Offline Mode:** Critical features work in low-network reliability areas.

#### AI-Based Anomaly Detection
- Monitors for sudden location drop-offs or deviation from planned routes.
- Flags "silent" or "distress" behavior for immediate investigation.

#### Authority Dashboard (Police & Tourism Dept)
- **Heat Maps:** Real-time visualization of tourist clusters and high-risk zones.
- **E-FIR Generation:** Automated filing for missing person cases based on digital logs.
- **Alert History:** Comprehensive logs of all breach attempts and SOS signals.

#### IoT Integration (Optional)
- Support for smart bands/tags for tracking in deep forests or caves where mobile signals fail.

---

### Privacy & Security

- **End-to-End Encryption:** All location data and personal communication are encrypted.
- **Self-Sovereign Identity:** Users own their data; verification does not require a central honeypot database.
- **Compliance:** Adheres to data protection laws and privacy standards.

---

### Proposed Tech Stack

- **Backend:** Node.js / Python (FastAPI)
- **Blockchain:** Hyperledger / Ethereum (for DID & Permits)
- **AI/ML:** TensorFlow / PyTorch (Movement Anomaly Detection)
- **Cloud/Infra:** AWS IoT Core (GPS Streaming), Amazon Managed Blockchain
- **Frontend:** React Native (Mobile), React.js (Web Dashboard)
- **Mapping:** OpenStreetMap / Mapbox

---

### License

This project is developed as a **Pinnacle Project (6th Semester)** to solve real-world tourism safety challenges.
