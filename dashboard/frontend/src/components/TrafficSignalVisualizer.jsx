import React, { useEffect, useState, useCallback } from 'react';

const TrafficSignalVisualizer = () => {
  const [signalStates, setSignalStates] = useState({
    north: { state: 'RED', timeRemaining: 0 },
    south: { state: 'RED', timeRemaining: 0 },
    east: { state: 'RED', timeRemaining: 0 },
    west: { state: 'RED', timeRemaining: 0 },
  });

  const [stats, setStats] = useState({
    currentPhase: 'PHASE_1',
    isRunning: true,
  });

  const fetchSignalStatus = useCallback(async () => {
    try {
      const response = await fetch('http://localhost:8765/api/signals/status');
      if (response.ok) {
        const data = await response.json();
        setSignalStates((prev) => data.signals || prev);
        setStats((prev) => data.statistics || prev);
      }
    } catch (error) {
      console.error('Error fetching signal status:', error);
    }
  }, []);

  useEffect(() => {
    const interval = setInterval(fetchSignalStatus, 500);
    fetchSignalStatus();
    return () => clearInterval(interval);
  }, [fetchSignalStatus]);

  const getSignalColor = (state) => {
    const colors = {
      RED: '#ef4444',
      YELLOW: '#eab308',
      GREEN: '#22c55e',
      EMERGENCY: '#2E6CCF',
      ALL_RED: '#7f1d1d',
    };
    return colors[state] || '#666';
  };

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-3">
          <h2 className="text-2xl font-bold bg-gradient-to-r from-pastel-blue to-pastel-purple bg-clip-text text-transparent">Traffic Junction</h2>
          <span className={`px-4 py-1 rounded-full text-sm font-semibold transition-all ${
            stats.isRunning ? 'bg-green-600/80 text-white ring-2 ring-green-500' : 'bg-slate-700/80 text-slate-300 ring-2 ring-slate-600'
          }`}>
            {stats.isRunning ? '● RUNNING' : '○ STOPPED'}
          </span>
        </div>
        <div className="text-sm text-slate-400 bg-slate-800/50 px-3 py-1 rounded-lg border border-slate-700">Phase: <span className="text-pastel-blue font-semibold">{stats.currentPhase}</span></div>
      </div>

      {/* Junction Visualization */}
      <div className="flex justify-center items-center w-full bg-[#242b3d] rounded-xl border border-slate-700/50 p-4 shadow-lg" style={{ height: '600px' }}>
        <svg viewBox="0 0 500 500" className="w-auto" style={{ height: '100%', maxWidth: '100%' }}>
          {/* Background */}
          <rect width="500" height="500" fill="#1a1f2e" rx="10" />

          {/* Roads */}
          <rect x="0" y="175" width="500" height="150" fill="#2d3548" />
          <rect x="175" y="0" width="150" height="500" fill="#2d3548" />

          {/* Lane Markings */}
          <line x1="250" y1="175" x2="250" y2="325" stroke="#a5b4fc" strokeWidth="2" strokeDasharray="8,8" />
          <line x1="175" y1="250" x2="325" y2="250" stroke="#a5b4fc" strokeWidth="2" strokeDasharray="8,8" />

          {/* Signal Posts and Lights */}
          
          {/* North */}
          <g>
            <rect x="215" y="30" width="70" height="35" fill="#111827" stroke="#374151" strokeWidth="2" rx="4" />
            <circle cx="250" cy="52" r="15" fill={getSignalColor(signalStates.north.state)} filter="url(#glow)" />
            <text x="250" y="85" textAnchor="middle" fill="#e5e7eb" fontSize="12" fontWeight="bold">N</text>
            {/* Timer Badge */}
            <rect x="228" y="95" width="44" height="20" fill="#0f172a" stroke="#374151" strokeWidth="1" rx="3" />
            <text x="250" y="108" textAnchor="middle" fill="#a5b4fc" fontSize="10" fontWeight="bold">{signalStates.north.timeRemaining}s</text>
          </g>

          {/* South */}
          <g>
            <rect x="215" y="435" width="70" height="35" fill="#111827" stroke="#374151" strokeWidth="2" rx="4" />
            <circle cx="250" cy="458" r="15" fill={getSignalColor(signalStates.south.state)} filter="url(#glow)" />
            <text x="250" y="485" textAnchor="middle" fill="#e5e7eb" fontSize="12" fontWeight="bold">S</text>
            {/* Timer Badge */}
            <rect x="228" y="395" width="44" height="20" fill="#0f172a" stroke="#374151" strokeWidth="1" rx="3" />
            <text x="250" y="408" textAnchor="middle" fill="#a5b4fc" fontSize="10" fontWeight="bold">{signalStates.south.timeRemaining}s</text>
          </g>

          {/* East */}
          <g>
            <rect x="435" y="215" width="35" height="70" fill="#111827" stroke="#374151" strokeWidth="2" rx="4" />
            <circle cx="458" cy="250" r="15" fill={getSignalColor(signalStates.east.state)} filter="url(#glow)" />
            <text x="485" y="255" textAnchor="middle" fill="#e5e7eb" fontSize="12" fontWeight="bold">E</text>
            {/* Timer Badge */}
            <rect x="435" y="290" width="40" height="18" fill="#0f172a" stroke="#374151" strokeWidth="1" rx="3" />
            <text x="455" y="301" textAnchor="middle" fill="#a5b4fc" fontSize="9" fontWeight="bold">{signalStates.east.timeRemaining}s</text>
          </g>

          {/* West */}
          <g>
            <rect x="30" y="215" width="35" height="70" fill="#111827" stroke="#374151" strokeWidth="2" rx="4" />
            <circle cx="52" cy="250" r="15" fill={getSignalColor(signalStates.west.state)} filter="url(#glow)" />
            <text x="15" y="255" textAnchor="middle" fill="#e5e7eb" fontSize="12" fontWeight="bold">W</text>
            {/* Timer Badge */}
            <rect x="25" y="290" width="40" height="18" fill="#0f172a" stroke="#374151" strokeWidth="1" rx="3" />
            <text x="45" y="301" textAnchor="middle" fill="#a5b4fc" fontSize="9" fontWeight="bold">{signalStates.west.timeRemaining}s</text>
          </g>

          {/* Center */}
          <circle cx="250" cy="250" r="25" fill="none" stroke="#374151" strokeWidth="1" />

          {/* Glow Filter */}
          <defs>
            <filter id="glow">
              <feGaussianBlur stdDeviation="3" result="coloredBlur" />
              <feMerge>
                <feMergeNode in="coloredBlur" />
                <feMergeNode in="SourceGraphic" />
              </feMerge>
            </filter>
          </defs>
        </svg>
      </div>
    </div>
  );
};

export default TrafficSignalVisualizer;


