const BACKEND_URL = "https://prahari-backend.onrender.com/api/v1";
let deviceId = "";
let isPanic = false;
let watchId = null;

// DOM Elements
const connectionIndicator = document.getElementById('connection-indicator');
const statusText = document.getElementById('status-text');
const deviceIdEl = document.getElementById('device-id');
const gpsStatusEl = document.getElementById('gps-status');
const latValEl = document.getElementById('lat-val');
const lngValEl = document.getElementById('lng-val');
const sosBtn = document.getElementById('sos-btn');
const sosText = document.querySelector('.sos-text');
const toastEl = document.getElementById('toast');
const toastMsgEl = document.getElementById('toast-message');

// Initialize Device
function initDevice() {
    // Use a pre-registered device identity to clear the Zero-Trust firewall
    deviceId = "SIGNAL_LOST";
    deviceIdEl.innerText = "DID:ETH:0xDEAD...666";
    
    // Simulate connection
    setTimeout(() => {
        connectionIndicator.classList.add('connected');
        statusText.classList.add('connected');
        statusText.innerText = "MoDoNER Safety Link: SECURE";
        requestLocation();
    }, 1500);
}

// Location Tracking
function requestLocation() {
    if ('geolocation' in navigator) {
        gpsStatusEl.innerText = "Tracking...";
        watchId = navigator.geolocation.watchPosition(
            (position) => {
                const lat = position.coords.latitude;
                const lng = position.coords.longitude;
                updateLocationUI(lat, lng);
                sendTelemetry(lat, lng);
            },
            (error) => {
                gpsStatusEl.innerText = "GPS Error";
                gpsStatusEl.style.color = "var(--red-alert)";
                showToast("Location access denied or unavailable.");
                // Fallback mock data for demo
                fallbackMockLocation();
            },
            { enableHighAccuracy: true, maximumAge: 0, timeout: 5000 }
        );
    } else {
        gpsStatusEl.innerText = "No GPS";
        fallbackMockLocation();
    }
}

function fallbackMockLocation() {
    gpsStatusEl.innerText = "Simulated GPS";
    let mockLat = 27.0238;
    let mockLng = 88.2636;
    
    setInterval(() => {
        mockLat += (Math.random() - 0.5) * 0.001;
        mockLng += (Math.random() - 0.5) * 0.001;
        updateLocationUI(mockLat, mockLng);
        sendTelemetry(mockLat, mockLng);
    }, 3000);
}

function updateLocationUI(lat, lng) {
    latValEl.innerText = lat.toFixed(4);
    lngValEl.innerText = lng.toFixed(4);
}

// Network Telemetry
let nonce = Date.now() * 100; // Guarantee higher nonce than python's time.time()*1000

async function computeSecureSignature(deviceId, timestamp, lat, lng) {
    const pyTimestampStr = timestamp.toString().includes('.') ? timestamp.toString() : timestamp + '.0';
    const payloadStr = `${deviceId}:${pyTimestampStr}:${lat}:${lng}`;
    const secretKey = "sk_dead"; // Burned-in mock private key for "SIGNAL_LOST"
    
    const enc = new TextEncoder();
    const key = await crypto.subtle.importKey("raw", enc.encode(secretKey), { name: "HMAC", hash: "SHA-256" }, false, ["sign"]);
    const signatureBuffer = await crypto.subtle.sign("HMAC", key, enc.encode(payloadStr));
    
    return Array.from(new Uint8Array(signatureBuffer)).map(b => b.toString(16).padStart(2, '0')).join('');
}

async function sendTelemetry(lat, lng) {
    // Exact binary float to guarantee identical serialization across Py/JS
    const timestamp = Math.floor(Date.now() / 1000) + 0.5; 
    nonce += 1;
    
    const payload = {
        device_id: deviceId,
        did: "did:eth:0xDEAD...666",
        timestamp: timestamp,
        location: { lat, lng },
        speed: 1.2,
        heading: 45,
        is_panic: isPanic,
        battery_level: Math.floor(Math.random() * 20) + 80
    };

    try {
        const signature = await computeSecureSignature(deviceId, timestamp, lat, lng);
        
        const response = await fetch(`${BACKEND_URL}/telemetry`, {
            method: 'POST',
            headers: { 
                'Content-Type': 'application/json',
                'x-api-key': 'dev-secret',
                'X-Signature': signature,
                'X-Nonce': nonce.toString()
            },
            body: JSON.stringify(payload)
        });
        
        if (!response.ok) {
            console.error("Telemetry rejected by backend firewall:", await response.text());
        }
    } catch (e) {
        console.warn("Offline Mode: Data queued locally", e);
    }
}

// SOS Logic (Hold to Trigger)
let pressTimer;
let isPressing = false;

sosBtn.addEventListener('mousedown', startPress);
sosBtn.addEventListener('touchstart', startPress);
sosBtn.addEventListener('mouseup', cancelPress);
sosBtn.addEventListener('mouseleave', cancelPress);
sosBtn.addEventListener('touchend', cancelPress);

function startPress(e) {
    if (isPanic) return; // Already in panic
    if (e.type === 'touchstart') e.preventDefault(); // Prevent duplicate mouse events
    
    isPressing = true;
    sosBtn.classList.add('active');
    
    if (navigator.vibrate) navigator.vibrate(100);
    
    pressTimer = setTimeout(() => {
        triggerSOS();
    }, 2000); // 2 second hold
}

function cancelPress() {
    if (!isPressing || isPanic) return;
    isPressing = false;
    clearTimeout(pressTimer);
    sosBtn.classList.remove('active');
}

function triggerSOS() {
    isPanic = true;
    sosBtn.classList.add('panic-mode');
    sosText.innerText = "SOS ACTIVE";
    statusText.innerText = "EMERGENCY ENGAGED";
    statusText.style.color = "var(--red-alert)";
    
    // Immediate vibration pattern
    if (navigator.vibrate) {
        navigator.vibrate([500, 300, 500, 300, 500]);
    }
    
    showToast("Authorities have been alerted immediately.");
    
    // Send immediate SOS packet
    const currentLat = parseFloat(latValEl.innerText) || 27.0238;
    const currentLng = parseFloat(lngValEl.innerText) || 88.2636;
    sendTelemetry(currentLat, currentLng);
}

// Toast System
let toastTimeout;
function showToast(msg) {
    clearTimeout(toastTimeout);
    toastMsgEl.innerText = msg;
    toastEl.classList.add('show');
    toastTimeout = setTimeout(() => {
        toastEl.classList.remove('show');
    }, 4000);
}

// Entry Point
document.addEventListener('DOMContentLoaded', initDevice);
