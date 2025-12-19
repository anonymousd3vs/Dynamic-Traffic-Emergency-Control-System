/**
 * EmergencyAlert Component - Monochrome Theme
 */

import React, { useEffect, useState, useRef } from 'react';
import { AlertTriangle, Siren, X } from 'lucide-react';
import useDashboardStore from '../stores/dashboardStore';

const EmergencyAlert = () => {
  const { metrics, alerts, clearAlert, addAlert } = useDashboardStore();
  const [audioEnabled, setAudioEnabled] = useState(false);
  const [audioContext, setAudioContext] = useState(null);
  const wasAmbulanceDetectedRef = useRef(false);

  const playAlertSound = () => {
    if (!audioEnabled || !audioContext) return;
    try {
      const oscillator = audioContext.createOscillator();
      const gainNode = audioContext.createGain();
      oscillator.connect(gainNode);
      gainNode.connect(audioContext.destination);
      oscillator.frequency.value = 800;
      oscillator.type = 'sine';
      gainNode.gain.setValueAtTime(0.3, audioContext.currentTime);
      gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.5);
      oscillator.start(audioContext.currentTime);
      oscillator.stop(audioContext.currentTime + 0.5);
    } catch (error) { console.error('Error playing alert sound:', error); }
  };

  const initAudio = () => {
    if (!audioContext) {
      const ctx = new (window.AudioContext || window.webkitAudioContext)();
      setAudioContext(ctx);
      setAudioEnabled(true);
    } else {
      setAudioEnabled(!audioEnabled);
    }
  };

  useEffect(() => {
    if (metrics.ambulance_detected && audioEnabled) playAlertSound();
  }, [metrics.ambulance_detected, audioEnabled]);

  useEffect(() => {
    if (wasAmbulanceDetectedRef.current && !metrics.ambulance_detected) {
      addAlert({
        alert_type: 'ambulance_cleared',
        severity: 'info',
        data: { confidence: 0, stable: false, reason: 'Ambulance left the frame' }
      });
    }
    wasAmbulanceDetectedRef.current = metrics.ambulance_detected;
  }, [metrics.ambulance_detected, addAlert]);

  const showMainAlert = metrics.ambulance_detected;

  return (
    <div className="space-y-4">
      {/* Main Ambulance Alert */}
      {showMainAlert && (
        <div className="bg-red-950 border border-red-800 rounded-lg p-4 flex items-center justify-between">
          <div className="flex items-center gap-4 flex-1">
            <Siren className="w-8 h-8 animate-pulse text-red-500" />
            <div className="flex-1">
              <h3 className="text-lg font-bold text-red-400">AMBULANCE DETECTED</h3>
              {metrics.ambulance_stable && (
                <span className="text-xs text-green-400 mt-1 inline-block">✓ Stable Detection</span>
              )}
            </div>
          </div>
          <button
            onClick={initAudio}
            className={`px-3 py-1.5 rounded text-xs font-medium transition-colors ${audioEnabled ? 'bg-red-600 text-white' : 'bg-[#1a1a1a] text-gray-400 border border-[#2a2a2a]'
              }`}
          >
            {audioEnabled ? '🔊 ON' : '🔇 OFF'}
          </button>
        </div>
      )}

      {/* Alert History */}
      {alerts.length > 0 && (
        <div className="bg-[#141414] rounded-lg border border-[#2a2a2a] p-4">
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-2">
              <AlertTriangle className="w-4 h-4 text-yellow-500" />
              <span className="text-sm font-medium text-gray-300">Alert History</span>
            </div>
            <span className="bg-[#1a1a1a] text-gray-400 px-2 py-0.5 rounded text-xs border border-[#2a2a2a]">
              {alerts.length}
            </span>
          </div>

          <div className="space-y-2 max-h-48 overflow-y-auto">
            {alerts.map((alert) => (
              <div
                key={alert.id}
                className={`p-3 rounded border flex items-start justify-between ${alert.alert_type === 'ambulance_detected'
                    ? 'bg-red-950/50 border-red-900'
                    : 'bg-green-950/50 border-green-900'
                  }`}
              >
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-1">
                    {alert.alert_type === 'ambulance_detected' && (
                      <Siren className="w-4 h-4 text-red-500" />
                    )}
                    {alert.alert_type === 'ambulance_cleared' && (
                      <AlertTriangle className="w-4 h-4 text-green-500" />
                    )}
                    <span className={`text-sm font-medium ${alert.alert_type === 'ambulance_detected' ? 'text-red-400' : 'text-green-400'
                      }`}>
                      {alert.alert_type === 'ambulance_detected' ? 'Ambulance Detected' : 'Ambulance Cleared'}
                    </span>
                  </div>
                  <div className="text-xs text-gray-500">
                    {new Date(alert.timestamp).toLocaleTimeString()}
                  </div>
                </div>
                <button
                  onClick={() => clearAlert(alert.id)}
                  className="text-gray-600 hover:text-gray-400 transition-colors ml-2"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default EmergencyAlert;
