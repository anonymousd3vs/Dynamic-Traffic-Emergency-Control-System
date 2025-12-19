/**
 * MetricsPanel Component - Simplified for Users
 * Shows only user-relevant metrics
 */

import React from 'react';
import { Car, Users, Siren, MapPin } from 'lucide-react';
import useDashboardStore from '../stores/dashboardStore';

const MetricCard = ({ icon: Icon, label, value, highlight }) => {
  return (
    <div className={`p-4 rounded-lg bg-[#141414] border ${highlight ? 'border-red-800' : 'border-[#2a2a2a]'} hover:border-[#444] transition-colors`}>
      <Icon className={`w-5 h-5 mb-2 ${highlight ? 'text-red-400' : 'text-gray-400'}`} />
      <div className={`text-2xl font-bold mb-1 ${highlight ? 'text-red-400' : 'text-white'}`}>
        {value}
      </div>
      <div className="text-xs text-gray-500">{label}</div>
    </div>
  );
};

const MetricsPanel = () => {
  const { metrics, metricsHistory } = useDashboardStore();

  // Total vehicles: use zone counting if available, otherwise show current active vehicles
  // vehicle_count = cumulative count of vehicles crossing zone/line
  // active_vehicles = currently tracked vehicles in frame
  const totalVehicles = metrics.vehicle_count > 0
    ? metrics.vehicle_count
    : (metricsHistory.length > 0
      ? Math.max(...metricsHistory.map(m => m.active_vehicles || 0))
      : metrics.active_vehicles || 0);

  return (
    <div className="space-y-4">
      {/* Primary Metrics Grid - User Relevant Only */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <MetricCard
          icon={Users}
          label="Vehicles in Frame"
          value={metrics.active_vehicles || 0}
        />
        <MetricCard
          icon={Car}
          label="Peak Vehicles"
          value={totalVehicles}
        />
        <MetricCard
          icon={MapPin}
          label="Detection Mode"
          value={metrics.mode === 'zone_counting' ? 'Zone' : (metrics.mode || 'N/A')}
        />
        <MetricCard
          icon={Siren}
          label="Ambulance"
          value={metrics.ambulance_detected ? 'DETECTED' : 'Clear'}
          highlight={metrics.ambulance_detected}
        />
      </div>

      {/* Status Info - Simplified */}
      <div className="bg-[#141414] rounded-lg border border-[#2a2a2a] p-4">
        <div className="flex justify-between items-center text-sm">
          <span className="text-gray-500">Last Update:</span>
          <span className="font-mono text-gray-400 text-xs">
            {metrics.timestamp ? new Date(metrics.timestamp).toLocaleTimeString() : 'Waiting...'}
          </span>
        </div>
      </div>
    </div>
  );
};

export default MetricsPanel;
