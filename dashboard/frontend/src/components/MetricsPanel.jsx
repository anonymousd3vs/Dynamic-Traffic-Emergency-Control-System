/**
 * MetricsPanel Component
 * Displays real-time system metrics in card format
 */

import React, { useMemo } from 'react';
import { Activity, Car, Users, Gauge, Clock } from 'lucide-react';
import useDashboardStore from '../stores/dashboardStore';

const MetricCard = ({ icon: Icon, label, value, unit, color = 'blue' }) => {
  const colorClasses = {
    blue: 'bg-slate-800 border-pastel-blue/30 text-pastel-blue',
    green: 'bg-slate-800 border-green-500/30 text-pastel-green',
    yellow: 'bg-slate-800 border-yellow-500/30 text-pastel-yellow',
    red: 'bg-slate-800 border-red-500/30 text-pastel-rose',
    purple: 'bg-slate-800 border-pastel-purple/30 text-pastel-purple',
  };

  const IconComponent = Icon;

  return (
    <div className={`p-4 rounded-lg border ${colorClasses[color]} transition-all hover:shadow-glow-blue`}>
      <IconComponent className="w-6 h-6 mb-2" />
      <div className="text-2xl font-bold mb-1">
        {value}
        {unit && <span className="text-xs text-slate-400 ml-1">{unit}</span>}
      </div>
      <div className="text-xs text-slate-300">{label}</div>
    </div>
  );
};

const MetricsPanel = () => {
  const { metrics, getAverageFPS, getVehicleStats } = useDashboardStore();
  
  // ✅ FIXED: Use useMemo to recalculate whenever these functions change
  const avgFPS = useMemo(() => getAverageFPS(1), [getAverageFPS]); // Last 1 minute
  const vehicleStats = useMemo(() => getVehicleStats(5), [getVehicleStats]); // Last 5 minutes

  return (
    <div className="space-y-4">
      
      {/* Primary Metrics Grid */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-4">
        <MetricCard
          icon={Activity}
          label="Current FPS"
          value={metrics.fps.toFixed(1)}
          color="green"
        />
        
        <MetricCard
          icon={Users}
          label="Active Vehicles"
          value={metrics.active_vehicles}
          color="blue"
        />
        
        <MetricCard
          icon={Car}
          label="Total Count"
          value={metrics.vehicle_count}
          color="purple"
        />
        
        <MetricCard
          icon={Gauge}
          label="Avg FPS (1m)"
          value={avgFPS.toFixed(1)}
          color="yellow"
        />
        
        <MetricCard
          icon={Clock}
          label="Frame Count"
          value={metrics.frame_count}
          color="blue"
        />
      </div>

      {/* Vehicle Statistics */}
      {vehicleStats.current > 0 && (
        <div className="bg-slate-800 rounded-xl shadow-md border border-slate-700 p-6">
          <h3 className="font-bold text-slate-50 mb-4">Vehicle Statistics (5 min)</h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="text-center">
              <div className="text-2xl font-bold text-pastel-green">{vehicleStats.current}</div>
              <div className="text-xs text-slate-400">Current</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-pastel-blue">{vehicleStats.max}</div>
              <div className="text-xs text-slate-400">Peak</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-pastel-yellow">{vehicleStats.avg.toFixed(1)}</div>
              <div className="text-xs text-slate-400">Average</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-pastel-purple">{vehicleStats.min}</div>
              <div className="text-xs text-slate-400">Minimum</div>
            </div>
          </div>
        </div>
      )}

      {/* System Info */}
      <div className="bg-slate-800 rounded-xl shadow-md border border-slate-700 p-6">
        <h3 className="font-bold text-slate-50 mb-4">System Information</h3>
        <div className="space-y-3 text-sm">
          <div className="flex justify-between items-center">
            <span className="text-slate-400">Detection Mode:</span>
            <span className="font-mono text-pastel-green font-semibold uppercase">{metrics.mode}</span>
          </div>
          <div className="flex justify-between items-center">
            <span className="text-slate-400">Video Source:</span>
            <span className="font-mono text-pastel-blue">{metrics.video_source}</span>
          </div>
          
          {/* Ambulance Status */}
          <div className="flex justify-between items-center">
            <span className="text-slate-400">Ambulance Status:</span>
            <div className="flex items-center gap-2">
              <span className={`font-mono font-bold uppercase ${
                metrics.ambulance_detected ? 'text-pastel-rose' : 'text-pastel-green'
              }`}>
                {metrics.ambulance_detected ? '🚨 DETECTED' : '✅ CLEAR'}
              </span>
              {metrics.ambulance_detected && (
                <span className="text-xs text-slate-400">
                  ({(metrics.ambulance_confidence * 100).toFixed(1)}%)
                </span>
              )}
            </div>
          </div>
          
          {/* Stability indicator */}
          {metrics.ambulance_detected && (
            <div className="flex justify-between items-center">
              <span className="text-slate-400">Detection Stability:</span>
              <span className={`font-mono font-bold ${
                metrics.ambulance_stable ? 'text-pastel-green' : 'text-pastel-yellow'
              }`}>
                {metrics.ambulance_stable ? '🟢 STABLE' : '🟡 UNSTABLE'}
              </span>
            </div>
          )}
          
          <div className="flex justify-between items-center">
            <span className="text-slate-400">Last Update:</span>
            <span className="font-mono text-pastel-purple">
              {metrics.timestamp ? new Date(metrics.timestamp).toLocaleTimeString() : 'N/A'}
            </span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default MetricsPanel;


