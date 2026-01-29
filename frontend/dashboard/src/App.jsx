import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Shield, AlertTriangle, Users, Activity } from 'lucide-react';
import MapComponent from './components/Map';

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
    fetchData();
    const interval = setInterval(fetchData, POLL_INTERVAL);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="flex h-screen bg-prahari-dark text-white overflow-hidden">

      {/* Sidebar - Alerts */}
      <aside className="w-96 bg-prahari-card border-r border-gray-700 flex flex-col z-20 shadow-xl">
        <div className="p-6 border-b border-gray-700 flex items-center space-x-3 bg-gradient-to-r from-blue-900 to-prahari-card">
          <Shield className="w-8 h-8 text-blue-400" />
          <div>
            <h1 className="text-xl font-bold tracking-wider">PRAHARI-AI</h1>
            <p className="text-xs text-blue-300">SENTINEL COMMAND</p>
          </div>
        </div>

        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          <h2 className="text-sm font-semibold text-gray-400 uppercase tracking-widest mb-2">Live Alerts</h2>

          {alerts.length === 0 && (
            <div className="text-center text-gray-500 py-10">No Active Threats</div>
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
              <p className="mt-2 text-sm text-gray-300">{alert.message}</p>
              <div className="mt-2 text-xs font-mono text-gray-500">ID: {alert.device_id}</div>
            </div>
          ))}
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 flex flex-col relative">

        {/* HUD Overlay Header */}
        <header className="absolute top-4 left-4 right-4 z-[1000] flex space-x-4 pointer-events-none">
          <div className="bg-prahari-card/90 backdrop-blur-md border border-gray-600 rounded-lg p-3 flex-1 flex items-center justify-between shadow-lg pointer-events-auto">
            <div className="flex items-center space-x-8 px-4">
              <div className="text-center">
                <div className="text-xs text-gray-400 uppercase">Active Users</div>
                <div className="text-2xl font-bold text-blue-400 flex items-center justify-center gap-2">
                  <Users className="w-5 h-5" /> {stats.active}
                </div>
              </div>
              <div className="text-center">
                <div className="text-xs text-gray-400 uppercase">Safe</div>
                <div className="text-2xl font-bold text-green-400">{stats.safe}</div>
              </div>
              <div className="text-center">
                <div className="text-xs text-gray-400 uppercase">Critical</div>
                <div className="text-2xl font-bold text-red-500 animate-pulse">{stats.danger}</div>
              </div>
            </div>
            <div className="px-4 text-right">
              <div className="text-xs text-blue-300 font-mono">SYSTEM STATUS: ONLINE</div>
              <div className="text-xs text-gray-500">MoDoNER SECURE LINK ESTABLISHED</div>
            </div>
          </div>
        </header>

        {/* Map Container */}
        <div className="flex-1 bg-gray-900 relative">
          <MapComponent tourists={tourists} geofences={DEMO_ZONES} />
        </div>
      </main>
    </div>
  );
}

export default App;
