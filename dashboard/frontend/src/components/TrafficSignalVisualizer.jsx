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
      EMERGENCY: '#3b82f6',
      ALL_RED: '#7f1d1d',
    };
    return colors[state] || '#666';
  };

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <h2 className="text-lg font-semibold text-white">Traffic Junction</h2>
          <span className={`px-3 py-1 rounded text-xs font-medium ${stats.isRunning ? 'bg-green-600 text-white' : 'bg-[#2a2a2a] text-gray-400'
            }`}>
            {stats.isRunning ? '● RUNNING' : '○ STOPPED'}
          </span>
        </div>
        <div className="text-xs text-gray-500 bg-[#141414] px-3 py-1 rounded border border-[#2a2a2a]">
          Phase: <span className="text-white font-medium">{stats.currentPhase}</span>
        </div>
      </div>

      {/* Junction Visualization */}
      <div className="flex justify-center items-center w-full bg-[#0a0a0a] rounded-lg border border-[#2a2a2a] p-4" style={{ height: '400px' }}>
        <svg viewBox="0 0 500 500" className="w-auto" style={{ height: '100%', maxWidth: '100%' }}>
          {/* Background */}
          <rect width="500" height="500" fill="#0a0a0a" rx="10" />

          {/* Roads */}
          <rect x="0" y="175" width="500" height="150" fill="#1a1a1a" />
          <rect x="175" y="0" width="150" height="500" fill="#1a1a1a" />

          {/* Lane Markings */}
          <line x1="250" y1="175" x2="250" y2="325" stroke="#444" strokeWidth="2" strokeDasharray="8,8" />
          <line x1="175" y1="250" x2="325" y2="250" stroke="#444" strokeWidth="2" strokeDasharray="8,8" />

          {/* Signal Posts and Lights */}

          {/* North */}
          <g>
            <rect x="215" y="30" width="70" height="35" fill="#141414" stroke="#333" strokeWidth="2" rx="4" />
            <circle cx="250" cy="52" r="15" fill={getSignalColor(signalStates.north.state)} filter="url(#glow)" />
            <text x="250" y="85" textAnchor="middle" fill="#fff" fontSize="12" fontWeight="bold">N</text>
            <rect x="228" y="95" width="44" height="20" fill="#0a0a0a" stroke="#333" strokeWidth="1" rx="3" />
            <text x="250" y="108" textAnchor="middle" fill="#fff" fontSize="10" fontWeight="bold">{signalStates.north.timeRemaining}s</text>
          </g>

          {/* South */}
          <g>
            <rect x="215" y="435" width="70" height="35" fill="#141414" stroke="#333" strokeWidth="2" rx="4" />
            <circle cx="250" cy="458" r="15" fill={getSignalColor(signalStates.south.state)} filter="url(#glow)" />
            <text x="250" y="485" textAnchor="middle" fill="#fff" fontSize="12" fontWeight="bold">S</text>
            <rect x="228" y="395" width="44" height="20" fill="#0a0a0a" stroke="#333" strokeWidth="1" rx="3" />
            <text x="250" y="408" textAnchor="middle" fill="#fff" fontSize="10" fontWeight="bold">{signalStates.south.timeRemaining}s</text>
          </g>

          {/* East */}
          <g>
            <rect x="435" y="215" width="35" height="70" fill="#141414" stroke="#333" strokeWidth="2" rx="4" />
            <circle cx="458" cy="250" r="15" fill={getSignalColor(signalStates.east.state)} filter="url(#glow)" />
            <text x="485" y="255" textAnchor="middle" fill="#fff" fontSize="12" fontWeight="bold">E</text>
            <rect x="435" y="290" width="40" height="18" fill="#0a0a0a" stroke="#333" strokeWidth="1" rx="3" />
            <text x="455" y="301" textAnchor="middle" fill="#fff" fontSize="9" fontWeight="bold">{signalStates.east.timeRemaining}s</text>
          </g>

          {/* West */}
          <g>
            <rect x="30" y="215" width="35" height="70" fill="#141414" stroke="#333" strokeWidth="2" rx="4" />
            <circle cx="52" cy="250" r="15" fill={getSignalColor(signalStates.west.state)} filter="url(#glow)" />
            <text x="15" y="255" textAnchor="middle" fill="#fff" fontSize="12" fontWeight="bold">W</text>
            <rect x="25" y="290" width="40" height="18" fill="#0a0a0a" stroke="#333" strokeWidth="1" rx="3" />
            <text x="45" y="301" textAnchor="middle" fill="#fff" fontSize="9" fontWeight="bold">{signalStates.west.timeRemaining}s</text>
          </g>

          {/* Center */}
          <circle cx="250" cy="250" r="25" fill="none" stroke="#333" strokeWidth="1" />

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
