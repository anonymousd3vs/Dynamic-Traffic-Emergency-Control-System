/**
 * Traffic Control System Dashboard - Modern Light Theme
 * Minimalistic and clean design
 */

import { useEffect, useState } from 'react';
import { Menu, X, Bell, Settings, LogOut } from 'lucide-react';

// Components
import VideoFeed from './components/VideoFeed';
import MetricsPanel from './components/MetricsPanel';
import EmergencyAlert from './components/EmergencyAlert';
import TrafficFlowChart from './components/TrafficFlowChart';
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
    <div className="min-h-screen bg-gradient-to-br from-[#1a1f2e] via-[#242b3d] to-[#2d3548]">
      {/* Header */}
      <header className="sticky top-0 z-40 bg-slate-900/95 backdrop-blur-md border-b border-slate-700 shadow-lg">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            {/* Logo */}
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-gradient-to-br from-pastel-blue to-pastel-purple rounded-lg flex items-center justify-center shadow-glow-blue">
                <span className="text-lg font-bold text-slate-950">TC</span>
              </div>
              <div className="hidden sm:block">
                <h1 className="text-xl font-bold text-slate-50">Traffic Control System</h1>
                <p className="text-xs text-slate-400">Real-time Management</p>
              </div>
            </div>

            {/* Desktop Navigation */}
            <div className="hidden md:flex items-center gap-6">
              <div className="flex items-center gap-2">
                <div className={`w-2 h-2 rounded-full ${connected ? 'bg-green-500 animate-pulse' : 'bg-red-500 animate-pulse'}`} />
                <span className={`text-sm font-medium ${connected ? 'text-pastel-green' : 'text-pastel-rose'}`}>
                  {connected ? 'Connected' : 'Offline'}
                </span>
              </div>

              <button 
                onClick={() => setUnreadAlerts(0)}
                className="relative p-2 text-slate-400 hover:text-pastel-blue hover:bg-slate-800 rounded-lg transition-colors"
              >
                <Bell className="w-5 h-5" />
                {unreadAlerts > 0 && (
                  <span className="absolute top-1 right-1 w-5 h-5 bg-red-600 text-white text-xs rounded-full flex items-center justify-center font-bold">
                    {unreadAlerts}
                  </span>
                )}
              </button>

              <button 
                onClick={() => setShowSettings(!showSettings)}
                className="p-2 text-slate-400 hover:text-pastel-blue hover:bg-slate-800 rounded-lg transition-colors"
              >
                <Settings className="w-5 h-5" />
              </button>

              <button className="p-2 text-slate-400 hover:text-pastel-blue hover:bg-slate-800 rounded-lg transition-colors">
                <LogOut className="w-5 h-5" />
              </button>
            </div>

            {/* Mobile Menu Button */}
            <button 
              onClick={() => setShowMobileMenu(!showMobileMenu)}
              className="md:hidden p-2 text-slate-400 hover:text-pastel-blue hover:bg-slate-800 rounded-lg"
            >
              {showMobileMenu ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
            </button>
          </div>
        </div>

        {/* Mobile Menu */}
        {showMobileMenu && (
          <div className="md:hidden border-t border-slate-700 bg-slate-900">
            <div className="px-4 py-3 space-y-2">
              <button 
                onClick={() => setUnreadAlerts(0)}
                className="w-full text-left px-3 py-2 text-slate-400 hover:text-pastel-blue hover:bg-slate-800 rounded-lg flex items-center gap-2"
              >
                <Bell className="w-4 h-4" />
                Notifications
              </button>
              <button 
                onClick={() => {
                  setShowSettings(!showSettings);
                  setShowMobileMenu(false);
                }}
                className="w-full text-left px-3 py-2 text-slate-400 hover:text-pastel-blue hover:bg-slate-800 rounded-lg flex items-center gap-2"
              >
                <Settings className="w-4 h-4" />
                Settings
              </button>
              <button className="w-full text-left px-3 py-2 text-slate-400 hover:text-pastel-blue hover:bg-slate-800 rounded-lg flex items-center gap-2">
                <LogOut className="w-4 h-4" />
                Logout
              </button>
            </div>
          </div>
        )}
      </header>

      {/* Settings Panel */}
      {showSettings && (
        <div className="bg-slate-800 border-b border-slate-700 px-4 sm:px-6 lg:px-8 py-4">
          <div className="max-w-7xl mx-auto">
            <div className="grid sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-1">
                  Server URL
                </label>
                <input
                  type="text"
                  value={serverUrl}
                  onChange={(e) => setServerUrl(e.target.value)}
                  className="input"
                />
              </div>
              <div className="flex items-end gap-2">
                <button 
                  onClick={() => window.location.reload()}
                  className="flex-1 btn btn-primary"
                >
                  Reconnect
                </button>
                <button 
                  onClick={() => setShowSettings(false)}
                  className="px-4 py-2 border border-slate-700 text-slate-300 rounded-lg hover:bg-slate-700 transition-colors text-sm font-medium"
                >
                  Close
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Mode Toggle Bar */}
      <div className="bg-slate-800 border-b border-slate-700">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium text-slate-300">Simulation Mode:</span>
            <div className="flex gap-2">
              <button
                onClick={() => {
                  setSimulationMode('manual');
                  window.dispatchEvent(new CustomEvent('modeChanged', { detail: { mode: 'manual' } }));
                }}
                className={`px-4 py-2 rounded-lg text-sm font-semibold transition-all ${
                  simulationMode === 'manual'
                    ? 'bg-gradient-to-r from-pastel-blue to-pastel-purple text-slate-950 shadow-glow-blue'
                    : 'bg-slate-700 text-slate-300 hover:border-pastel-blue border border-slate-600'
                }`}
              >
                Manual
              </button>
              <button
                onClick={() => {
                  setSimulationMode('automatic');
                  window.dispatchEvent(new CustomEvent('modeChanged', { detail: { mode: 'automatic' } }));
                }}
                className={`px-4 py-2 rounded-lg text-sm font-semibold transition-all ${
                  simulationMode === 'automatic'
                    ? 'bg-gradient-to-r from-pastel-green to-pastel-teal text-white shadow-lg'
                    : 'bg-slate-700 text-slate-300 hover:border-green-500 border border-slate-600'
                }`}
              >
                Automatic
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Emergency Alert */}
        <div className="mb-8">
          <EmergencyAlert />
        </div>

        {/* Top Row: Detection Controls & Video Feed */}
        <div className="grid lg:grid-cols-3 gap-6 mb-8">
          <div className="lg:col-span-1">
            <div className="card">
              <DetectionControls 
                onVideoStop={() => clearAllAlerts()}
              />
            </div>
          </div>
          <div className="lg:col-span-2">
            <div className="card">
              <VideoFeed />
            </div>
          </div>
        </div>

        {/* Middle Row: Signal Visualizer & Control Panel */}
        <div className="grid lg:grid-cols-2 gap-6 mb-8">
          <div className="card">
            <TrafficSignalVisualizer simulationMode={simulationMode} />
          </div>
          <div className="card">
            <TrafficControlPanel simulationMode={simulationMode} />
          </div>
        </div>

        {/* Bottom Row: Metrics & Charts */}
        <div className="grid lg:grid-cols-2 gap-6">
          <div className="card">
            <h2 className="card-title">System Metrics</h2>
            <MetricsPanel />
          </div>
          <div className="card">
            <h2 className="card-title">Traffic Flow</h2>
            <TrafficFlowChart timeRange={10} />
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-700 bg-slate-900 mt-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex flex-col sm:flex-row justify-between items-center text-sm text-slate-400">
          </div>
        </div>
      </footer>
    </div>
  );
}

export default App;



