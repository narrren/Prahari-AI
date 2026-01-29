import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Shield, AlertTriangle, Users, Activity, FileBadge, Map as MapIcon, Globe } from 'lucide-react';
import MapComponent from './components/Map';
import PermitIssuer from './components/PermitIssuer';

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
  const [tourists, setTourists] = useState([]);
  const [alerts, setAlerts] = useState([]);
  const [stats, setStats] = useState({ active: 0, safe: 0, danger: 0 });

  const fetchData = async () => {
    try {
      const [posRes, alertRes] = await Promise.all([
        axios.get(`${API_BASE}/map/positions`),
        axios.get(`${API_BASE}/alerts`)
      ]);

      const positions = posRes.data;
      const activeAlerts = alertRes.data;

      setTourists(positions);
      setAlerts(activeAlerts);

      // Calc Stats
      const dangerCount = positions.filter(t => t.is_panic).length;
      setStats({
        active: positions.length,
        safe: positions.length - dangerCount,
        danger: dangerCount
      });

    } catch (err) {
      console.error("Fetch error", err);
    }
  };

  useEffect(() => {
    if (view === 'monitor') {
      fetchData();
      const interval = setInterval(fetchData, POLL_INTERVAL);
      return () => clearInterval(interval);
    }
  }, [view]);

  return (
    <div className="flex h-screen bg-prahari-dark text-white overflow-hidden font-inter">

      {/* Sidebar - Navigation & Context */}
      <aside className="w-96 bg-prahari-card border-r border-gray-700 flex flex-col z-20 shadow-xl">
        <div className="p-6 border-b border-gray-700 bg-gradient-to-r from-blue-900 to-prahari-card">
          <div className="flex items-center space-x-3 mb-6">
            <Shield className="w-8 h-8 text-blue-400" />
            <div>
              <h1 className="text-xl font-bold tracking-wider">PRAHARI-AI</h1>
              <p className="text-xs text-blue-300">SENTINEL COMMAND</p>
            </div>
          </div>

          {/* Navigation Tabs */}
          <div className="flex bg-gray-900/50 p-1 rounded-lg">
            <button
              onClick={() => setView('monitor')}
              className={`flex-1 flex items-center justify-center gap-2 py-2 rounded-md text-sm font-medium transition-all ${view === 'monitor' ? 'bg-blue-600 text-white shadow-lg' : 'text-gray-400 hover:text-white'}`}
            >
              <MapIcon className="w-4 h-4" /> Monitor
            </button>
            <button
              onClick={() => setView('issuer')}
              className={`flex-1 flex items-center justify-center gap-2 py-2 rounded-md text-sm font-medium transition-all ${view === 'issuer' ? 'bg-blue-600 text-white shadow-lg' : 'text-gray-400 hover:text-white'}`}
            >
              <FileBadge className="w-4 h-4" /> Permits
            </button>
          </div>
        </div>

        {/* Sidebar Content Switched by View */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4">

          {view === 'monitor' ? (
            <>
              <h2 className="text-xs font-bold text-gray-500 uppercase tracking-widest flex items-center gap-2 mb-4">
                <Activity className="w-4 h-4" /> Live Incident Feed
              </h2>

              {alerts.length === 0 && (
                <div className="p-8 text-center border-2 border-dashed border-gray-700 rounded-xl">
                  <Globe className="w-10 h-10 text-gray-600 mx-auto mb-3" />
                  <p className="text-gray-500 font-medium">All Zones Secure</p>
                  <p className="text-xs text-gray-600 mt-1">No anomalies detected in the trek sectors.</p>
                </div>
              )}

              {alerts.map((alert) => (
                <div key={alert.alert_id} className={`p-4 rounded-lg border-l-4 shadow-md transition-all hover:bg-gray-800 ${alert.severity === 'CRITICAL' || alert.is_panic ? 'bg-red-900/20 border-red-500' :
                  alert.type === 'GEOFENCE_BREACH' ? 'bg-orange-900/20 border-orange-500' : 'bg-blue-900/20 border-blue-500'
                  }`}>
                  <div className="flex justify-between items-start">
                    <div className="flex items-center space-x-2">
                      <AlertTriangle className={`w-4 h-4 ${alert.severity === 'CRITICAL' ? 'text-red-500' : 'text-orange-400'}`} />
                      <span className="font-bold text-sm">{alert.type}</span>
                    </div>
                    <span className="text-xs text-gray-400">{new Date(alert.timestamp * 1000).toLocaleTimeString()}</span>
                  </div>
                  <p className="mt-2 text-sm text-gray-300 leading-relaxed">{alert.message}</p>
                  <div className="mt-2 text-xs font-mono text-gray-500 bg-gray-900/50 p-1 rounded inline-block">ID: {alert.device_id}</div>
                </div>
              ))}
            </>
          ) : (
            <>
              <h2 className="text-xs font-bold text-gray-500 uppercase tracking-widest flex items-center gap-2 mb-4">
                <FileBadge className="w-4 h-4" /> Issuer Logs
              </h2>
              <div className="text-sm text-gray-400 p-4 bg-gray-800/50 rounded-lg border border-gray-700">
                <p className="mb-2"><strong>Authority:</strong> ADMIN_NODE_01</p>
                <p className="mb-2"><strong>Network:</strong> LocalStack / Ganache</p>
                <p><strong>Status:</strong> <span className="text-green-400">Connected</span></p>
              </div>
              <div className="text-xs text-gray-500 mt-4 text-center">
                Select a tourist profile to issue credentials.
              </div>
            </>
          )}

        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 flex flex-col relative bg-gray-900">

        {/* HUD Overlay Header (Only for Monitor) */}
        {view === 'monitor' && (
          <header className="absolute top-4 left-4 right-4 z-[1000] flex space-x-4 pointer-events-none">
            <div className="bg-prahari-card/90 backdrop-blur-md border border-gray-600 rounded-lg p-3 flex-1 flex items-center justify-between shadow-lg pointer-events-auto">
              <div className="flex items-center space-x-12 px-6">
                <div className="text-center">
                  <div className="text-[10px] text-gray-400 uppercase tracking-widest font-bold">Active Trackers</div>
                  <div className="text-3xl font-bold text-blue-400 flex items-center justify-center gap-2 font-mono">
                    {stats.active}
                  </div>
                </div>
                <div className="text-center">
                  <div className="text-[10px] text-gray-400 uppercase tracking-widest font-bold">Safe</div>
                  <div className="text-3xl font-bold text-green-400 font-mono">{stats.safe}</div>
                </div>
                <div className="text-center">
                  <div className="text-[10px] text-gray-400 uppercase tracking-widest font-bold">Critical</div>
                  <div className="text-3xl font-bold text-red-500 animate-pulse font-mono">{stats.danger}</div>
                </div>
              </div>
              <div className="px-4 text-right border-l border-gray-600 pl-6">
                <div className="text-xs text-blue-300 font-mono flex items-center justify-end gap-2">
                  <span className="w-2 h-2 rounded-full bg-green-500 animate-pulse"></span>
                  SYSTEM ONLINE
                </div>
                <div className="text-[10px] text-gray-500 mt-1">MoDoNER SECURE UPLINK ESTABLISHED</div>
              </div>
            </div>
          </header>
        )}

        {/* Dynamic Content View */}
        <div className="flex-1 relative overflow-hidden">
          {view === 'monitor' ? (
            <MapComponent tourists={tourists} geofences={DEMO_ZONES} />
          ) : (
            <div className="h-full overflow-y-auto bg-gradient-to-br from-gray-900 to-gray-800">
              <PermitIssuer />
            </div>
          )}
        </div>
      </main>
    </div>
  );
}

export default App;
