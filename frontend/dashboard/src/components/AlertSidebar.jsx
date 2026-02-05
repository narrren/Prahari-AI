import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { AlertTriangle, ShieldAlert, FileText, Activity, CheckCircle, Clock, Send, Gavel } from 'lucide-react';
import { downloadEFIR } from '../utils/api';

// Mock Config for Demo (In real app, get from Context/Auth)
const CURRENT_ROLE = 'DISTRICT_SUPERVISOR';
const API_BASE = "http://localhost:8000/api/v1";

const AlertSidebar = ({ alerts, onRefresh, tourists }) => {
    // V5.1 Cyber-Forensics HUD State
    const [modelStatus, setModelStatus] = useState('CHECKING');
    const [modelHash, setModelHash] = useState(null);
    const [blockHeight, setBlockHeight] = useState(742);

    useEffect(() => {
        // Fetch Integrity
        const checkIntegrity = async () => {
            try {
                const res = await axios.get(`${API_BASE}/integrity/model`);
                setModelStatus(res.data.status);
                setModelHash(res.data.current_hash);
            } catch (e) { setModelStatus('OFFLINE'); }
        };
        checkIntegrity();

        // Simulate Block Height ticking
        const ledgerInterval = setInterval(() => {
            setBlockHeight(prev => prev + 1);
        }, 3000);

        return () => clearInterval(ledgerInterval);
    }, []);

    const handleAction = async (action, alertId) => {
        try {
            const endpoint = action === 'ACK' ? 'acknowledge' : 'resolve';
            await axios.patch(`${API_BASE}/alerts/${alertId}/${endpoint}`, {}, {
                headers: {
                    'X-Actor-ID': 'demo-user',
                    'X-Role': CURRENT_ROLE
                }
            });
            console.log(`Alert ${alertId} ${action}ed`);
            if (onRefresh) onRefresh();
        } catch (err) {
            console.error(`Failed to ${action} alert`, err);
        }
    };

    const handleClaim = async (alertId) => {
        try {
            await axios.post(`${API_BASE}/incident/claim/${alertId}`, {}, {
                headers: { 'X-Actor-ID': 'commander-01' }
            });
            if (onRefresh) onRefresh();
        } catch (e) {
            console.error("Claim failed", e);
        }
    }

    const handleDispatch = (alertId) => {
        // Mock Dispatch UX
        const agency = prompt("SELECT AGENCY FOR HANDOFF:\n1. ITBP (Border Police)\n2. NDRF (Disaster)\n3. Local Medical");
        if (agency) {
            alert(`Connect: Blockchain Transaction Initiated.\nTarget: AGENCY_${agency}\nAsset: INCIDENT_${alertId}\nStatus: PENDING_CONFIRMATION`);
        }
    }

    // V5.0 Decentralized Attestation
    const handleAttest = async (alertId) => {
        try {
            await axios.post(`${API_BASE}/alert/attest/${alertId}`, {}, {
                headers: { 'X-Node-ID': 'CHECKPOST_BRAVO' }
            });
            if (onRefresh) onRefresh();
        } catch (e) { console.error(e); }
    }

    // Sort: CRITICAL first, then new
    const sortedAlerts = [...(alerts || [])].sort((a, b) => {
        if (a.actions?.includes('CRITICAL') && !b.severity) return -1; // Fallback sort
        return (b.timestamp || 0) - (a.timestamp || 0); // Newest first
    });

    return (
        <aside className="w-96 bg-gray-950 border-r border-gray-800 flex flex-col z-20 shadow-2xl h-full">
            <div className="p-4 border-b border-gray-800 bg-gray-900/50 backdrop-blur flex items-center justify-between">
                <h2 className="text-white font-bold flex items-center gap-2">
                    <Activity size={18} className="text-red-500 animate-pulse" />
                    LIVE INCIDENTS
                </h2>
                <div className="flex gap-2">
                    <span className="text-[10px] bg-blue-900 text-blue-200 px-2 py-0.5 rounded border border-blue-700">OPS: ON</span>
                    <span className="text-[10px] bg-red-900 text-red-200 px-2 py-0.5 rounded border border-red-700 animate-pulse">LIVE</span>
                </div>
            </div>

            {/* V5.1 CYBER-FORENSICS HUD */}
            <div className="bg-gray-900 mx-3 mt-3 p-3 rounded-lg border-2 border-purple-500 shadow-[0_0_15px_rgba(168,85,247,0.3)]">
                <h3 className="text-xs font-bold text-white uppercase tracking-widest mb-2 flex items-center gap-2">
                    <Gavel size={14} className="text-purple-400" /> Cyber-Forensics HUD
                </h3>

                {/* Node Consensus */}
                <div className="flex justify-between items-center mb-1 text-[10px] font-mono">
                    <span className="text-gray-500">Node Consensus</span>
                    <span className="text-green-400 flex items-center gap-1"><CheckCircle size={8} /> 2/2 Nodes (Attested)</span>
                </div>

                {/* Ledger Health */}
                <div className="flex justify-between items-center mb-1 text-[10px] font-mono">
                    <span className="text-gray-500">Ledger Health</span>
                    <span className="text-blue-300 animate-pulse">Syncing Block #{blockHeight}...</span>
                </div>

                {/* Model Hash */}
                <div className="flex justify-between items-center mb-2 text-[10px] font-mono">
                    <span className="text-gray-500">Model Integrity</span>
                    <span className={modelStatus === 'SECURE' ? "text-green-400 font-bold" : "text-red-500 font-bold animate-pulse"}>
                        {modelStatus === 'SECURE' ? '0x8f2... (VALID)' : 'COMPROMISED'}
                    </span>
                </div>

                {/* Controls */}
                <div className="grid grid-cols-2 gap-2 mt-2 pt-2 border-t border-purple-500/20">
                    <button className="bg-slate-800 text-[10px] text-gray-300 py-1.5 rounded border border-slate-600 hover:bg-slate-700 transition flex items-center justify-center gap-1">
                        <Activity size={10} /> Anomaly Heatmap
                    </button>
                    <button onClick={() => alert("Redirecting to Forensic Timeline...")} className="bg-purple-900/40 text-purple-300 text-[9px] py-1.5 rounded border border-purple-500/50 hover:bg-purple-900/60 transition flex items-center justify-center gap-1">
                        <Clock size={10} /> Audit Mode (Time-Travel)
                    </button>
                </div>
            </div>

            <div className="flex-1 overflow-y-auto p-3 space-y-3 bg-black/20 custom-scrollbar">
                {sortedAlerts.length === 0 && (
                    <div className="flex flex-col items-center justify-center h-40 text-slate-500">
                        <Activity className="w-8 h-8 mb-2 opacity-20" />
                        <p className="text-sm italic">Scanning for anomalies...</p>
                    </div>
                )}

                {sortedAlerts.map((alert) => {
                    const status = alert.status || 'DETECTED'; // Default to DETECTED if missing
                    const isCritical = alert.severity === 'CRITICAL' || alert.is_panic;

                    // V5.0 Metrics Lookup
                    const tourist = tourists?.find(t => t.device_id === alert.device_id);
                    const humanityScore = tourist?.humanity_score ?? 100.0;
                    const isSpoofed = humanityScore < 50;

                    return (
                        <div
                            key={alert.alert_id || alert.id}
                            className={`relative p-3 rounded-lg border-l-4 shadow-lg transition-all border border-y-0 border-r-0 ${status === 'RESOLVED'
                                ? 'opacity-50 border-gray-600 bg-gray-900'
                                : isCritical
                                    ? 'bg-red-950/30 border-red-600 text-red-100'
                                    : 'bg-blue-950/30 border-blue-500 text-blue-100'
                                }`}
                        >
                            {/* SLA Timer Bar (Visual) */}
                            {status === 'DETECTED' && (
                                <div className="absolute top-0 left-0 right-0 h-0.5 bg-gray-800 overflow-hidden rounded-t">
                                    <div className="h-full bg-gradient-to-r from-red-500 to-yellow-500 w-[80%] animate-[width_2m_linear]"></div>
                                </div>
                            )}

                            <div className="flex justify-between items-start mb-2 mt-1">
                                <div className="flex flex-col">
                                    <span className="text-[10px] font-mono opacity-70 flex items-center gap-1">
                                        <Clock size={10} />
                                        {new Date((alert.timestamp || Date.now()) * 1000).toLocaleTimeString()}
                                    </span>
                                    {alert.confidence !== undefined && (
                                        <span className={`text-[9px] font-bold mt-0.5 ${alert.confidence > 80 ? 'text-green-400' :
                                            alert.confidence > 50 ? 'text-yellow-400' :
                                                'text-red-400'
                                            }`}>
                                            AI CONFIDENCE: {Math.round(alert.confidence)}%
                                        </span>
                                    )}
                                </div>
                                <span className={`text-[9px] font-bold px-1.5 py-0.5 rounded uppercase ${status === 'DETECTED' ? 'bg-red-600 text-white animate-pulse' :
                                    status === 'ACKNOWLEDGED' ? 'bg-yellow-600 text-black' :
                                        'bg-green-600 text-white'
                                    }`}>
                                    {status}
                                </span>
                            </div>

                            <div className="font-bold text-sm mb-1 flex justify-between items-center">
                                <span>{alert.device_id}</span>
                                {isCritical && <ShieldAlert size={16} className="text-red-500" />}
                            </div>

                            <div className="text-xs mb-2 p-2 bg-black/40 rounded border border-white/5 font-mono text-gray-300">
                                {alert.message}
                            </div>

                            {/* V5.0 TRUSTLESS GOVERNANCE BLOCK */}
                            <div className="mb-2 p-2 bg-slate-800/50 rounded border border-slate-700">
                                <div className="text-[9px] text-slate-400 font-bold uppercase tracking-wider mb-1">Blockchain & Biometrics</div>
                                <div className="flex justify-between items-center mb-1">
                                    <span className="text-[10px] text-gray-400">Attestation:</span>
                                    {alert.attestation_status === 'ATTESTED' ? (
                                        <span className="text-[10px] text-green-400 font-bold flex items-center gap-1">
                                            <CheckCircle size={10} /> VERIFIED (Node-2)
                                        </span>
                                    ) : (
                                        <button onClick={() => handleAttest(alert.alert_id)} className="text-[9px] bg-slate-700 hover:bg-slate-600 px-1.5 py-0.5 rounded text-gray-300 transition-colors">
                                            Request Checkpost
                                        </button>
                                    )}
                                </div>
                                <div className="flex justify-between items-center">
                                    <span className="text-[10px] text-gray-400">Signal Auth:</span>
                                    <span className={`text-[10px] font-mono font-bold ${isSpoofed ? 'text-red-500 animate-pulse' : 'text-blue-300'}`}>
                                        {humanityScore.toFixed(1)}% {isSpoofed && '(BOT DETECTED)'}
                                    </span>
                                </div>
                                {/* Progress Bar for Humanity */}
                                <div className="w-full bg-gray-700 h-1 mt-1 rounded-full overflow-hidden">
                                    <div className={`h-full transition-all duration-500 ${isSpoofed ? 'bg-red-500' : 'bg-blue-500'}`} style={{ width: `${humanityScore}%` }}></div>
                                </div>
                            </div>

                            {/* SMART AI SUGGESTION */}
                            {alert.suggested_action && (
                                <div className="mb-2 p-2 bg-blue-900/20 border-l-2 border-blue-500 rounded-r">
                                    <span className="text-[8px] font-bold text-blue-400 block tracking-wider mb-0.5">AI RECOMMENDATION</span>
                                    <div className="text-[10px] text-blue-100 font-mono">
                                        {alert.suggested_action}
                                    </div>
                                </div>
                            )}

                            {/* INCIDENT OWNERSHIP (V3.2) */}
                            <div className="mb-3 flex items-center justify-between bg-black/20 p-1.5 rounded border border-white/5">
                                <span className="text-[9px] text-gray-500 font-bold uppercase tracking-wider">Incident Commander</span>
                                {alert.owner_id ? (
                                    <span className="text-[9px] font-mono text-green-400 font-bold flex items-center gap-1">
                                        <Gavel size={10} /> {alert.owner_id}
                                    </span>
                                ) : (
                                    <button
                                        onClick={() => handleClaim(alert.alert_id)}
                                        className="text-[9px] bg-blue-700 hover:bg-blue-600 text-white px-2 py-0.5 rounded font-bold transition-colors"
                                    >
                                        CLAIM CMD
                                    </button>
                                )}
                            </div>

                            {/* CONTROL PLANE ACTIONS */}
                            <div className="grid grid-cols-2 gap-2 mt-2 pt-2 border-t border-white/10">
                                {status === 'DETECTED' ? (
                                    <>
                                        <button
                                            onClick={() => handleAction('ACK', alert.alert_id)}
                                            className="col-span-1 bg-yellow-600 hover:bg-yellow-500 text-black text-[10px] font-bold py-1.5 rounded flex items-center justify-center gap-1"
                                        >
                                            <CheckCircle size={10} /> ACKNOWLEDGE
                                        </button>
                                        <button
                                            onClick={() => handleDispatch(alert.alert_id)}
                                            className="col-span-1 flex items-center justify-center gap-1 bg-purple-700 hover:bg-purple-600 text-white rounded text-[10px] font-bold transition-all"
                                        >
                                            <Send size={10} /> DISPATCH
                                        </button>
                                    </>
                                ) : status === 'ACKNOWLEDGED' ? (
                                    <>
                                        <button
                                            onClick={() => handleAction('RESOLVE', alert.alert_id)}
                                            className="bg-green-700 hover:bg-green-600 text-white text-[10px] font-bold py-1.5 rounded"
                                        >
                                            RESOLVE
                                        </button>
                                        <button
                                            onClick={() => downloadEFIR(alert.device_id)}
                                            className="bg-red-700 hover:bg-red-600 text-white text-[10px] font-bold py-1.5 rounded flex items-center justify-center gap-1"
                                        >
                                            <FileText size={10} /> GEN E-FIR
                                        </button>
                                    </>
                                ) : (
                                    <div className="col-span-2 text-center text-[10px] text-gray-500 font-mono">
                                        CASE CLOSED (Archived)
                                    </div>
                                )}
                            </div>
                        </div>
                    );
                })}
            </div>
        </aside>
    );
};

export default AlertSidebar;
