import React, { useState } from 'react';
import axios from 'axios';
import { MapContainer, TileLayer, CircleMarker, Popup, Circle, Polyline } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';

// Tawang Coords
const NETWORK_CENTER = [27.5861, 91.8594];
const API_BASE = "http://localhost:8000/api/v1";

const MapComponent = ({ tourists, geofences }) => {
    const [historyPath, setHistoryPath] = useState([]);
    const [selectedId, setSelectedId] = useState(null);
    const [activeLayer, setActiveLayer] = useState('osm'); // 'osm' | 'satellite' | 'terrain'

    // TILE SOURCES
    const TILES = {
        osm: {
            url: "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
            attr: '&copy; OpenStreetMap contributors'
        },
        satellite: {
            url: "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
            attr: '&copy; Esri &mdash; Source: Esri, i-cubed, USDA, USGS, AEX, GeoEye, Getmapping, Aerogrid, IGN, IGP, UPR-EGP, and the GIS User Community'
        },
        terrain: {
            url: "https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png",
            attr: 'Map data: &copy; OpenStreetMap contributors, SRTM | Map style: &copy; OpenTopoMap (CC-BY-SA)'
        }
    };

    // Auto-Switch Logic: If High Risk detected, switch to Satellite for situational awareness
    React.useEffect(() => {
        const hasCritical = tourists.some(t => {
            const score = t.risk?.score || t.risk_score || 0;
            return score > 50 || t.is_panic;
        });

        if (hasCritical && activeLayer === 'osm') {
            // Only auto-switch if currently on basic map
            setActiveLayer('satellite');
            console.log("Auto-Switching to Satellite Mode due to detected Risk");
        }
    }, [tourists]);

    const handleMarkerClick = async (deviceId) => {
        if (selectedId === deviceId) {
            setSelectedId(null);
            setHistoryPath([]);
            return;
        }

        setSelectedId(deviceId);
        setHistoryPath([]);

        try {
            const res = await axios.get(`${API_BASE}/telemetry/history/${deviceId}?hours=4`);
            const path = res.data
                .sort((a, b) => a.timestamp - b.timestamp)
                .map(pt => [pt.location.lat, pt.location.lng]);

            setHistoryPath(path);
        } catch (err) {
            console.error("Failed to fetch breadcrumbs", err);
        }
    };

    return (
        <div className="h-full w-full rounded-xl overflow-hidden shadow-2xl border border-gray-700 relative">
            {/* Visual Sentinel Overlay */}
            <div className="absolute top-4 right-4 z-[9999] pointer-events-none flex flex-col gap-2 items-end">
                <div className="text-[10px] text-gray-500 font-mono bg-black/50 px-2 py-1 rounded border border-gray-800 backdrop-blur-sm">
                    SATELLITE LINK: ACTIVE <span className="animate-pulse text-green-500">●</span>
                </div>
            </div>

            {/* Map Layer Controls (Custom UI) */}
            <div className="absolute top-4 left-14 z-[1000] flex bg-white/10 backdrop-blur-md rounded-lg overflow-hidden border border-white/20 shadow-lg">
                <button
                    onClick={() => setActiveLayer('osm')}
                    className={`px-3 py-1 text-xs font-bold transition-colors ${activeLayer === 'osm' ? 'bg-blue-600 text-white' : 'text-white hover:bg-white/10'}`}
                >
                    MAP
                </button>
                <button
                    onClick={() => setActiveLayer('satellite')}
                    className={`px-3 py-1 text-xs font-bold transition-colors ${activeLayer === 'satellite' ? 'bg-blue-600 text-white' : 'text-white hover:bg-white/10'}`}
                >
                    SAT
                </button>
                <button
                    onClick={() => setActiveLayer('terrain')}
                    className={`px-3 py-1 text-xs font-bold transition-colors ${activeLayer === 'terrain' ? 'bg-blue-600 text-white' : 'text-white hover:bg-white/10'}`}
                >
                    TER
                </button>
            </div>

            <MapContainer center={NETWORK_CENTER} zoom={15} scrollWheelZoom={true} className="h-full w-full">
                {/* Dynamic Base Layer */}
                <TileLayer
                    key={activeLayer} // Force re-render on change
                    attribution={TILES[activeLayer].attr}
                    url={TILES[activeLayer].url}
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

                {/* Active Breadcrumb Trail */}
                {historyPath.length > 0 && (
                    <Polyline
                        positions={historyPath}
                        pathOptions={{ color: '#0ea5e9', weight: 3, opacity: 0.6, dashArray: '5, 10' }}
                    />
                )}

                {/* Render Tourists */}
                {tourists.map((t) => (
                    <CircleMarker
                        key={t.device_id}
                        center={[t.location?.lat || 0, t.location?.lng || 0]}
                        pathOptions={{
                            color: t.is_panic ? '#ef4444' : (selectedId === t.device_id ? '#ffffff' : '#3b82f6'),
                            fillColor: t.is_panic ? '#ef4444' : '#3b82f6',
                            fillOpacity: selectedId === t.device_id ? 1 : 0.8,
                            weight: selectedId === t.device_id ? 3 : 2,
                            opacity: 1
                        }}
                        radius={selectedId === t.device_id ? 8 : 6}
                        eventHandlers={{
                            click: () => handleMarkerClick(t.device_id)
                        }}
                    >
                        <Popup closeButton={false} className="bg-transparent border-none shadow-none">
                            <div className="bg-gray-950 text-white p-3 min-w-[200px] border border-gray-700 rounded-lg shadow-2xl backdrop-blur-md">
                                <div className="flex justify-between items-center border-b border-gray-700 pb-2 mb-2">
                                    <span className="font-mono text-xs text-blue-400 font-bold tracking-wider">{t.device_id}</span>
                                    <span className={`text-[10px] font-bold px-1.5 py-0.5 rounded ${t.is_panic ? 'bg-red-900/50 text-red-200 border border-red-500 animate-pulse' : 'bg-green-900/50 text-green-200 border border-green-500'}`}>
                                        {t.is_panic ? "SOS ACTIVE" : "SAFE"}
                                    </span>
                                </div>

                                <div className="space-y-1.5 text-xs font-mono text-gray-400">
                                    <div className="flex justify-between">
                                        <span>SPEED:</span>
                                        <span className="text-white">{parseFloat(t.speed).toFixed(1)} m/s</span>
                                    </div>
                                    <div className="flex justify-between">
                                        <span>BATTERY:</span>
                                        <span className={t.battery_level < 20 ? "text-red-400" : "text-green-400"}>{Math.round(t.battery_level || 100)}%</span>
                                    </div>
                                    {t.risk && (
                                        <div className="flex justify-between pt-1">
                                            <span>RISK SCORE:</span>
                                            <span className={(t.risk.score || 0) > 50 ? "text-red-400 font-bold" : "text-blue-300"}>{(t.risk.score || 0).toFixed(0)}/100</span>
                                        </div>
                                    )}
                                </div>

                                <button
                                    onClick={(e) => {
                                        e.stopPropagation();
                                        handleMarkerClick(t.device_id);
                                    }}
                                    className={`mt-3 w-full text-[10px] font-bold py-1.5 rounded border transition-all ${selectedId === t.device_id ? 'bg-blue-600 border-blue-500 text-white shadow-[0_0_10px_rgba(37,99,235,0.5)]' : 'bg-gray-800 border-gray-600 hover:bg-gray-700 text-gray-300'}`}
                                >
                                    {selectedId === t.device_id ? "HIDE TRAJECTORY" : "SHOW TRAJECTORY"}
                                </button>
                            </div>
                        </Popup>
                    </CircleMarker>
                ))}
            </MapContainer>
        </div>
    );
};

export default MapComponent;
