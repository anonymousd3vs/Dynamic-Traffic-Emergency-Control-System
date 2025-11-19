/**
 * Dashboard Store using Zustand
 * Manages global state for the traffic control system dashboard
 */

import { create } from 'zustand';

const useDashboardStore = create((set, get) => ({
  // Connection state
  connected: false,
  connectionError: null,
  
  // Real-time metrics
  metrics: {
    fps: 0,
    frame_count: 0,
    vehicle_count: 0,
    active_vehicles: 0,
    ambulance_detected: false,
    ambulance_stable: false,
    ambulance_confidence: 0,
    mode: 'unknown',
    video_source: 'unknown',
  },
  
  // Video frame
  currentFrame: null,
  frameMetadata: {},
  
  // Metrics history for charts (last 10 minutes ~600 data points at 1Hz)
  metricsHistory: [],
  maxHistoryLength: 600,
  
  // Alerts
  alerts: [],
  maxAlerts: 10,
  
  // Actions
  setConnected: (connected) => set({ connected }),
  
  setConnectionError: (error) => set({ connectionError: error }),
  
  updateMetrics: (newMetrics) => {
    const state = get();
    const timestamp = new Date().toISOString();
    
    // Update current metrics
    set({ 
      metrics: { 
        ...state.metrics, 
        ...newMetrics,
        timestamp 
      } 
    });
    
    // Add to history
    const historyEntry = {
      ...state.metrics,
      ...newMetrics,
      timestamp
    };
    
    const newHistory = [...state.metricsHistory, historyEntry];
    
    // Trim history if too long
    if (newHistory.length > state.maxHistoryLength) {
      newHistory.shift();
    }
    
    set({ metricsHistory: newHistory });
  },
  
  updateFrame: (frameData, metadata) => {
    set({
      currentFrame: frameData,
      frameMetadata: metadata || {}
    });
  },
  
  addAlert: (alert) => {
    const state = get();
    const newAlert = {
      ...alert,
      id: Date.now(),
      timestamp: new Date().toISOString()
    };
    
    const newAlerts = [newAlert, ...state.alerts];
    
    // Keep only last N alerts
    if (newAlerts.length > state.maxAlerts) {
      newAlerts.pop();
    }
    
    set({ alerts: newAlerts });
  },
  
  clearAlert: (alertId) => {
    const state = get();
    set({
      alerts: state.alerts.filter(alert => alert.id !== alertId)
    });
  },
  
  clearAllAlerts: () => set({ alerts: [] }),
  
  // Get metrics for specific time range
  getMetricsRange: (minutes = 5) => {
    const state = get();
    const now = new Date();
    const cutoff = new Date(now.getTime() - minutes * 60 * 1000);
    
    return state.metricsHistory.filter(entry => {
      const entryTime = new Date(entry.timestamp);
      return entryTime >= cutoff;
    });
  },
  
  // Get average FPS over time
  getAverageFPS: (minutes = 1) => {
    const metrics = get().getMetricsRange(minutes);
    if (metrics.length === 0) return 0;
    
    const sum = metrics.reduce((acc, m) => acc + (m.fps || 0), 0);
    return sum / metrics.length;
  },
  
  // Get vehicle count statistics
  getVehicleStats: (minutes = 5) => {
    const metrics = get().getMetricsRange(minutes);
    if (metrics.length === 0) {
      return { max: 0, min: 0, avg: 0, current: 0 };
    }
    
    const counts = metrics.map(m => m.active_vehicles || 0);
    return {
      max: Math.max(...counts),
      min: Math.min(...counts),
      avg: counts.reduce((a, b) => a + b, 0) / counts.length,
      current: get().metrics.active_vehicles || 0
    };
  },
  
  // Reset store (metrics only, preserve connection state)
  reset: () => {
    // ✅ PRESERVE: Keep connection state while resetting metrics
    set({
      // DO NOT reset connected status - preserve WebSocket connection
      connectionError: null,
      metrics: {
        fps: 0,
        frame_count: 0,
        vehicle_count: 0,
        active_vehicles: 0,
        ambulance_detected: false,
        ambulance_stable: false,
        ambulance_confidence: 0,
        mode: 'unknown',
        video_source: 'unknown',
      },
      currentFrame: null,
      frameMetadata: {},
      metricsHistory: [],
      alerts: [],
    });
  },
}));

export default useDashboardStore;
