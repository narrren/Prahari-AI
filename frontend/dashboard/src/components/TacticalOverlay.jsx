import React, { useState, useEffect } from 'react';
import { Play, Pause, ChevronLeft, ChevronRight, Activity, Clock, Navigation } from 'lucide-react';
import axios from 'axios';

const API_BASE = "http://localhost:8000/api/v1";

const TacticalOverlay = ({ deviceId, onClose, onPlaybackUpdate }) => {
    const [history, setHistory] = useState([]);
    const [currentIndex, setCurrentIndex] = useState(0);
    const [isPlaying, setIsPlaying] = useState(false);
    const [speed, setSpeed] = useState(100); // ms per step
    const [loading, setLoading] = useState(true);

    // Fetch History
    useEffect(() => {
        const fetchHistory = async () => {
            if (!deviceId) return;
            setLoading(true);
            try {
                const res = await axios.get(`${API_BASE}/telemetry/history/${deviceId}?hours=6`);
                // Sort ascending by time
                const sorted = res.data.sort((a, b) => a.timestamp - b.timestamp);
                setHistory(sorted);
                setCurrentIndex(sorted.length - 1); // Start at end

                // Lift state up to Map for rendering the line
                onPlaybackUpdate(sorted, sorted.length - 1);
            } catch (err) {
                console.error("Fetch history failed", err);
            } finally {
                setLoading(false);
            }
        };
        fetchHistory();
    }, [deviceId]);

    // Playback Loop
    useEffect(() => {
        let interval;
        if (isPlaying && history.length > 0) {
            interval = setInterval(() => {
                setCurrentIndex(prev => {
                    const next = prev + 1;
                    if (next >= history.length) {
                        setIsPlaying(false);
                        return prev;
                    }
                    onPlaybackUpdate(history, next);
                    return next;
                });
            }, speed);
        }
        return () => clearInterval(interval);
    }, [isPlaying, history, speed, onPlaybackUpdate]);

    // Handle Time Slider Buffer
    const handleSliderChange = (e) => {
        const idx = parseInt(e.target.value);
        setCurrentIndex(idx);
        onPlaybackUpdate(history, idx);
        setIsPlaying(false); // Pause on manual seek
    };

    if (!deviceId) return null;

    const currentPoint = history[currentIndex];

    return (
        <div className="absolute bottom-6 left-14 right-14 z-[9999] bg-gray-900/90 backdrop-blur-md border border-gray-700 rounded-xl p-4 shadow-2xl text-white">
            <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-3">
                    <Activity size={16} className="text-blue-400" />
                    <span className="text-xs font-bold tracking-widest text-blue-100 uppercase">
                        TACTICAL REPLAY: {deviceId}
                    </span>
                    {loading && <span className="text-[10px] text-yellow-400 animate-pulse">DOWNLOADING TELEMETRY...</span>}
                </div>
                <button onClick={onClose} className="text-xs text-red-400 hover:text-red-300 font-bold">
                    EXIT VCR MODE
                </button>
            </div>

            {/* VCR Display Screen */}
            <div className="grid grid-cols-4 gap-4 mb-3">
                <div className="bg-black/40 p-2 rounded border border-gray-800 flex items-center gap-2">
                    <Clock size={14} className="text-gray-500" />
                    <div>
                        <div className="text-[9px] text-gray-500">TIMESTAMP</div>
                        <div className="text-xs font-mono font-bold">
                            {currentPoint ? new Date(currentPoint.timestamp * 1000).toLocaleTimeString() : "--:--:--"}
                        </div>
                    </div>
                </div>
                <div className="bg-black/40 p-2 rounded border border-gray-800 flex items-center gap-2">
                    <Navigation size={14} className="text-gray-500" />
                    <div>
                        <div className="text-[9px] text-gray-500">SPEED (Rec)</div>
                        <div className="text-xs font-mono font-bold text-green-400">
                            {currentPoint ? currentPoint.speed.toFixed(1) : "0.0"} m/s
                        </div>
                    </div>
                </div>
                <div className="bg-black/40 p-2 rounded border border-gray-800 col-span-2 flex flex-col justify-center">
                    <div className="text-[9px] text-gray-500 mb-1">TIMELINE PROGRESS</div>
                    <div className="w-full bg-gray-800 h-1.5 rounded-full overflow-hidden">
                        <div
                            className="bg-blue-500 h-full transition-all duration-100"
                            style={{ width: `${(currentIndex / Math.max(history.length - 1, 1)) * 100}%` }}
                        />
                    </div>
                </div>
            </div>

            {/* SCRUBBER */}
            <div className="flex items-center gap-4">
                <button
                    onClick={() => setIsPlaying(!isPlaying)}
                    className={`p-2 rounded-full border ${isPlaying ? 'bg-yellow-500/20 border-yellow-500 text-yellow-400' : 'bg-green-600 border-green-500 text-white hover:bg-green-500 transition-all'}`}
                >
                    {isPlaying ? <Pause size={16} fill="currentColor" /> : <Play size={16} fill="currentColor" />}
                </button>

                <input
                    type="range"
                    min="0"
                    max={Math.max(history.length - 1, 0)}
                    value={currentIndex}
                    onChange={handleSliderChange}
                    className="w-full h-2 bg-gray-800 rounded-lg appearance-none cursor-pointer accent-blue-500"
                />

                <span className="text-[10px] font-mono text-gray-400 min-w-[60px] text-right">
                    -{history.length > 0 ? ((history[history.length - 1].timestamp - (currentPoint?.timestamp || 0)) / 60).toFixed(0) : 0} MIN AGO
                </span>
            </div>
        </div>
    );
};

export default TacticalOverlay;
