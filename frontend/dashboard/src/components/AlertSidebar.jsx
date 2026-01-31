import React, { useEffect, useRef } from 'react';
import { AlertTriangle, ShieldAlert, FileText, Activity } from 'lucide-react';
import { downloadEFIR } from '../utils/api';

const AlertSidebar = ({ alerts }) => {
    // We receive the FULL alert list from App.jsx parent state.
    // This ensures consistency between Map and Sidebar.

    // Audio Effect using ref to avoid re-creation
    const audioRef = useRef(new Audio('https://od.lk/s/OTFfMjk5ODk5NDdf/siren_alert.mp3')); // Hosted siren or use local if available

    useEffect(() => {
        // Check if the latest alert is critical and new (simple check: implies top of list is new)
        if (alerts.length > 0) {
            const topAlert = alerts[0];
            // Simple logic: if it's very recent (< 5 seconds ago), play sound.
            // Or rely on the socket callback in parent to handle sound?
            // User requested "Part 2" has logic here.
            // But App.jsx ALREADY has the audio logic in the socket listener.
            // So we'll skip duplicating the audio here to avoid double-playing.
        }
    }, [alerts]);

    return (
        <aside className="w-96 bg-prahari-card border-r border-gray-700 flex flex-col z-20 shadow-xl h-full">
            <div className="p-4 border-b border-gray-700 bg-slate-800 flex items-center justify-between">
                <h2 className="text-white font-bold flex items-center gap-2">
                    <Activity size={18} className="text-red-500 animate-pulse" />
                    LIVE INCIDENTS
                </h2>
                <span className="text-xs bg-red-900 text-red-200 px-2 py-1 rounded animate-pulse">LIVE</span>
            </div>

            <div className="flex-1 overflow-y-auto p-3 space-y-3 bg-gray-900">
                {alerts.length === 0 && (
                    <div className="flex flex-col items-center justify-center h-40 text-slate-500">
                        <Activity className="w-8 h-8 mb-2 opacity-20" />
                        <p className="text-sm italic">Scanning for anomalies...</p>
                    </div>
                )}

                {alerts.map((alert) => (
                    <div
                        key={alert.alert_id || alert.id}
                        className={`p-3 rounded-lg border-l-4 shadow-lg transition-all transform hover:scale-[1.02] cursor-pointer ${alert.severity === 'CRITICAL' || alert.is_panic
                                ? 'bg-red-950/40 border-red-500 text-red-100'
                                : alert.type === 'GEOFENCE_BREACH'
                                    ? 'bg-orange-950/40 border-orange-500 text-orange-100'
                                    : 'bg-blue-950/40 border-blue-500 text-blue-100'
                            }`}
                    >
                        <div className="flex justify-between items-start mb-1">
                            <span className="text-xs font-mono opacity-70">
                                {new Date((alert.timestamp || Date.now()) * 1000).toLocaleTimeString()}
                            </span>
                            {alert.severity === 'CRITICAL' || alert.is_panic ?
                                <ShieldAlert size={16} className="text-red-500" /> :
                                <AlertTriangle size={16} className="text-amber-500" />}
                        </div>

                        <div className="font-bold text-sm mb-1">
                            <span className="text-xs opacity-50 block uppercase tracking-wider">Subject ID</span>
                            {alert.device_id}
                        </div>
                        <div className="text-xs mb-2 p-1 bg-black/20 rounded">
                            {alert.message}
                        </div>

                        <div className="flex items-center justify-between mt-3 pt-2 border-t border-white/10">
                            <div className="text-xs font-bold text-gray-400">STATUS: {alert.severity || "WARNING"}</div>
                            <button
                                onClick={(e) => {
                                    e.stopPropagation();
                                    downloadEFIR(alert.device_id);
                                }}
                                className="flex items-center gap-1 bg-white text-black text-[10px] font-bold px-3 py-1.5 rounded hover:bg-blue-100 transition-colors shadow-sm"
                            >
                                <FileText size={10} />
                                GEN E-FIR
                            </button>
                        </div>
                    </div>
                ))}
            </div>
        </aside>
    );
};

export default AlertSidebar;
