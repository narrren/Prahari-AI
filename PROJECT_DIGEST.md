# PRAHARI-AI: Technical Digest & Architectural Reference

**Version:** 3.2.0 "Defense-Grade Release"  
**Status**: 🟢 **MISSION READY**  
**Last Updated**: 2026-01-31  
**Codebase**: `c:\Users\naren\Desktop\Prahari-AI`

---

## 1. Project Identity
**One-Liner**: An AI-augmented, Hardware-Hardened Tourist Safety & Border Surveillance Network for Arunachal Pradesh.
**Mission**: To eliminate "Dark Zones" in remote border areas using a dual-path telemetry architecture (LoRa/Sat), decentralized governance, and resilient AI oversight.

---

## 2. V3.2 Real-World Capabilities (The "Production Gap" Closers)
This release addresses the harsh realities of government deployment: Accountability, Conflict, and Failure.

### A. Alert Fatigue & SLA Enforcement
*   **The Upgrade**: Visual timers are not enough. We added an **Escalation Automation Engine**.
*   **Logic**:
    *   Alert not ACKed in 5 mins → Auto-escalate to Supervisor.
    *   Supervisor override without justification → Flagged for Audit.
    *   **Rule**: *"SLAs are machine-enforced, not advisory."*

### B. Decision Provenance Engine
*   **The Upgrade**: Every human action is a structured record.
*   **Structure**: `DecisionRecord { alert_id, ai_recommendation, operator_action, divergence_flag, justification }`.
*   **Impact**: *"All human overrides are captured as first-class decision artifacts, enabling post-incident accountability without operator fear."*

### C. Smart Confidence & Self-Degradation
*   **The Upgrade**: The system knows when it is sick.
*   **Autonomous Degradation Policies**:
    *   *WebSocket Unstable* → Auto-switch to Polling Mode.
    *   *Blockchain High Latency* → Auto-extend Cache Grace Window.
    *   *Telemetry Drop* → Freeze AI Confidence Scores (prevent false positives).
*   **Dashboard State**: Shows `NORMAL` / `DEGRADED` / `EMERGENCY` modes explicitly.

### D. Geofence Conflict Resolution
*   **The Upgrade**: Handling multi-agency jurisdiction overlaps.
*   **Priority Logic**: `Military (Defcon)` > `Disaster Mgmt` > `Civil Admin` > `Tourism Dept`.
*   **Outcome**: If the Army declares a Red Zone, it overrides a Tourism Green Zone deterministically.

---

## 3. Phase 4: Advanced Hardening (Roadmap)
Future-proofing Prahari for scale (10k+ users) and rigorous compliance.

### A. Tactical Visual Intelligence
*   **VCR Mode**: A time-slider capability to replay a target's movement history (last 6h) to pinpoint exactly where they deviated from the trail.
*   **Resource Layers**: Auto-calculation of "Time-to-Rescue" by plotting the nearest Helipads and Police Outposts relative to the alert location.

### B. Inter-Agency Dispatch Protocol
*   **The Feature**: "Chain of Responsibility".
*   **Logic**: Supervisors can "Forward" a verified E-FIR to external agencies (ITBP, Army, Forest Dept).
*   **Audit**: The blockchain logs the handoff, ensuring the specific agency acknowledges receipt of the rescue mission.

### C. Telemetry Hardening
*   **Protobuf Serialization**: Migration from JSON to Google Protocol Buffers for the mobile uplink, projecting a **60% reduction in bandwidth usage** (vital for 2G/Sat-Link).
*   **Leaky Bucket Rate Limiting**: Anti-DDoS protection on the ingestion endpoint to prevent flooded or malicious telemetry packets.

### D. Forensic "Black Box" & Privacy
*   **DPDP Compliance**: Automated "PII Scrubbing" cron jobs.
*   **Policy**: Once a permit expires + 30 days retention, the raw GPS logs are purged, leaving only anonymized heatmaps for tourism analytics.

### E. Split-Horizon Resilience
*   **Scenario**: Cloud (AWS) unreachable during a storm.
*   **Fallback**: Dashboard auto-detects "Cloud Failure" and switches to **Local P2P Mode**, pulling directly from the local LoRa WAN Gateway to maintain situational awareness.

---

## 4. Operational Control Plane (Governance)

### Incident Ownership Model (ICS Compliant)
*   **Problem**: "Everyone thought someone else was handling it."
*   **Solution**: **Exclusive Incident Ownership**.
    *   When an alert hits `CRITICAL`, a specific `owner_id` is assigned.
    *   Handoffs are logged in a `handoff_log[]`.
    *   Mirrors standard **Incident Command System (ICS)** protocols.

### Emergency Kill Switch
*   **Feature**: **System Freeze Mode**.
*   **Trigger**: Suspected cyber-compromise or false-positive cascade.
*   **Action**: Freezes all Outbound Notifications and FIR Generation. Preserves Inbound Logging.

---

## 5. System Architecture (Resilient Design)

### Trust Scope Declaration
We explicitly define the boundaries of Decentralized Trust to satisfy production reviewers:
*   **Blockchain IS used for**:
    *   Permit Issuance/Verification (Anti-Retroactive Deletion).
    *   Audit Anchoring (Evidence Integrity).
*   **Blockchain is NOT used for**:
    *   Real-time Decision Making.
    *   Life-critical Latency Paths.

> **"Blockchain acts as a trust anchor, never a real-time dependency."**

### Data Lifecycle & Privacy
Policy-driven management of sensitive border data:
1.  **Telemetry (Raw)**: Retained 30 Days (Hot Storage).
2.  **Incident Reports (Legal)**: Retained 7 Years (Cold Archive/Blockchain).
3.  **Analytics (Aggregated)**: Indefinite (Anonymized).
4.  **Anonymization**: Automatic PII stripping post-retention window.
5.  **Serialization**: Protobuf (Planned) for bandwidth optimization.

---

## 6. Deployment & Simulation

### Infrastructure
```bash
docker-compose up -d  # Fast-Path (Redis), Slow-Path (DB), Ledger (Ganache)
```

### Key Workflows
1.  **Deployment**: `python scripts/deploy_contract.py`
2.  **Simulation**: `python scripts/simulation.py` (Triggers scenarios)
3.  **Governance**: Operator Acknowledges -> Supervisor Resolves -> System Logs Timeline.

---

## 6. Viva Preparation: Tough Questions

### Q1: "Who is responsible if the AI misses a distress signal?"
**A:** "The **Decision Provenance Engine** ensures we know exactly why. If the AI confidence was low due to 'Telemetry Drop', the **Degradation Policy** would have flagged the system as 'DEGRADED', shifting liability from the operator to the infrastructure status. If the operator ignored a High Confidence alert, the **Audit Log** proves negligence."

### Q2: "What happens if the Army and Tourism department disagree on a zone?"
**A:** "We implemented a **Deterministic Conflict Resolver**. The backend has a rigid hierarchy: Military Risk Layers always supersede Civil Tourism Layers. There is no ambiguity in the code during multiple-agency inputs."

### Q3: "Is the Blockchain a single point of failure?"
**A:** "No. We use it strictly as an **Async Trust Anchor**. Our **Resilience Circuit Breakers** allow the system to run on 'Cached Trust' for up to 24 hours if the mainnet is unreachable. Real-time safety never waits for a block confirmation."


