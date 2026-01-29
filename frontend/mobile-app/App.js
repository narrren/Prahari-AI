import React, { useState, useEffect } from 'react';
import { StyleSheet, Text, View, TouchableOpacity, Alert, Vibration } from 'react-native';
import * as Location from 'expo-location';
import { io } from 'socket.io-client';

// AWS IoT / Backend Endpoint
const BACKEND_URL = "http://YOUR_LOCAL_IP:8000/api/v1";

export default function App() {
    const [location, setLocation] = useState(null);
    const [isPanic, setIsPanic] = useState(false);
    const [status, setStatus] = useState('SECURE');

    useEffect(() => {
        (async () => {
            let { status } = await Location.requestForegroundPermissionsAsync();
            if (status !== 'granted') {
                Alert.alert('Permission Denied', 'Allow location access for sentinel tracking.');
                return;
            }

            // Background tracking (Simplified for demo)
            Location.watchPositionAsync(
                {
                    accuracy: Location.Accuracy.High,
                    timeInterval: 5000,
                    distanceInterval: 10,
                },
                (loc) => {
                    setLocation(loc);
                    sendTelemetry(loc);
                }
            );
        })();
    }, []);

    const sendTelemetry = async (loc) => {
        if (!loc) return;

        const payload = {
            device_id: "DEVICE_MOBILE_001",
            timestamp: loc.timestamp / 1000,
            location: {
                lat: loc.coords.latitude,
                lng: loc.coords.longitude
            },
            is_panic: isPanic,
            battery_level: 100 // Mock
        };

        try {
            await fetch(`${BACKEND_URL}/telemetry`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
        } catch (e) {
            console.log("Offline Mode: Queuing data...", e);
            // Implement Offline Queue here (SQLite/AsyncStorage)
        }
    };

    const handlePanic = () => {
        setIsPanic(true);
        setStatus('SOS ACTIVE');
        Vibration.vibrate([500, 500, 500]);
        Alert.alert("SOS TRIGGERED", "Authorities have been notified.");
        // Force immediate send
        sendTelemetry(location);
    };

    return (
        <View style={styles.container}>
            <View style={styles.header}>
                <Text style={styles.title}>PRAHARI SENTINEL</Text>
                <Text style={styles.subtitle}>MoDoNER Safety Link: CONNECTED</Text>
            </View>

            <View style={styles.geoBox}>
                <Text style={styles.label}>CURRENT LOCATION</Text>
                {location ? (
                    <Text style={styles.coords}>
                        {location.coords.latitude.toFixed(4)}, {location.coords.longitude.toFixed(4)}
                    </Text>
                ) : (
                    <Text style={styles.coords}>Acquiring GPS...</Text>
                )}
            </View>

            <TouchableOpacity
                style={[styles.sosButton, isPanic && styles.sosActive]}
                onLongPress={handlePanic}
                delayLongPress={1000}
            >
                <Text style={styles.sosText}>HOLD FOR SOS</Text>
            </TouchableOpacity>

            <Text style={styles.instruction}>Hold for 3 seconds to trigger emergency response</Text>
        </View>
    );
}

const styles = StyleSheet.create({
    container: {
        flex: 1,
        backgroundColor: '#111827', // Prahari Dark
        alignItems: 'center',
        justifyContent: 'center',
        padding: 20,
    },
    header: {
        position: 'absolute',
        top: 60,
        alignItems: 'center',
    },
    title: {
        color: '#60A5FA', // Blue 400
        fontSize: 24,
        fontWeight: 'bold',
        letterSpacing: 2,
    },
    subtitle: {
        color: '#10B981', // Green 500
        fontSize: 10,
        marginTop: 5,
        fontFamily: 'monospace',
    },
    geoBox: {
        marginBottom: 50,
        alignItems: 'center',
    },
    label: {
        color: '#6B7280',
        fontSize: 12,
        marginBottom: 5,
    },
    coords: {
        color: 'white',
        fontSize: 32,
        fontFamily: 'monospace',
        fontWeight: 'bold',
    },
    sosButton: {
        width: 250,
        height: 250,
        borderRadius: 125,
        backgroundColor: '#EF4444', // Red 500
        alignItems: 'center',
        justifyContent: 'center',
        borderWidth: 4,
        borderColor: '#7F1D1D',
        shadowColor: '#EF4444',
        shadowOffset: { width: 0, height: 0 },
        shadowOpacity: 0.8,
        shadowRadius: 20,
        elevation: 10,
    },
    sosActive: {
        backgroundColor: '#7F1D1D',
        borderColor: '#EF4444',
    },
    sosText: {
        color: 'white',
        fontSize: 24,
        fontWeight: 'bold',
    },
    instruction: {
        color: '#9CA3AF',
        marginTop: 30,
        fontSize: 14,
    }
});
