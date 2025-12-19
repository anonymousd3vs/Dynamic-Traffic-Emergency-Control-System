/**
 * Traffic Control Panel - Monochrome Theme
 */

import React, { useEffect, useState, useCallback } from 'react';
import { AlertCircle, RotateCcw, Zap } from 'lucide-react';
import useDashboardStore from '../stores/dashboardStore';

const TrafficControlPanel = ({ simulationMode }) => {
  const [mode, setMode] = useState(simulationMode || 'manual');
  const [videoLane, setVideoLane] = useState('north');
  const [selectedDirection, setSelectedDirection] = useState('north');
  const [stats, setStats] = useState({ totalAmbulances: 0 });
  const [lastAmbulanceTriggered, setLastAmbulanceTriggered] = useState(false);

  const { metrics } = useDashboardStore();

  useEffect(() => {
    if (simulationMode) setMode(simulationMode);
  }, [simulationMode]);

  const fetchSignalStatus = async () => {
    try {
      const response = await fetch('http://localhost:8765/api/signals/status');
      if (response.ok) {
        const data = await response.json();
        setStats((prev) => ({
          ...prev,
          totalAmbulances: data.statistics?.totalAmbulances || prev.totalAmbulances,
        }));
      }
    } catch (error) {
      console.error('Error fetching signal status:', error);
    }
  };

  useEffect(() => {
    const interval = setInterval(fetchSignalStatus, 1000);
    fetchSignalStatus();
    return () => clearInterval(interval);
  }, []);

  const handleAmbulance = useCallback(async (direction) => {
    try {
      const response = await fetch('http://localhost:8765/api/signals/ambulance', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ direction, confidence: 0.95 }),
      });
      if (response.ok) console.log(`Ambulance triggered for ${direction}`);
    } catch (error) {
      console.error('Error triggering ambulance:', error);
    }
  }, []);

  const handleReset = async () => {
    try {
      await fetch('http://localhost:8765/api/signals/reset', { method: 'POST' });
    } catch (error) {
      console.error('Error resetting:', error);
    }
  };

  const handleSelectLane = async (lane) => {
    try {
      const response = await fetch('http://localhost:8765/api/signals/select-lane', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ lane }),
      });
      if (response.ok) console.log(`Lane selected: ${lane}`);
    } catch (error) {
      console.error('Error selecting lane:', error);
    }
  };

  useEffect(() => {
    if (mode === 'automatic' && metrics.ambulance_detected && !lastAmbulanceTriggered) {
      handleAmbulance(videoLane);
      setLastAmbulanceTriggered(true);
    } else if (!metrics.ambulance_detected && lastAmbulanceTriggered) {
      setLastAmbulanceTriggered(false);
    }
  }, [metrics.ambulance_detected, mode, videoLane, lastAmbulanceTriggered, handleAmbulance]);

  const directions = ['north', 'south', 'east', 'west'];
  const directionLabels = { north: 'NORTH', south: 'SOUTH', east: 'EAST', west: 'WEST' };

  return (
    <div className="space-y-4">
      <h3 className="text-lg font-semibold text-white">Control Panel</h3>

      {/* Mode Status */}
      <div className="bg-[#141414] p-4 rounded-lg border border-[#2a2a2a] space-y-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Zap className="w-4 h-4 text-gray-400" />
            <span className="text-sm text-gray-300">Current Mode</span>
          </div>
          <div className={`px-3 py-1.5 rounded text-xs font-medium ${mode === 'manual' ? 'bg-white text-black' : 'bg-green-600 text-white'
            }`}>
            {mode === 'manual' ? 'Manual' : 'Automatic'}
          </div>
        </div>

        <p className="text-xs text-gray-500 p-2 bg-[#0a0a0a] rounded border border-[#2a2a2a]">
          {mode === 'manual'
            ? 'Click direction buttons to trigger ambulance manually'
            : `Ambulance auto-triggered when detected in ${videoLane.toUpperCase()} lane`}
        </p>

        {/* Lane Selection - Automatic mode */}
        {mode === 'automatic' && (
          <div className="pt-3 border-t border-[#2a2a2a]">
            <label className="text-xs text-gray-500 mb-2 block">Video Lane</label>
            <div className="grid grid-cols-4 gap-2">
              {directions.map((lane) => (
                <button
                  key={lane}
                  onClick={() => { setVideoLane(lane); handleSelectLane(lane); }}
                  className={`py-1.5 rounded text-xs font-medium transition-colors ${videoLane === lane
                    ? 'bg-white text-black'
                    : 'bg-[#1a1a1a] text-gray-400 hover:text-white border border-[#2a2a2a]'
                    }`}
                >
                  {lane.toUpperCase()}
                </button>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Manual Mode Controls */}
      {mode === 'manual' && (
        <>
          <div className="bg-[#141414] p-4 rounded-lg border border-[#2a2a2a] text-center">
            <div className="text-xs text-gray-500 uppercase tracking-wider">Selected Direction</div>
            <div className="text-xl font-bold text-white mt-1">{directionLabels[selectedDirection]}</div>
          </div>

          <div className="grid grid-cols-2 gap-2">
            {directions.map((dir) => (
              <button
                key={dir}
                onClick={() => setSelectedDirection(dir)}
                className={`py-2 rounded text-sm font-medium transition-colors ${selectedDirection === dir
                  ? 'bg-white text-black'
                  : 'bg-[#1a1a1a] text-gray-400 hover:text-white border border-[#2a2a2a]'
                  }`}
              >
                {directionLabels[dir]}
              </button>
            ))}
          </div>

          <button
            onClick={() => handleAmbulance(selectedDirection)}
            className="w-full flex items-center justify-center gap-2 px-4 py-3 bg-red-600 hover:bg-red-700 text-white font-medium rounded-lg transition-colors"
          >
            <AlertCircle className="w-4 h-4" />
            Trigger Ambulance ({directionLabels[selectedDirection]})
          </button>
        </>
      )}

      {/* Automatic Mode Status */}
      {mode === 'automatic' && (
        <div className="bg-[#141414] border border-[#2a2a2a] p-4 rounded-lg">
          <div className="flex items-center gap-3">
            <div className={`w-3 h-3 rounded-full ${metrics.ambulance_detected ? 'bg-red-500 animate-pulse' : 'bg-[#333]'}`} />
            <span className={`text-sm ${metrics.ambulance_detected ? 'text-red-400' : 'text-gray-400'}`}>
              {metrics.ambulance_detected ? 'Ambulance detected' : 'No ambulance in frame'}
            </span>
          </div>
        </div>
      )}

      {/* Reset Button */}
      <button
        onClick={handleReset}
        className="w-full flex items-center justify-center gap-2 px-4 py-2.5 bg-[#1a1a1a] hover:bg-[#242424] text-gray-300 font-medium rounded-lg transition-colors border border-[#2a2a2a]"
      >
        <RotateCcw className="w-4 h-4" />
        Reset System
      </button>
    </div>
  );
};

export default TrafficControlPanel;
