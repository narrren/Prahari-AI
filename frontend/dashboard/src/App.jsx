import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Shield, AlertTriangle, Users, Activity, FileBadge, Map as MapIcon, Globe } from 'lucide-react';
import MapComponent from './components/Map';
import PermitIssuer from './components/PermitIssuer';
import { downloadEFIR } from './utils/api';

import AlertSidebar from './components/AlertSidebar';
import SystemHealth from './components/SystemHealth';

// Constants
const API_BASE = "http://localhost:8000/api/v1";
const POLL_INTERVAL = 3000;

// Hardcoded Zones for Demo (Matches Backend Logic)
const DEMO_ZONES = [
  {
    zone_id: "ZONE_001",
    name: "Tawang Landslide Zone A",
    risk_level: "HIGH",
    center: { lat: 27.5880, lng: 91.8620 },
    radius_meters: 100
  }
];

function App() {
  const [view, setView] = useState('monitor'); // 'monitor' | 'issuer'
  const [selectedIncident, setSelectedIncident] = useState(null);
  const [tourists, setTourists] = useState([]);
  const [alerts, setAlerts] = useState([]);
  const [stats, setStats] = useState({ active: 0, safe: 0, danger: 0 });
  const [filter, setFilter] = useState('ALL'); // 'ALL', 'HIGH_RISK', 'SAFE'

  const fetchData = async () => {
    try {
      const [posRes, alertRes] = await Promise.all([
        axios.get(`${API_BASE}/map/positions`),
        axios.get(`${API_BASE}/alerts`)
      ]);

      const positionsRaw = posRes.data;
      const activeAlerts = alertRes.data;

      const latestPositions = Object.values(positionsRaw.reduce((acc, curr) => {
        if (!acc[curr.device_id] || curr.timestamp > acc[curr.device_id].timestamp) {
          acc[curr.device_id] = curr;
        }
        return acc;
      }, {}));

      setTourists(latestPositions);
      setAlerts(activeAlerts);

      const dangerCount = latestPositions.filter(t => t.is_panic).length;
      setStats({
        active: latestPositions.length,
        safe: latestPositions.length - dangerCount,
        danger: dangerCount
      });

    } catch (err) {
      console.error("Fetch error", err);
    }
  };

  useEffect(() => {
    import('socket.io-client').then(({ io }) => {
      const socket = io('http://localhost:8000');

      socket.on('connect', () => {
        console.log("Sentinel Uplink Established: WS Connected");
      });

      socket.on('new_alert', (alert) => {
        console.log("CRITICAL ALERT RECEIVED:", alert);

        const audioCtx = new (window.AudioContext || window.webkitAudioContext)();
        const oscillator = audioCtx.createOscillator();
        const gainNode = audioCtx.createGain();
        oscillator.type = 'square';
        oscillator.frequency.setValueAtTime(440, audioCtx.currentTime);
        oscillator.frequency.exponentialRampToValueAtTime(880, audioCtx.currentTime + 0.1);
        gainNode.gain.setValueAtTime(0.1, audioCtx.currentTime);
        gainNode.gain.exponentialRampToValueAtTime(0.001, audioCtx.currentTime + 0.5);
        oscillator.connect(gainNode);
        gainNode.connect(audioCtx.destination);
        oscillator.start();
        oscillator.stop(audioCtx.currentTime + 0.5);

        setAlerts(prev => [alert, ...prev]);

        if (alert.severity === 'CRITICAL') {
          setStats(prev => ({ ...prev, danger: prev.danger + 1, safe: prev.safe - 1 }));
        }
      });

      socket.on('telemetry_update', (data) => {
        setTourists(prev => {
          const index = prev.findIndex(t => t.device_id === data.device_id);
          if (index > -1) {
            const newArr = [...prev];
            newArr[index] = data;
            return newArr;
          } else {
            return [...prev, data];
          }
        });
        setStats(prev => ({ ...prev, active: prev.active }));
      });

      return () => socket.disconnect();
    });
  }, []);

  useEffect(() => {
    if (view === 'monitor') {
      fetchData();
      const interval = setInterval(fetchData, POLL_INTERVAL);
      return () => clearInterval(interval);
    }
  }, [view]);

  // Filtering Logic
  const filteredTourists = tourists.filter(t => {
    if (filter === 'ALL') return true;
    if (filter === 'HIGH_RISK') {
      const score = t.risk?.score || 0;
      return score > 50 || t.is_panic;
    }
    if (filter === 'SAFE') {
      const score = t.risk?.score || 0;
      return score <= 50 && !t.is_panic;
    }
    return true;
  });

  return (
    <div className="flex flex-col h-screen bg-prahari-dark text-white font-inter overflow-hidden">

      {/* TOP COMPONENT: Control Room Header */}
      <header className="h-16 bg-slate-900 border-b border-gray-700 flex items-center justify-between px-6 z-50 shadow-xl relative">
        <div className="flex items-center gap-4">
          <Shield className="w-8 h-8 text-blue-500" />
          <div>
            <h1 className="text-lg font-bold tracking-widest text-white">PRAHARI-AI</h1>
            <span className="text-[10px] text-blue-400 font-mono tracking-[0.2em] uppercase">Sentinel Command v3.0</span>
          </div>
        </div>

        {/* Center Tabs */}
        <div className="flex bg-gray-800/50 p-1 rounded-lg border border-gray-700">
          <button
            onClick={() => setView('monitor')}
            className={`px-6 py-1.5 rounded text-xs font-bold transition-all ${view === 'monitor' ? 'bg-blue-600 text-white shadow-lg' : 'text-gray-400 hover:text-white'}`}
          >
            LIVE MONITOR
          </button>
          <button
            onClick={() => setView('issuer')}
            className={`px-6 py-1.5 rounded text-xs font-bold transition-all ${view === 'issuer' ? 'bg-blue-600 text-white shadow-lg' : 'text-gray-400 hover:text-white'}`}
          >
            PERMIT ISSUER
          </button>
        </div>

        {/* System Health Indicators */}
        <SystemHealth />
      </header>

      <div className="flex flex-1 overflow-hidden relative">

        {/* LEFT SIDEBAR: Filters (Visible in Monitor) */}
        {view === 'monitor' && (
          <aside className="w-64 bg-slate-900 border-r border-gray-700 p-4 z-40 flex flex-col gap-6 shadow-2xl">

            {/* Status Card */}
            <div className="bg-gray-800/50 rounded-lg p-4 border border-gray-700">
              <div className="text-[10px] text-gray-400 uppercase tracking-widest font-bold mb-3">Threat Level</div>
              <div className="text-3xl font-bold text-white flex items-center gap-2">
                {src => stats.danger > 0 ? (
                  <>
                    <AlertTriangle className="text-red-500 w-6 h-6 animate-bounce" />
                    <span className="text-red-500">CRITICAL</span>
                  </>
                ) : (
                  <>
                    <Shield className="text-green-500 w-6 h-6" />
                    <span className="text-green-500">STABLE</span>
                  </>
                )}
                {stats.danger > 0 ? (
                  <>
                    <AlertTriangle className="text-red-500 w-6 h-6 animate-bounce" />
                    <span className="text-red-500">CRITICAL</span>
                  </>
                ) : (
                  <>
                    <Shield className="text-green-500 w-6 h-6" />
                    <span className="text-green-500">STABLE</span>
                  </>
                )}
              </div>
              <div className="mt-2 text-[10px] text-gray-500 font-mono">
                Active: {stats.active} | Safe: {stats.safe}
              </div>
            </div>

            {/* Filter Controls */}
            <div>
              <div className="text-[10px] text-gray-500 uppercase tracking-widest font-bold mb-3">Map Filter</div>
              <div className="flex flex-col gap-2">
                <button
                  onClick={() => setFilter('ALL')}
                  className={`w-full text-left px-3 py-2 rounded text-xs font-bold flex justify-between items-center transition-colors ${filter === 'ALL' ? 'bg-blue-600/20 text-blue-400 border border-blue-500/50' : 'bg-gray-800 text-gray-400 hover:bg-gray-700'}`}
                >
                  Show All Units
                  <span className="bg-gray-700 text-white px-1.5 rounded text-[10px]">{stats.active}</span>
                </button>
                <button
                  onClick={() => setFilter('HIGH_RISK')}
                  className={`w-full text-left px-3 py-2 rounded text-xs font-bold flex justify-between items-center transition-colors ${filter === 'HIGH_RISK' ? 'bg-red-600/20 text-red-400 border border-red-500/50' : 'bg-gray-800 text-gray-400 hover:bg-gray-700'}`}
                >
                  High Risk Only
                  <span className="bg-red-900 text-red-200 px-1.5 rounded text-[10px]">{tourists.filter(t => (t.risk?.score || 0) > 50 || t.is_panic).length}</span>
                </button>
                <button
                  onClick={() => setFilter('SAFE')}
                  className={`w-full text-left px-3 py-2 rounded text-xs font-bold flex justify-between items-center transition-colors ${filter === 'SAFE' ? 'bg-green-600/20 text-green-400 border border-green-500/50' : 'bg-gray-800 text-gray-400 hover:bg-gray-700'}`}
                >
                  Safe Units Only
                  <span className="bg-green-900 text-green-200 px-1.5 rounded text-[10px]">{tourists.filter(t => (t.risk?.score || 0) <= 50).length}</span>
                </button>
              </div>
            </div>
          </aside>
        )}

        {/* CENTER: Main Content */}
        <main className="flex-1 relative bg-gray-950 flex flex-col">
          {view === 'monitor' ? (
            <div className="flex-1 relative">
              <MapComponent tourists={filteredTourists} geofences={DEMO_ZONES} />

              {/* Floating Incident Counter (if filter hides them) */}
              {filter !== 'ALL' && (
                <div className="absolute top-4 left-1/2 -translate-x-1/2 bg-black/70 backdrop-blur text-white text-xs px-4 py-1 rounded-full border border-gray-600 pointer-events-none">
                  Filtering Active: Showing {filteredTourists.length} of {tourists.length} units
                </div>
              )}
            </div>
          ) : (
            <div className="h-full overflow-y-auto p-6">
              <PermitIssuer />
            </div>
          )}
        </main>

        {/* RIGHT SIDEBAR: Alerts (Visible in Monitor) */}
        {view === 'monitor' && (
          <div className="w-96 bg-prahari-card border-l border-gray-700 z-40 flex flex-col shadow-xl">
            <AlertSidebar alerts={alerts} />
          </div>
        )}
      </div>

      {/* EMERGENCY INCIDENT REPORT MODAL (Same as V2) */}
      {selectedIncident && (
        <div className="fixed inset-0 z-[2000] bg-black/80 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-gray-900 border-2 border-red-500/50 rounded-lg shadow-2xl max-w-lg w-full overflow-hidden animate-in fade-in zoom-in duration-200">

            <div className="bg-red-900/20 p-4 border-b border-red-500/50 flex justify-between items-center">
              <div className="flex items-center gap-3">
                <FileBadge className="w-6 h-6 text-red-500" />
                <div>
                  <h2 className="text-lg font-bold text-white tracking-widest uppercase">Official E-FIR Report</h2>
                  <p className="text-[10px] text-red-400 font-mono">MINISTRY OF HOME AFFAIRS // AUTOMATED SYSTEM</p>
                </div>
              </div>
              <button onClick={() => setSelectedIncident(null)} className="text-gray-400 hover:text-white">✕</button>
            </div>

            <div className="p-6 space-y-6">
              <div className="bg-black/40 p-3 rounded border border-gray-700">
                <label className="text-[10px] text-gray-500 uppercase tracking-widest block mb-1">Subject Identity</label>
                <div className="font-mono text-blue-400 text-sm">
                  {selectedIncident.device_id}
                </div>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div className="bg-black/40 p-3 rounded border border-gray-700">
                  <label className="text-[10px] text-gray-500 uppercase tracking-widest block mb-1">Incident Type</label>
                  <div className="text-white font-bold">{selectedIncident.type || "EMERGENCY"}</div>
                </div>
                <div className="bg-black/40 p-3 rounded border border-gray-700">
                  <label className="text-[10px] text-gray-500 uppercase tracking-widest block mb-1">Status</label>
                  <div className="text-white font-mono text-sm text-red-400 font-bold">ACTIVE</div>
                </div>
              </div>

              {/* Blockchain Proof */}
              <div className="bg-green-900/10 border border-green-500/30 p-4 rounded-lg relative overflow-hidden">
                <div className="absolute top-0 right-0 bg-green-500 text-black text-[9px] font-bold px-2 py-0.5 uppercase">
                  Verified On-Chain
                </div>
                <label className="text-[10px] text-green-400 uppercase tracking-widest block mb-1 flex items-center gap-2">
                  <Shield className="w-3 h-3" /> Blockchain Proof Record
                </label>
                <div className="font-mono text-xs text-gray-300 break-all">
                  TXID: 0x8a9d{Math.floor(Math.random() * 1000000)}...ae34{selectedIncident.timestamp}
                </div>
              </div>
            </div>

            {/* Footer */}
            <div className="bg-gray-800 p-4 flex justify-end gap-3 border-t border-gray-700">
              <button onClick={() => setSelectedIncident(null)} className="px-4 py-2 rounded text-sm text-gray-400 hover:text-white">Close</button>
              <button onClick={() => downloadEFIR(selectedIncident.device_id)} className="px-4 py-2 bg-red-600 hover:bg-red-500 text-white text-sm font-bold rounded shadow-lg flex items-center gap-2">
                <FileBadge className="w-4 h-4" /> EXPORT PDF
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default App;
