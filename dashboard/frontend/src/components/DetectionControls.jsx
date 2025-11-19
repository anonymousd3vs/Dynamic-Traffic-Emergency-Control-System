import { useState, useEffect } from 'react';
import { Play, Square, Video, Settings, Camera, FileVideo, RefreshCw } from 'lucide-react';
import useDashboardStore from '../stores/dashboardStore';

/**
 * Detection Controls Component
 * Provides UI for configuring and controlling the traffic detection system
 */
export default function DetectionControls({ onVideoStart, onVideoStop }) {
  const [isRunning, setIsRunning] = useState(false);
  const [videoSource, setVideoSource] = useState('camera');
  const [cameraIndex, setCameraIndex] = useState('0');
  const [videoFile, setVideoFile] = useState('');
  const [videoFiles, setVideoFiles] = useState([]);
  const [laneFiltering, setLaneFiltering] = useState(true);
  const [hasConfig, setHasConfig] = useState(false);
  const [checkingConfig, setCheckingConfig] = useState(false);
  const [configPath, setConfigPath] = useState('');
  const { reset: resetDashboard } = useDashboardStore();

  // Fetch available video files on mount
  useEffect(() => {
    fetchVideoFiles();
    checkSystemStatus();
  }, []);

  // Check system status periodically
  useEffect(() => {
    const interval = setInterval(checkSystemStatus, 5000);
    return () => clearInterval(interval);
  }, []);

  const fetchVideoFiles = async () => {
    console.log('Fetching video files...');
    try {
      const response = await fetch('http://localhost:8765/api/videos/list');
      if (response.ok) {
        const data = await response.json();
        console.log('Video files received:', data);
        const videos = data.videos || [];
        setVideoFiles(videos);
        console.log('Video files set:', videos.length, 'videos');
      } else {
        console.error('Failed to fetch videos:', response.status);
      }
    } catch (error) {
      console.error('Error fetching video files:', error);
    }
  };

  const checkSystemStatus = async () => {
    try {
      const response = await fetch('http://localhost:8765/api/detection/status');
      if (response.ok) {
        const data = await response.json();
        setIsRunning(data.is_running || false);
      }
    } catch (error) {
      console.error('Error checking system status:', error);
    }
  };

  const checkConfiguration = async () => {
    if (videoSource !== 'file' || !videoFile) {
      setHasConfig(false);
      setCheckingConfig(false);
      return;
    }

    console.log('Checking config for:', videoFile);
    setCheckingConfig(true);
    setHasConfig(false);
    
    try {
      const response = await fetch('http://localhost:8765/api/config/check', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ video_source: videoFile })
      });

      if (response.ok) {
        const data = await response.json();
        console.log('Config check result:', data);
        setHasConfig(data.has_config || false);
        setConfigPath(data.config_path || '');
      } else {
        console.error('Config check failed:', response.status);
        setHasConfig(false);
      }
    } catch (error) {
      console.error('Error checking configuration:', error);
      setHasConfig(false);
    } finally {
      console.log('Config check complete');
      setCheckingConfig(false);
    }
  };

  // Check config when video file changes
  useEffect(() => {
    if (videoSource === 'file' && videoFile) {
      checkConfiguration();
    } else {
      setCheckingConfig(false);
      setHasConfig(false);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [videoFile, videoSource]);

  const handleStart = async () => {
    const source = videoSource === 'camera' ? cameraIndex : videoFile;
    
    if (!source) {
      alert('Please select a video source');
      return;
    }

    // For video files, make sure we have the latest config path
    let finalConfigPath = configPath;
    if (videoSource === 'file' && !finalConfigPath && laneFiltering) {
      // Re-check config path synchronously to ensure we have it
      try {
        const response = await fetch('http://localhost:8765/api/config/check', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ video_source: videoFile })
        });
        if (response.ok) {
          const data = await response.json();
          if (data.has_config && data.config_path) {
            finalConfigPath = data.config_path;
            setConfigPath(finalConfigPath);
          }
        }
      } catch (error) {
        console.error('Error re-checking config:', error);
      }
    }

    // If using file and lane filtering is enabled, check if we found config
    if (videoSource === 'file' && laneFiltering && !finalConfigPath) {
      const proceed = confirm(
        'No lane configuration found for this video. Do you want to:\n\n' +
        '1. Click OK to create configuration now\n' +
        '2. Click Cancel to run without lane filtering'
      );

      if (proceed) {
        await openConfigurationTool();
        return;
      } else {
        setLaneFiltering(false);
      }
    }

    try {
      const response = await fetch('http://localhost:8765/api/detection/start', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          source,
          lane_filtering: laneFiltering,
          config_path: finalConfigPath || undefined
        })
      });

      if (response.ok) {
        // ✅ RESET: Clear all metrics, history, and alerts when starting new video
        resetDashboard();
        setIsRunning(true);
        if (onVideoStart) onVideoStart(); // Call parent callback
        console.log('✅ Detection started - Dashboard metrics reset');
      } else {
        const error = await response.json();
        alert(`Failed to start detection: ${error.message || 'Unknown error'}`);
      }
    } catch (error) {
      alert(`Error starting detection: ${error.message}`);
    }
  };

  const handleStop = async () => {
    try {
      const response = await fetch('http://localhost:8765/api/detection/stop', {
        method: 'POST'
      });

      if (response.ok) {
        setIsRunning(false);
        if (onVideoStop) onVideoStop(); // Call parent callback to clear alerts
      }
    } catch (error) {
      alert(`Error stopping detection: ${error.message}`);
    }
  };

  const openConfigurationTool = async () => {
    if (!videoFile) {
      alert('Please select a video file first');
      return;
    }

    try {
      const response = await fetch('http://localhost:8765/api/config/launch', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ video_source: videoFile })
      });

      if (response.ok) {
        const data = await response.json();
        alert(`Configuration tool launched. ${data.message || 'Please configure lanes in the opened window.'}`);
        // Recheck configuration after tool closes with multiple attempts
        setTimeout(() => checkConfiguration(), 1000);
        setTimeout(() => checkConfiguration(), 2500);
        setTimeout(() => checkConfiguration(), 4000);
      }
    } catch (error) {
      alert(`Error launching configuration tool: ${error.message}`);
    }
  };

  const handleReset = async () => {
    if (!confirm('Reset vehicle count? This cannot be undone.')) {
      return;
    }

    try {
      await fetch('http://localhost:8765/api/detection/reset', {
        method: 'POST'
      });
    } catch (error) {
      console.error('Error resetting count:', error);
    }
  };

  return (
    <div className="card space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-bold flex items-center gap-2 bg-gradient-to-r from-pastel-blue to-pastel-purple bg-clip-text text-transparent">
          <Settings className="w-6 h-6 text-pastel-blue" />
          Detection Controls
        </h2>
        <div className={`px-3 py-1 rounded-full text-sm font-semibold ${
          isRunning ? 'bg-green-600 text-white' : 'bg-slate-700 text-slate-300'
        }`}>
          {isRunning ? '● RUNNING' : '○ STOPPED'}
        </div>
      </div>

      {/* Video Source Selection */}
      <div className="space-y-3">
        <label className="block text-sm font-semibold text-slate-200">
          Video Source
        </label>
        
        <div className="flex gap-2">
          <button
            onClick={() => setVideoSource('camera')}
            disabled={isRunning}
            className={`flex-1 flex items-center justify-center gap-2 px-4 py-3 rounded-lg font-medium transition-all ${
              videoSource === 'camera'
                ? 'bg-gradient-to-r from-pastel-blue to-blue-500 text-slate-950'
                : 'bg-slate-700 text-slate-300 hover:bg-slate-600'
            } ${isRunning ? 'opacity-50 cursor-not-allowed' : ''}`}
          >
            <Camera className="w-5 h-5" />
            Camera
          </button>
          
          <button
            onClick={() => setVideoSource('file')}
            disabled={isRunning}
            className={`flex-1 flex items-center justify-center gap-2 px-4 py-3 rounded-lg font-medium transition-all ${
              videoSource === 'file'
                ? 'bg-gradient-to-r from-pastel-blue to-blue-500 text-slate-950'
                : 'bg-slate-700 text-slate-300 hover:bg-slate-600'
            } ${isRunning ? 'opacity-50 cursor-not-allowed' : ''}`}
          >
            <FileVideo className="w-5 h-5" />
            Video File
          </button>
        </div>

        {videoSource === 'camera' ? (
          <div>
            <label className="block text-sm text-slate-400 mb-2">Camera Index</label>
            <input
              type="number"
              value={cameraIndex}
              onChange={(e) => setCameraIndex(e.target.value)}
              disabled={isRunning}
              className="w-full px-4 py-2 bg-slate-700 border border-slate-600 rounded-lg text-slate-50 focus:ring-2 focus:ring-pastel-blue disabled:opacity-50"
              min="0"
              max="9"
            />
          </div>
        ) : (
          <div>
            <div className="flex items-center justify-between mb-2">
              <label className="block text-sm text-slate-400">Select Video File</label>
              <button
                onClick={fetchVideoFiles}
                className="text-pastel-blue hover:text-pastel-blue/80 p-1"
                title="Refresh list"
              >
                <RefreshCw className="w-4 h-4" />
              </button>
            </div>
            
            <select
              value={videoFile}
              onChange={(e) => setVideoFile(e.target.value)}
              disabled={isRunning}
              className="w-full px-4 py-2 bg-slate-700 border border-slate-600 rounded-lg text-slate-50 focus:ring-2 focus:ring-pastel-blue disabled:opacity-50"
            >
              <option value="">-- Select a video --</option>
              {videoFiles.map((file, idx) => (
                <option key={idx} value={file}>{file}</option>
              ))}
            </select>

            {videoFile && (
              <div className="mt-3 p-3 bg-slate-700 rounded-lg border border-slate-600">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    {checkingConfig ? (
                      <>
                        <RefreshCw className="w-4 h-4 animate-spin text-pastel-blue" />
                        <span className="text-sm text-slate-400">Checking configuration...</span>
                      </>
                    ) : hasConfig ? (
                      <>
                        <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                        <span className="text-sm text-pastel-green">Configuration found ✓</span>
                      </>
                    ) : (
                      <>
                        <div className="w-2 h-2 bg-yellow-500 rounded-full"></div>
                        <span className="text-sm text-pastel-yellow">No configuration</span>
                      </>
                    )}
                  </div>
                  
                  <div className="flex gap-2">
                    <button
                      onClick={openConfigurationTool}
                      disabled={isRunning}
                      className={`text-xs px-3 py-1 rounded transition-all ${
                        hasConfig
                          ? 'bg-pastel-purple hover:bg-pastel-purple/80 text-slate-950'
                          : 'bg-pastel-blue hover:bg-pastel-blue/80 text-slate-950'
                      } ${isRunning ? 'opacity-50 cursor-not-allowed' : ''}`}
                    >
                      {hasConfig ? 'Reconfigure' : 'Configure Lanes'}
                    </button>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Detection Settings */}
      <div className="space-y-3">
        <label className="block text-sm font-semibold text-slate-200">
          Detection Settings
        </label>
        
        <div className="flex items-center justify-between p-3 bg-slate-700 rounded-lg border border-slate-600">
          <div className="flex items-center gap-2">
            <Settings className="w-5 h-5 text-pastel-blue" />
            <div>
              <div className="text-sm font-medium text-slate-50">Lane-Based Filtering</div>
              <div className="text-xs text-slate-400">Filter vehicles by configured lanes</div>
            </div>
          </div>
          <button
            onClick={() => setLaneFiltering(!laneFiltering)}
            disabled={isRunning}
            className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
              laneFiltering ? 'bg-pastel-blue' : 'bg-slate-600'
            } ${isRunning ? 'opacity-50 cursor-not-allowed' : ''}`}
          >
            <span
              className={`inline-block h-4 w-4 transform rounded-full bg-slate-950 transition-transform ${
                laneFiltering ? 'translate-x-6' : 'translate-x-1'
              }`}
            />
          </button>
        </div>
      </div>

      {/* Control Buttons */}
      <div className="flex gap-3">
        {!isRunning ? (
          <button
            onClick={handleStart}
            className="flex-1 flex items-center justify-center gap-2 px-6 py-3 bg-green-600 hover:bg-green-700 text-white font-semibold rounded-lg transition-colors shadow-glow-green"
          >
            <Play className="w-5 h-5" />
            Start Detection
          </button>
        ) : (
          <button
            onClick={handleStop}
            className="flex-1 flex items-center justify-center gap-2 px-6 py-3 bg-red-600 hover:bg-red-700 text-white font-semibold rounded-lg transition-colors shadow-glow-pink"
          >
            <Square className="w-5 h-5" />
            Stop Detection
          </button>
        )}
        
        <button
          onClick={handleReset}
          disabled={!isRunning}
          className="px-6 py-3 bg-slate-700 hover:bg-slate-600 text-pastel-blue font-semibold rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        >
          Reset Count
        </button>
      </div>
    </div>
  );
}


