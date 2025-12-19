/**
 * Traffic Control System Dashboard - Modern Light Theme
 * Minimalistic and clean design
 */

import { useEffect, useState } from 'react';
import { Bell, Settings } from 'lucide-react';

// Components
import VideoFeed from './components/VideoFeed';
import MetricsPanel from './components/MetricsPanel';
import EmergencyAlert from './components/EmergencyAlert';
import DetectionControls from './components/DetectionControls';
import TrafficSignalVisualizer from './components/TrafficSignalVisualizer';
import TrafficControlPanel from './components/TrafficControlPanel';

// Services and Store
import wsService from './services/websocket';
import useDashboardStore from './stores/dashboardStore';

function App() {
  const {
    connected,
    setConnected,
    updateMetrics,
    updateFrame,
    addAlert,
    clearAllAlerts
  } = useDashboardStore();

  const [serverUrl, setServerUrl] = useState('http://localhost:8765');
  const [showMobileMenu, setShowMobileMenu] = useState(false);
  const [showSettings, setShowSettings] = useState(false);
  const [unreadAlerts, setUnreadAlerts] = useState(0);
  const [simulationMode, setSimulationMode] = useState('manual');

  useEffect(() => {
    console.log('App.jsx: Attempting WebSocket connection to', serverUrl);

    wsService.connect(
      serverUrl,
      () => {
        console.log('App.jsx: Dashboard connected to backend');
        setConnected(true);
      },
      (reason) => {
        console.log('App.jsx: Dashboard disconnected:', reason);
        setConnected(false);
      }
    );

    const unsubMetrics = wsService.on('metrics', (data) => {
      console.log('📊 Metrics received:', data);
      if (data && data.data) {
        updateMetrics(data.data);
      }
    });

    const unsubFrame = wsService.on('frame', (data) => {
      if (data && data.frame) {
        updateFrame(data.frame, data.metadata);
      }
    });

    const unsubAlert = wsService.on('alert', (data) => {
      if (data) {
        addAlert(data);
        setUnreadAlerts(prev => prev + 1);
      }
    });

    const pingInterval = setInterval(() => {
      if (wsService.isConnected()) {
        console.log('App.jsx: Sending keepalive ping');
        wsService.ping();
      }
    }, 15000);

    const healthCheckInterval = setInterval(() => {
      if (!wsService.isConnected()) {
        console.log('App.jsx: Connection lost, attempting to reconnect...');
        wsService.connect(
          serverUrl,
          () => {
            console.log('App.jsx: Reconnection successful');
            setConnected(true);
          },
          (reason) => {
            console.log('App.jsx: Reconnection failed:', reason);
            setConnected(false);
          }
        );
      }
    }, 30000);

    return () => {
      clearInterval(pingInterval);
      clearInterval(healthCheckInterval);
      unsubMetrics();
      unsubFrame();
      unsubAlert();
      wsService.disconnect();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [serverUrl]);

  return (
    <div className="min-h-screen bg-[#0a0a0a]">
      {/* Header */}
      <header className="sticky top-0 z-40 bg-[#0a0a0a] border-b border-[#1a1a1a]">
        <div className="max-w-[1600px] mx-auto px-6">
          <div className="flex justify-between items-center h-14">
            {/* Logo */}
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 bg-white rounded flex items-center justify-center">
                <span className="text-sm font-bold text-black">TC</span>
              </div>
              <div>
                <h1 className="text-base font-semibold text-white">Traffic Control</h1>
              </div>
            </div>

            {/* Status & Actions */}
            <div className="flex items-center gap-4">
              <div className="flex items-center gap-2">
                <div className={`w-2 h-2 rounded-full ${connected ? 'bg-green-500' : 'bg-red-500'}`} />
                <span className={`text-xs font-medium ${connected ? 'text-green-400' : 'text-red-400'}`}>
                  {connected ? 'Connected' : 'Offline'}
                </span>
              </div>

              <button
                onClick={() => setUnreadAlerts(0)}
                className="p-2 text-gray-500 hover:text-white rounded transition-colors"
              >
                <Bell className="w-4 h-4" />
              </button>

              <button
                onClick={() => setShowSettings(!showSettings)}
                className="p-2 text-gray-500 hover:text-white rounded transition-colors"
              >
                <Settings className="w-4 h-4" />
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Settings Panel */}
      {showSettings && (
        <div className="bg-[#141414] border-b border-[#1a1a1a] px-6 py-4">
          <div className="max-w-[1600px] mx-auto">
            <div className="flex gap-4 items-end">
              <div className="flex-1 max-w-md">
                <label className="block text-xs font-medium text-gray-400 mb-2">
                  Server URL
                </label>
                <input
                  type="text"
                  value={serverUrl}
                  onChange={(e) => setServerUrl(e.target.value)}
                  className="input"
                />
              </div>
              <button
                onClick={() => window.location.reload()}
                className="btn btn-primary"
              >
                Reconnect
              </button>
              <button
                onClick={() => setShowSettings(false)}
                className="btn btn-secondary"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Mode Toggle */}
      <div className="bg-[#0a0a0a] border-b border-[#1a1a1a]">
        <div className="max-w-[1600px] mx-auto px-6 py-3">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-gray-500 uppercase tracking-wider">Mode</span>
            <div className="flex gap-2">
              <button
                onClick={() => {
                  setSimulationMode('manual');
                  window.dispatchEvent(new CustomEvent('modeChanged', { detail: { mode: 'manual' } }));
                }}
                className={`px-4 py-1.5 rounded text-xs font-medium transition-all ${simulationMode === 'manual'
                  ? 'bg-white text-black'
                  : 'bg-[#1a1a1a] text-gray-400 hover:text-white border border-[#2a2a2a]'
                  }`}
              >
                Manual
              </button>
              <button
                onClick={() => {
                  setSimulationMode('automatic');
                  window.dispatchEvent(new CustomEvent('modeChanged', { detail: { mode: 'automatic' } }));
                }}
                className={`px-4 py-1.5 rounded text-xs font-medium transition-all ${simulationMode === 'automatic'
                  ? 'bg-green-600 text-white'
                  : 'bg-[#1a1a1a] text-gray-400 hover:text-white border border-[#2a2a2a]'
                  }`}
              >
                Automatic
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <main className="max-w-[1600px] mx-auto px-6 py-6">
        {/* Emergency Alert */}
        <EmergencyAlert />

        {/* Row 1: Detection Controls | Live Feed */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-5 mt-5">
          <div className="lg:col-span-4">
            <div className="card">
              <h2 className="card-title">Detection Controls</h2>
              <DetectionControls onVideoStop={() => clearAllAlerts()} />
            </div>
          </div>
          <div className="lg:col-span-8">
            <div className="card min-h-[400px]">
              <h2 className="card-title">Live Feed</h2>
              <VideoFeed />
            </div>
          </div>
        </div>

        {/* Row 2: Traffic Junction | System Metrics */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-5 mt-5">
          <div className="card">
            <TrafficSignalVisualizer simulationMode={simulationMode} />
          </div>
          <div className="card">
            <TrafficControlPanel simulationMode={simulationMode} />
          </div>
        </div>

        {/* Row 3: Metrics */}
        <div className="mt-5">
          <div className="card">
            <h2 className="card-title">System Metrics</h2>
            <MetricsPanel />
          </div>
        </div>
      </main>
    </div>
  );
}

export default App;



