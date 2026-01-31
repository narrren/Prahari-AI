import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { Server, Database, Wifi, ShieldCheck, Activity } from 'lucide-react';

const API_BASE = "http://localhost:8000/api/v1";

const SystemHealth = () => {
    const [stats, setStats] = useState(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchHealth = async () => {
            try {
                const res = await axios.get(`${API_BASE}/health/metrics`);
                setStats(res.data);
                setLoading(false);
            } catch (err) {
                console.error("Health check failed", err);
                setLoading(false);
            }
        };

        // Initial Fetch
        fetchHealth();

        // Poll every 5 seconds
        const interval = setInterval(fetchHealth, 5000);
        return () => clearInterval(interval);
    }, []);

    if (loading || !stats) return null; // Don't show until ready

    const metrics = stats.metrics || {};
    const services = stats.services || {};

    return (
        <div className="flex items-center gap-4 bg-slate-900/80 border border-gray-700 rounded-lg px-4 py-2 text-xs font-mono text-gray-300 backdrop-blur-md shadow-lg">
            {/* INGESTION RATE */}
            <div className="flex items-center gap-2 border-r border-gray-700 pr-4">
                <Activity size={12} className="text-blue-400" />
                <div className="flex flex-col">
                    <span className="text-[9px] text-gray-500 uppercase tracking-wider">Telemetry Rate</span>
                    <span className="font-bold text-white">{metrics.ingestion_rate || 0} pks/s</span>
                </div>
            </div>

            {/* ACTIVE ALERTS */}
            <div className="flex items-center gap-2 border-r border-gray-700 pr-4">
                <ShieldCheck size={12} className={metrics.alerts_active > 0 ? "text-red-500 animate-pulse" : "text-green-500"} />
                <div className="flex flex-col">
                    <span className="text-[9px] text-gray-500 uppercase tracking-wider">Active Alerts</span>
                    <span className={`font-bold ${metrics.alerts_active > 0 ? "text-red-400" : "text-green-400"}`}>
                        {metrics.alerts_active || 0}
                    </span>
                </div>
            </div>

            {/* UPTIME */}
            <div className="flex items-center gap-2 border-r border-gray-700 pr-4">
                <Server size={12} className="text-purple-400" />
                <div className="flex flex-col">
                    <span className="text-[9px] text-gray-500 uppercase tracking-wider">Uptime</span>
                    <span className="font-bold text-white">{Math.floor((stats.uptime_seconds || 0) / 60)} min</span>
                </div>
            </div>

            {/* CONNECTION STATUS ICONS */}
            <div className="flex gap-2">
                <div title="Database" className={`p-1 rounded ${services.database === 'CONNECTED' ? 'bg-green-900/50 text-green-400' : 'bg-red-900/50 text-red-400'}`}>
                    <Database size={10} />
                </div>
                <div title="Blockchain" className={`p-1 rounded ${services.blockchain === 'CONNECTED' ? 'bg-green-900/50 text-green-400' : 'bg-red-900/50 text-red-400'}`}>
                    <ShieldCheck size={10} />
                </div>
                <div title="WebSocket" className={`p-1 rounded ${services.websocket === 'ACTIVE' ? 'bg-green-900/50 text-green-400' : 'bg-red-900/50 text-red-400'}`}>
                    <Wifi size={10} />
                </div>
            </div>

            <div className="ml-2 pl-2 border-l border-gray-700">
                <span className="text-[10px] text-green-500 font-bold tracking-widest animate-pulse">● SYSTEM OPTIMAL</span>
            </div>
        </div>
    );
};

export default SystemHealth;
