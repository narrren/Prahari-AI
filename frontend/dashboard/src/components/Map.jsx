import React, { useEffect } from 'react';
import { MapContainer, TileLayer, CircleMarker, Popup, Circle, Polyline } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';

// Tawang Coords
const NETWORK_CENTER = [27.5861, 91.8594];

const MapComponent = ({ tourists, geofences }) => {
    return (
        <div className="h-full w-full rounded-xl overflow-hidden shadow-2xl border border-gray-700 relative">
            {/* Visual Sentinel Overlay */}
            <div className="absolute top-4 right-4 z-[9999] pointer-events-none">
                <div className="text-[10px] text-gray-500 font-mono bg-black/50 px-2 py-1 rounded border border-gray-800">
                    SATELLITE LINK: ACTIVE <span className="animate-pulse text-green-500">●</span>
                </div>
            </div>

            <MapContainer center={NETWORK_CENTER} zoom={15} scrollWheelZoom={true} className="h-full w-full bg-black">
                {/* Dark Matter Skin */}
                <TileLayer
                    attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> &copy; <a href="https://carto.com/attributions">CARTO</a>'
                    url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
                />

                {/* Render GeoFences - Red Polygons */}
                {geofences.map((zone) => (
                    <Circle
                        key={zone.zone_id}
                        center={[zone.center.lat, zone.center.lng]}
                        pathOptions={{
                            color: '#ef4444',
                            fillColor: '#7f1d1d',
                            fillOpacity: 0.2,
                            dashArray: '10, 10',
                            weight: 2
                        }}
                        radius={zone.radius_meters}
                    >
                        <Popup>
                            <div className="text-black font-sans">
                                <strong className="text-red-700 uppercase tracking-widest text-xs">Restricted Zone</strong>
                                <div className="text-sm font-bold">{zone.name}</div>
                                <div className="text-xs text-red-500 font-mono">RISK LEVEL: {zone.risk_level}</div>
                            </div>
                        </Popup>
                    </Circle>
                ))}

                {/* Render Tourists & Breadcrumbs */}
                {tourists.map((t) => (
                    <React.Fragment key={t.device_id}>
                        {/* Mock Breadcrumb Trail (Faded Line) */}
                        {/* In real app, fetch history. Here we simulate a trailing tail based on velocity vector or just static mock */}
                        <Polyline
                            positions={[
                                [t.location.lat, t.location.lng],
                                [t.location.lat - 0.0005, t.location.lng - 0.0005] // Mock tail
                            ]}
                            pathOptions={{ color: t.is_panic ? 'red' : '#3b82f6', weight: 1, opacity: 0.4, dashArray: '5,5' }}
                        />

                        <CircleMarker
                            center={[t.location.lat, t.location.lng]}
                            pathOptions={{
                                color: t.is_panic ? '#ff0000' : '#3b82f6',
                                fillColor: t.is_panic ? '#ff0000' : '#60a5fa',
                                fillOpacity: 0.9,
                                weight: 2
                            }}
                            radius={6}
                        >
                            <Popup>
                                <div className="text-slate-800 min-w-[150px]">
                                    <div className="border-b border-gray-300 pb-1 mb-1 font-bold text-xs uppercase text-gray-500">
                                        ID: {t.device_id}
                                    </div>
                                    <div className="flex justify-between items-center mb-1">
                                        <span className="text-xs font-bold">Status:</span>
                                        <span className={`text-xs font-bold px-1 rounded ${t.is_panic ? 'bg-red-100 text-red-600' : 'bg-green-100 text-green-600'}`}>
                                            {t.is_panic ? "CRITICAL" : "NORMAL"}
                                        </span>
                                    </div>
                                    <div className="text-xs font-mono">
                                        Speed: {parseFloat(t.speed).toFixed(1)} m/s
                                    </div>
                                </div>
                            </Popup>
                        </CircleMarker>
                    </React.Fragment>
                ))}
            </MapContainer>
        </div>
    );
};


export default MapComponent;
