import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { AlertTriangle, ShieldAlert, FileText, Activity, CheckCircle, Clock } from 'lucide-react';
import { downloadEFIR } from '../utils/api';

// Mock Config for Demo (In real app, get from Context/Auth)
const CURRENT_ROLE = 'DISTRICT_SUPERVISOR';
const API_BASE = "http://localhost:8000/api/v1";

const AlertSidebar = ({ alerts }) => {
    // We maintain a local version of alerts to allow optimistic UI updates
    // But mostly rely on the parent 'alerts' prop which comes from polling/socket

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
            // Optimistic update could go here, but next poll will catch it
        } catch (err) {
            console.error(`Failed to ${action} alert`, err);
        }
    };

    return (
        <aside className="w-96 bg-prahari-card border-r border-gray-700 flex flex-col z-20 shadow-xl h-full">
            <div className="p-4 border-b border-gray-700 bg-slate-800 flex items-center justify-between">
                <h2 className="text-white font-bold flex items-center gap-2">
                    <Activity size={18} className="text-red-500 animate-pulse" />
                    LIVE INCIDENTS
                </h2>
                <div className="flex gap-2">
                    <span className="text-[10px] bg-blue-900 text-blue-200 px-2 py-0.5 rounded border border-blue-700">OPS: ON</span>
                    <span className="text-[10px] bg-red-900 text-red-200 px-2 py-0.5 rounded border border-red-700 animate-pulse">LIVE</span>
                </div>
            </div>

            <div className="flex-1 overflow-y-auto p-3 space-y-3 bg-gray-950">
                {alerts.length === 0 && (
                    <div className="flex flex-col items-center justify-center h-40 text-slate-500">
                        <Activity className="w-8 h-8 mb-2 opacity-20" />
                        <p className="text-sm italic">Scanning for anomalies...</p>
                    </div>
                )}

                {alerts.map((alert) => {
                    const status = alert.status || 'DETECTED'; // Default to DETECTED if missing
                    const isCritical = alert.severity === 'CRITICAL' || alert.is_panic;

                    return (
                        <div
                            key={alert.alert_id || alert.id}
                            className={`relative p-3 rounded-lg border-l-4 shadow-lg transition-all ${status === 'RESOLVED'
                                ? 'opacity-50 border-gray-500 bg-gray-800'
                                : isCritical
                                    ? 'bg-red-950/40 border-red-500 text-red-100'
                                    : 'bg-blue-950/40 border-blue-500 text-blue-100'
                                }`}
                        >
                            {/* SLA Timer Bar (Visual) */}
                            {status === 'DETECTED' && (
                                <div className="absolute top-0 left-0 right-0 h-1bg-gray-800">
                                    <div className="h-1 bg-gradient-to-r from-red-500 to-yellow-500 w-[80%] animate-[width_2m_linear]"></div>
                                </div>
                            )}

                            <div className="flex justify-between items-start mb-2">
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
                                            CONFIDENCE: {Math.round(alert.confidence)}%
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

                            <div className="font-bold text-sm mb-1 flex justify-between">
                                <span>{alert.device_id}</span>
                                {isCritical && <ShieldAlert size={16} className="text-red-500" />}
                            </div>

                            <div className="text-xs mb-2 p-2 bg-black/30 rounded border border-white/5 font-mono">
                                {alert.message}
                            </div>

                            {/* SMART AI SUGGESTION */}
                            {alert.suggested_action && (
                                <div className="mb-3 p-2 bg-blue-900/20 border-l-2 border-blue-500 rounded-r">
                                    <span className="text-[8px] font-bold text-blue-400 block tracking-wider mb-0.5">AI RECOMMENDATION</span>
                                    <div className="text-[10px] text-blue-100 font-mono">
                                        {alert.suggested_action}
                                    </div>
                                </div>
                            )}

                            {/* CONTROL PLANE ACTIONS */}
                            <div className="grid grid-cols-2 gap-2 mt-2 pt-2 border-t border-white/10">
                                {status === 'DETECTED' ? (
                                    <button
                                        onClick={() => handleAction('ACK', alert.alert_id)}
                                        className="col-span-2 bg-yellow-600 hover:bg-yellow-500 text-black text-xs font-bold py-1.5 rounded flex items-center justify-center gap-2"
                                    >
                                        <CheckCircle size={12} /> ACKNOWLEDGE
                                    </button>
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
