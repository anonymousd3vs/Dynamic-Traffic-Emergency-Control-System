/**
 * TrafficFlowChart Component
 * Displays historical traffic data using Recharts
 */

import React, { useMemo } from 'react';
import { LineChart, Line, AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { TrendingUp, BarChart3 } from 'lucide-react';
import useDashboardStore from '../stores/dashboardStore';

const TrafficFlowChart = ({ timeRange = 10 }) => {
  const { getMetricsRange } = useDashboardStore();

  // Get metrics for the specified time range
  const chartData = useMemo(() => {
    const metrics = getMetricsRange(timeRange);
    
    return metrics.map((m) => {
      const time = new Date(m.timestamp);
      return {
        time: time.toLocaleTimeString('en-US', { 
          hour: '2-digit', 
          minute: '2-digit',
          second: '2-digit'
        }),
        timestamp: time.getTime(),
        vehicles: m.active_vehicles || 0,
        fps: m.fps || 0,
        totalCount: m.vehicle_count || 0,
      };
    });
  }, [getMetricsRange, timeRange]);

  // Calculate statistics
  const stats = useMemo(() => {
    if (chartData.length === 0) return null;

    const vehicles = chartData.map(d => d.vehicles);
    const peak = Math.max(...vehicles);
    const avg = vehicles.reduce((a, b) => a + b, 0) / vehicles.length;
    const current = vehicles[vehicles.length - 1] || 0;

    return { peak, avg: avg.toFixed(1), current };
  }, [chartData]);

  // Custom tooltip
  const CustomTooltip = ({ active, payload }) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-slate-800 border border-slate-700 rounded p-3 shadow-glow-blue">
          <p className="text-sm text-slate-300 mb-2">{payload[0].payload.time}</p>
          {payload.map((entry, index) => (
            <div key={index} className="flex items-center gap-2 text-sm">
              <div 
                className="w-3 h-3 rounded-full" 
                style={{ backgroundColor: entry.color }}
              />
              <span className="text-slate-400">{entry.name}:</span>
              <span className="font-semibold text-slate-50">
                {entry.name === 'FPS' ? entry.value.toFixed(1) : entry.value}
              </span>
            </div>
          ))}
        </div>
      );
    }
    return null;
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <BarChart3 className="w-6 h-6 text-pastel-blue" />
          <h2 className="text-2xl font-bold bg-gradient-to-r from-pastel-blue to-pastel-purple bg-clip-text text-transparent">Traffic Flow</h2>
        </div>
        <div className="text-sm text-slate-400 bg-slate-800/50 px-3 py-1 rounded-lg border border-slate-700">
          Last <span className="text-pastel-blue font-semibold">{timeRange}</span> seconds
        </div>
      </div>

      {/* Statistics Cards */}
      {stats && (
        <div className="grid grid-cols-3 gap-3">
          <div className="bg-slate-800 border-2 border-green-500/30 rounded-lg shadow-md p-4 text-center hover:shadow-glow-green transition-shadow">
            <div className="text-xs font-semibold text-slate-400 uppercase mb-2">Current Vehicles</div>
            <div className="text-3xl font-bold text-pastel-green">{stats.current}</div>
          </div>
          <div className="bg-slate-800 border-2 border-red-500/30 rounded-lg shadow-md p-4 text-center hover:shadow-glow-pink transition-shadow">
            <div className="text-xs font-semibold text-slate-400 uppercase mb-2">Peak Vehicles</div>
            <div className="text-3xl font-bold text-pastel-rose">{stats.peak}</div>
          </div>
          <div className="bg-slate-800 border-2 border-pastel-blue/30 rounded-lg shadow-md p-4 text-center hover:shadow-glow-blue transition-shadow">
            <div className="text-xs font-semibold text-slate-400 uppercase mb-2">Average Vehicles</div>
            <div className="text-3xl font-bold text-pastel-blue">{stats.avg}</div>
          </div>
        </div>
      )}

      {/* Vehicle Count Chart */}
      <div className="bg-slate-800 rounded-lg shadow-md border border-slate-700 p-6">
        <h3 className="text-lg font-semibold text-slate-50 mb-4 flex items-center gap-2">
          <TrendingUp className="w-5 h-5 text-pastel-blue" />
          Active Vehicles Over Time
        </h3>
        {chartData.length > 0 ? (
          <ResponsiveContainer width="100%" height={280}>
            <AreaChart data={chartData}>
              <defs>
                <linearGradient id="colorVehicles" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#a5b4fc" stopOpacity={0.8}/>
                  <stop offset="95%" stopColor="#a5b4fc" stopOpacity={0.1}/>
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#374151" strokeWidth={0.5} />
              <XAxis 
                dataKey="time" 
                stroke="#9ca3af"
                tick={{ fontSize: 12 }}
                interval="preserveStartEnd"
              />
              <YAxis stroke="#9ca3af" tick={{ fontSize: 12 }} />
              <Tooltip content={<CustomTooltip />} />
              <Area 
                type="monotone" 
                dataKey="vehicles" 
                stroke="#a5b4fc" 
                strokeWidth={2}
                fillOpacity={1} 
                fill="url(#colorVehicles)"
                name="Vehicles"
              />
            </AreaChart>
          </ResponsiveContainer>
        ) : (
          <div className="h-80 flex items-center justify-center text-slate-500">
            <div className="text-center space-y-3">
              <TrendingUp className="w-16 h-16 mx-auto opacity-30" />
              <p className="text-lg font-semibold">Waiting for data...</p>
              <p className="text-sm text-slate-600">Start detection to see traffic flow analysis</p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default TrafficFlowChart;


