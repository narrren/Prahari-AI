import React, { useEffect } from 'react';
import { MapContainer, TileLayer, CircleMarker, Popup, Circle } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';

// Tawang Coords
const NETWORK_CENTER = [27.5861, 91.8594];

const MapComponent = ({ tourists, geofences }) => {
    return (
        <div className="h-full w-full rounded-xl overflow-hidden shadow-2xl border border-gray-700">
            <MapContainer center={NETWORK_CENTER} zoom={15} scrollWheelZoom={true} className="h-full w-full">
                <TileLayer
                    attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
                    url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                />

                {/* Render GeoFences */}
                {geofences.map((zone) => (
                    <Circle
                        key={zone.zone_id}
                        center={[zone.center.lat, zone.center.lng]}
                        pathOptions={{ color: 'red', fillColor: '#ef4444', fillOpacity: 0.2 }}
                        radius={zone.radius_meters}
                    >
                        <Popup>
                            <div className="text-black">
                                <strong className="text-red-600">RESTRICTED ZONE</strong><br />
                                {zone.name}<br />
                                Risk: {zone.risk_level}
                            </div>
                        </Popup>
                    </Circle>
                ))}

                {/* Render Tourists */}
                {tourists.map((t) => (
                    <CircleMarker
                        key={t.device_id}
                        center={[t.location.lat, t.location.lng]}
                        pathOptions={{
                            color: t.is_panic ? 'red' : '#3b82f6',
                            fillColor: t.is_panic ? 'red' : '#60a5fa',
                            fillOpacity: 0.8
                        }}
                        radius={8}
                    >
                        <Popup>
                            <div className="text-black">
                                <strong>User: {t.device_id}</strong><br />
                                Status: {t.is_panic ? "PANIC" : "Active"}<br />
                                Speed: {t.speed} m/s
                            </div>
                        </Popup>
                    </CircleMarker>
                ))}
            </MapContainer>
        </div>
    );
};

export default MapComponent;
