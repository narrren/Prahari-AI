import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Shield, Zap, Lock, Skull } from 'lucide-react';

export default function CyberHUD() {
    const [hud, setHud] = useState(null);
    const [modelStatus, setModelStatus] = useState({ status: 'SECURE', checked_at: 0 });

    useEffect(() => {
        const fetchHud = async () => {
            try {
                const res = await axios.get("http://localhost:8000/api/v1/cyber/hud");
                setHud(res.data);

                // Fetch Model Integrity
                const intRes = await axios.get("http://localhost:8000/api/v1/integrity/model");
                setModelStatus(intRes.data);
            } catch (e) { }
        };
        fetchHud();
        const poll = setInterval(fetchHud, 2000);
        return () => clearInterval(poll);
    }, []);

    if (!hud) return null;

    return (
        <div className="absolute bottom-4 right-4 z-50 bg-black/80 backdrop-blur border border-blue-500/50 p-4 rounded-lg w-80 shadow-2xl">
            <div className="flex justify-between items-center mb-2 border-b border-gray-700 pb-2">
                <h3 className="text-sm font-bold text-blue-400 tracking-widest uppercase">Cyber-Defense HUD</h3>
                {hud.threat_level === 'CRITICAL' ?
                    <Skull className="text-red-500 animate-pulse w-5 h-5" /> :
                    <Shield className="text-green-500 w-5 h-5" />
                }
            </div>

            <div className="space-y-3">

                {/* Protocol Badge (PQC) */}
                <div className="flex justify-between items-center bg-purple-900/20 p-1.5 rounded border border-purple-500/30">
                    <span className="text-[10px] text-purple-300 font-mono">ENCRYPTION</span>
                    <span className="text-[10px] font-bold text-cyan-300 flex items-center gap-1">
                        <Lock className="w-3 h-3" /> CRYSTALS-Dilithium (PQC)
                    </span>
                </div>

                <div className="flex justify-between items-center">
                    <span className="text-xs text-gray-400">Threat Level</span>
                    <span className={`text-xs font-bold px-2 py-0.5 rounded ${hud.threat_level === 'CRITICAL' ? 'bg-red-900 text-red-200 animate-pulse' : 'bg-green-900 text-green-200'
                        }`}>
                        {hud.threat_level}
                    </span>
                </div>

                {/* AI Model Integrity */}
                <div className="flex justify-between items-center">
                    <span className="text-xs text-gray-400">AI Model Provenance</span>
                    {modelStatus.status === 'SECURE' ? (
                        <span className="text-[10px] font-bold text-green-400 flex items-center gap-1">
                            <Shield className="w-3 h-3" /> Anchored (Blockchain)
                        </span>
                    ) : (
                        <span className="text-[10px] font-bold text-red-500 flex items-center gap-1 animate-pulse">
                            <Skull className="w-3 h-3" /> POISON DETECTED
                        </span>
                    )}
                </div>

                <div className="space-y-1">
                    <span className="text-[10px] text-gray-500 uppercase font-bold">Active Countermeasures</span>
                    {hud.active_countermeasures.length === 0 ? (
                        <div className="text-xs text-gray-600 italic">None active</div>
                    ) : (
                        hud.active_countermeasures.map((cm, i) => (
                            <div key={i} className="flex items-center gap-2 text-xs text-yellow-500">
                                <Zap className="w-3 h-3" /> {cm}
                            </div>
                        ))
                    )}
                </div>

                {hud.blacklisted_ips.length > 0 && (
                    <div className="pt-2 border-t border-gray-700">
                        <div className="text-[10px] text-red-500 uppercase font-bold flex items-center gap-2">
                            <Lock className="w-3 h-3" /> Blacklisted IPs
                        </div>
                        <div className="flex flex-wrap gap-1 mt-1">
                            {hud.blacklisted_ips.map((ip, i) => (
                                <span key={i} className="bg-red-900/50 text-red-400 text-[10px] px-1 rounded">{ip}</span>
                            ))}
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
}
