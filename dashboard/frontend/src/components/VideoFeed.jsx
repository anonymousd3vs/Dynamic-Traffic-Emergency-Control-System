/**
 * VideoFeed Component
 * Displays the live video stream from the traffic detection system
 */

import React, { useEffect, useRef, useCallback } from 'react';
import { Video, VideoOff, Wifi, WifiOff } from 'lucide-react';
import useDashboardStore from '../stores/dashboardStore';

const VideoFeed = () => {
  const { currentFrame, frameMetadata, metrics, connected } = useDashboardStore();
  const imgRef = useRef(null);
  const lastFrameRef = useRef(null);
  const rafRef = useRef(null);
  const pendingUpdateRef = useRef(false);

  // ✅ FIXED: Prevent flickering by batching frame updates
  // Only update img src when frame actually changes, with debouncing
  const updateFrame = useCallback(() => {
    if (currentFrame && currentFrame !== lastFrameRef.current && imgRef.current) {
      try {
        // Store the current frame
        lastFrameRef.current = currentFrame;
        // Update image source
        imgRef.current.src = `data:image/jpeg;base64,${currentFrame}`;
      } catch (err) {
        console.error('Error updating frame:', err);
      }
    }
    pendingUpdateRef.current = false;
    rafRef.current = null;
  }, [currentFrame]);

  useEffect(() => {
    // Prevent multiple RAF calls for same frame (prevents flickering)
    if (currentFrame && currentFrame !== lastFrameRef.current && !pendingUpdateRef.current) {
      pendingUpdateRef.current = true;
      
      // Cancel previous animation frame if still pending
      if (rafRef.current) {
        cancelAnimationFrame(rafRef.current);
      }
      
      // Schedule update on next browser refresh
      rafRef.current = requestAnimationFrame(updateFrame);
    }

    return () => {
      if (rafRef.current) {
        cancelAnimationFrame(rafRef.current);
      }
    };
  }, [currentFrame, updateFrame]);

  return (
    <div className="w-full">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-3">
          {connected ? (
            <Video className="w-6 h-6 text-pastel-green" />
          ) : (
            <VideoOff className="w-6 h-6 text-pastel-rose" />
          )}
          <h2 className="text-lg font-bold text-slate-50">Live Feed</h2>
        </div>
        
        <div className={`flex items-center gap-2 px-4 py-2 rounded-lg font-medium transition-all ${
          connected
            ? 'bg-slate-700 border border-green-500 text-pastel-green'
            : 'bg-slate-700 border border-red-500 text-pastel-rose'
        }`}>
          {connected ? (
            <>
              <Wifi className="w-5 h-5" />
              <span>Connected</span>
            </>
          ) : (
            <>
              <WifiOff className="w-5 h-5" />
              <span>Disconnected</span>
            </>
          )}
        </div>
      </div>

      {/* Video Display */}
      <div className="relative bg-slate-950 rounded-xl shadow-lg border border-slate-700 overflow-hidden aspect-video">
        {currentFrame ? (
          <img
            ref={imgRef}
            alt="Traffic feed"
            className="w-full h-full object-contain will-change-transform"
            loading="eager"
            decoding="async"
          />
        ) : (
          <div className="absolute inset-0 flex flex-col items-center justify-center text-slate-500">
            <VideoOff className="w-20 h-20 mb-4 opacity-30" />
            <p className="text-lg font-semibold">
              {connected ? 'Waiting for video stream...' : 'Not connected'}
            </p>
          </div>
        )}

        {/* FPS Overlay */}
        {currentFrame && (
          <div className="absolute top-4 left-4 bg-slate-800/90 backdrop-blur px-4 py-2 rounded-lg pointer-events-none border border-pastel-blue/50 shadow-glow-blue">
            <span className="text-pastel-blue text-sm font-mono font-bold">
              ⚡ {metrics.fps.toFixed(1)} FPS
            </span>
          </div>
        )}

        {/* Frame Count Overlay */}
        {currentFrame && (
          <div className="absolute top-4 right-4 bg-slate-800/90 backdrop-blur px-4 py-2 rounded-lg pointer-events-none border border-pastel-purple/50 shadow-glow-purple">
            <span className="text-pastel-purple text-sm font-mono font-bold">
              🎬 Frame: {metrics.frame_count}
            </span>
          </div>
        )}

        {/* Source Info */}
        {currentFrame && metrics.video_source !== 'unknown' && (
          <div className="absolute bottom-4 left-4 bg-slate-800/90 backdrop-blur px-4 py-2 rounded-lg pointer-events-none border border-slate-600 shadow-md">
            <span className="text-slate-300 text-sm font-semibold">
              📹 {metrics.video_source}
            </span>
          </div>
        )}

        {/* Mode Indicator */}
        {currentFrame && (
          <div className={`absolute bottom-4 right-4 bg-slate-800/90 backdrop-blur px-4 py-2 rounded-lg pointer-events-none border shadow-md ${
            metrics.mode === 'manual' ? 'border-pastel-blue/50' : 'border-green-500/50'
          }`}>
            <span className={`text-sm font-bold uppercase ${
              metrics.mode === 'manual' ? 'text-pastel-blue' : 'text-pastel-green'
            }`}>
              {metrics.mode === 'manual' ? '📍 Manual' : '🎥 Auto'} Mode
            </span>
          </div>
        )}
      </div>

      {/* Frame Info */}
      {frameMetadata && Object.keys(frameMetadata).length > 0 && (
        <div className="mt-3 text-xs text-slate-500 flex items-center justify-between">
          <span>Last update: <span className="text-slate-400 font-mono">{new Date(frameMetadata.timestamp).toLocaleTimeString()}</span></span>
        </div>
      )}
    </div>
  );
};

export default VideoFeed;


