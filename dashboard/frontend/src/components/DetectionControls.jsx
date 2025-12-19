import { useState, useEffect } from 'react';
import { Play, Square, Camera, FileVideo, RefreshCw, Settings } from 'lucide-react';
import useDashboardStore from '../stores/dashboardStore';

/**
 * Detection Controls Component - Monochrome Theme
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

  useEffect(() => { fetchVideoFiles(); checkSystemStatus(); }, []);
  useEffect(() => { const i = setInterval(checkSystemStatus, 5000); return () => clearInterval(i); }, []);

  const fetchVideoFiles = async () => {
    try {
      const response = await fetch('http://localhost:8765/api/videos/list');
      if (response.ok) {
        const data = await response.json();
        setVideoFiles(data.videos || []);
      }
    } catch (error) { console.error('Error fetching videos:', error); }
  };

  const checkSystemStatus = async () => {
    try {
      const response = await fetch('http://localhost:8765/api/detection/status');
      if (response.ok) {
        const data = await response.json();
        setIsRunning(data.is_running || false);
      }
    } catch (error) { console.error('Error checking status:', error); }
  };

  const checkConfiguration = async () => {
    if (videoSource !== 'file' || !videoFile) { setHasConfig(false); setCheckingConfig(false); return; }
    setCheckingConfig(true); setHasConfig(false);
    try {
      const r = await fetch('http://localhost:8765/api/config/check', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ video_source: videoFile })
      });
      if (r.ok) { const d = await r.json(); setHasConfig(d.has_config || false); setConfigPath(d.config_path || ''); }
    } catch (e) { setHasConfig(false); } finally { setCheckingConfig(false); }
  };

  useEffect(() => {
    if (videoSource === 'file' && videoFile) checkConfiguration();
    else { setCheckingConfig(false); setHasConfig(false); }
  }, [videoFile, videoSource]);

  const handleStart = async () => {
    const source = videoSource === 'camera' ? cameraIndex : videoFile;
    if (!source) { alert('Please select a video source'); return; }

    let finalConfigPath = configPath;
    if (videoSource === 'file' && !finalConfigPath && laneFiltering) {
      try {
        const r = await fetch('http://localhost:8765/api/config/check', {
          method: 'POST', headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ video_source: videoFile })
        });
        if (r.ok) { const d = await r.json(); if (d.has_config && d.config_path) { finalConfigPath = d.config_path; setConfigPath(finalConfigPath); } }
      } catch (e) { }
    }

    if (videoSource === 'file' && laneFiltering && !finalConfigPath) {
      const proceed = confirm('No lane configuration found. OK to configure now, Cancel to run without lane filtering.');
      if (proceed) { await openConfigurationTool(); return; } else { setLaneFiltering(false); }
    }

    try {
      const r = await fetch('http://localhost:8765/api/detection/start', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ source, lane_filtering: laneFiltering, config_path: finalConfigPath || undefined })
      });
      if (r.ok) { resetDashboard(); setIsRunning(true); if (onVideoStart) onVideoStart(); }
      else { const e = await r.json(); alert(`Failed: ${e.message || 'Unknown error'}`); }
    } catch (e) { alert(`Error: ${e.message}`); }
  };

  const handleStop = async () => {
    try {
      const r = await fetch('http://localhost:8765/api/detection/stop', { method: 'POST' });
      if (r.ok) { setIsRunning(false); if (onVideoStop) onVideoStop(); }
    } catch (e) { alert(`Error: ${e.message}`); }
  };

  const openConfigurationTool = async () => {
    if (!videoFile) { alert('Select a video file first'); return; }
    try {
      const r = await fetch('http://localhost:8765/api/config/launch', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ video_source: videoFile })
      });
      if (r.ok) {
        alert('Configuration tool launched. Configure lanes in the opened window.');
        setTimeout(checkConfiguration, 1000);
        setTimeout(checkConfiguration, 2500);
      }
    } catch (e) { alert(`Error: ${e.message}`); }
  };

  const handleReset = async () => {
    if (!confirm('Reset vehicle count? This cannot be undone.')) return;
    try { await fetch('http://localhost:8765/api/detection/reset', { method: 'POST' }); } catch (e) { }
  };

  return (
    <div className="space-y-4">
      {/* Status Badge */}
      <div className="flex items-center justify-between">
        <span className="text-xs text-gray-500 uppercase tracking-wider">Status</span>
        <span className={`px-2.5 py-1 rounded text-xs font-medium ${isRunning ? 'bg-green-600 text-white' : 'bg-[#1a1a1a] text-gray-400 border border-[#2a2a2a]'
          }`}>
          {isRunning ? '● Running' : '○ Stopped'}
        </span>
      </div>

      {/* Video Source */}
      <div className="space-y-2">
        <label className="text-xs text-gray-500 uppercase tracking-wider">Video Source</label>
        <div className="grid grid-cols-2 gap-2">
          <button
            onClick={() => setVideoSource('camera')}
            disabled={isRunning}
            className={`flex items-center justify-center gap-2 py-2 rounded text-sm font-medium transition-colors ${videoSource === 'camera' ? 'bg-white text-black' : 'bg-[#1a1a1a] text-gray-400 border border-[#2a2a2a]'
              } ${isRunning ? 'opacity-50 cursor-not-allowed' : 'hover:text-white'}`}
          >
            <Camera className="w-4 h-4" /> Camera
          </button>
          <button
            onClick={() => setVideoSource('file')}
            disabled={isRunning}
            className={`flex items-center justify-center gap-2 py-2 rounded text-sm font-medium transition-colors ${videoSource === 'file' ? 'bg-white text-black' : 'bg-[#1a1a1a] text-gray-400 border border-[#2a2a2a]'
              } ${isRunning ? 'opacity-50 cursor-not-allowed' : 'hover:text-white'}`}
          >
            <FileVideo className="w-4 h-4" /> File
          </button>
        </div>

        {videoSource === 'camera' ? (
          <input
            type="number"
            value={cameraIndex}
            onChange={(e) => setCameraIndex(e.target.value)}
            disabled={isRunning}
            placeholder="Camera Index"
            className="w-full px-3 py-2 bg-[#141414] border border-[#2a2a2a] rounded text-white text-sm focus:outline-none focus:border-white disabled:opacity-50"
            min="0" max="9"
          />
        ) : (
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-xs text-gray-500">Select Video</span>
              <button onClick={fetchVideoFiles} className="text-gray-500 hover:text-white">
                <RefreshCw className="w-3 h-3" />
              </button>
            </div>
            <select
              value={videoFile}
              onChange={(e) => setVideoFile(e.target.value)}
              disabled={isRunning}
              className="w-full px-3 py-2 bg-[#141414] border border-[#2a2a2a] rounded text-white text-sm focus:outline-none focus:border-white disabled:opacity-50"
            >
              <option value="">-- Select --</option>
              {videoFiles.map((f, i) => <option key={i} value={f}>{f}</option>)}
            </select>

            {videoFile && (
              <div className="flex items-center justify-between p-2 bg-[#0a0a0a] rounded border border-[#2a2a2a]">
                <div className="flex items-center gap-2">
                  {checkingConfig ? (
                    <><RefreshCw className="w-3 h-3 animate-spin text-gray-400" /><span className="text-xs text-gray-500">Checking...</span></>
                  ) : hasConfig ? (
                    <><div className="w-2 h-2 bg-green-500 rounded-full" /><span className="text-xs text-green-400">Config found</span></>
                  ) : (
                    <><div className="w-2 h-2 bg-yellow-500 rounded-full" /><span className="text-xs text-yellow-400">No config</span></>
                  )}
                </div>
                <button
                  onClick={openConfigurationTool}
                  disabled={isRunning}
                  className="text-xs px-2 py-1 bg-[#1a1a1a] text-gray-300 hover:text-white rounded border border-[#2a2a2a] disabled:opacity-50"
                >
                  {hasConfig ? 'Edit' : 'Configure'}
                </button>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Lane Filtering Toggle */}
      <div className="flex items-center justify-between p-3 bg-[#141414] rounded border border-[#2a2a2a]">
        <div className="flex items-center gap-2">
          <Settings className="w-4 h-4 text-gray-500" />
          <span className="text-sm text-gray-300">Lane Filtering</span>
        </div>
        <button
          onClick={() => setLaneFiltering(!laneFiltering)}
          disabled={isRunning}
          className={`relative w-10 h-5 rounded-full transition-colors ${laneFiltering ? 'bg-white' : 'bg-[#333]'
            } ${isRunning ? 'opacity-50 cursor-not-allowed' : ''}`}
        >
          <span className={`absolute top-0.5 w-4 h-4 rounded-full bg-black transition-transform ${laneFiltering ? 'left-5' : 'left-0.5'
            }`} />
        </button>
      </div>

      {/* Control Buttons */}
      <div className="flex gap-2">
        {!isRunning ? (
          <button
            onClick={handleStart}
            className="flex-1 flex items-center justify-center gap-2 py-2.5 bg-green-600 hover:bg-green-700 text-white font-medium rounded transition-colors"
          >
            <Play className="w-4 h-4" /> Start
          </button>
        ) : (
          <button
            onClick={handleStop}
            className="flex-1 flex items-center justify-center gap-2 py-2.5 bg-red-600 hover:bg-red-700 text-white font-medium rounded transition-colors"
          >
            <Square className="w-4 h-4" /> Stop
          </button>
        )}
        <button
          onClick={handleReset}
          disabled={!isRunning}
          className="px-4 py-2.5 bg-[#1a1a1a] text-gray-400 hover:text-white font-medium rounded border border-[#2a2a2a] transition-colors disabled:opacity-50"
        >
          Reset
        </button>
      </div>
    </div>
  );
}
