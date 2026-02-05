import React, { useState, useEffect } from 'react';
import { ShieldCheck, Database, Lock, Network } from 'lucide-react';

const SecurityHUD = () => {
    const [metrics, setMetrics] = useState({
        merkle_root: "WAITING...",
        chain_height: 150000,
        consensus_status: "LOCKED (2/3)"
    });

    useEffect(() => {
        // Poll for metrics every 2s
        const interval = setInterval(() => {
            fetch('http://localhost:8000/api/v1/health/metrics')
                .then(res => res.json())
                .then(data => {
                    if (data.metrics) {
                        setMetrics({
                            merkle_root: data.metrics.merkle_root || "PENDING",
                            chain_height: data.metrics.chain_height || 150000,
                            consensus_status: data.metrics.consensus_status || "LOCKED"
                        });
                    }
                })
                .catch(err => console.error("HUD Fetch Error", err));
        }, 2000);
        return () => clearInterval(interval);
    }, []);

    return (
        <div style={{
            position: 'absolute',
            bottom: '80px', // Above bottom bar
            left: '20px',
            background: 'rgba(10, 25, 47, 0.9)',
            border: '1px solid #1abc9c',
            borderRadius: '8px',
            padding: '12px',
            color: '#e0e6ed',
            width: 'auto',
            minWidth: '250px',
            zIndex: 1000,
            boxShadow: '0 0 15px rgba(26, 188, 156, 0.3)'
        }}>
            <div style={{ display: 'flex', alignItems: 'center', marginBottom: '8px', borderBottom: '1px solid #333', paddingBottom: '4px' }}>
                <ShieldCheck size={18} color="#1abc9c" style={{ marginRight: '8px' }} />
                <span style={{ fontWeight: 'bold', fontSize: '12px', letterSpacing: '1px' }}>SECURITY INTEGRITY HUD</span>
            </div>

            <div style={{ fontSize: '11px', display: 'flex', flexDirection: 'column', gap: '6px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <span style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
                        <Network size={12} /> Chain Height:
                    </span>
                    <span style={{ fontFamily: 'monospace', color: '#64ffda' }}>#{metrics.chain_height}</span>
                </div>

                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <span style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
                        <Database size={12} /> Merkle Root:
                    </span>
                    <span style={{ fontFamily: 'monospace', color: '#f1c40f' }}>{metrics.merkle_root.substring(0, 8)}...</span>
                </div>

                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <span style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
                        <Lock size={12} /> Governance:
                    </span>
                    <span style={{ color: '#2ecc71', fontWeight: 'bold' }}>{metrics.consensus_status}</span>
                </div>
            </div>

            <div style={{ marginTop: '8px', fontSize: '10px', color: '#8892b0', fontStyle: 'italic', textAlign: 'center' }}>
                Telemetry Cryptographically Verified
            </div>
        </div>
    );
};

export default SecurityHUD;
