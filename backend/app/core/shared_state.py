
# Shared In-Memory State for Prahari-AI Backend
# This acts as a localized Redis replacement for the demo.

# Latest known positions of all devices. 
# Format: { "device_id": { ...TelemetryData... } }
LATEST_POSITIONS = {}

# Kalman Filter states
KALMAN_STATES = {}
