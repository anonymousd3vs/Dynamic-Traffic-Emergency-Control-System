/**
 * VideoFeed Component - Monochrome Theme
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

  const updateFrame = useCallback(() => {
    if (currentFrame && currentFrame !== lastFrameRef.current && imgRef.current) {
      try {
        lastFrameRef.current = currentFrame;
        imgRef.current.src = `data:image/jpeg;base64,${currentFrame}`;
      } catch (err) {
        console.error('Error updating frame:', err);
      }
    }
    pendingUpdateRef.current = false;
    rafRef.current = null;
  }, [currentFrame]);

  useEffect(() => {
    if (currentFrame && currentFrame !== lastFrameRef.current && !pendingUpdateRef.current) {
      pendingUpdateRef.current = true;
      if (rafRef.current) cancelAnimationFrame(rafRef.current);
      rafRef.current = requestAnimationFrame(updateFrame);
    }
    return () => { if (rafRef.current) cancelAnimationFrame(rafRef.current); };
  }, [currentFrame, updateFrame]);

  return (
    <div className="w-full h-full flex flex-col">
      {/* Video Display */}
      <div className="relative bg-[#0a0a0a] rounded-lg border border-[#2a2a2a] overflow-hidden flex-1 min-h-[300px]">
        {currentFrame ? (
          <img
            ref={imgRef}
            alt="Traffic feed"
            className="w-full h-full object-contain"
            loading="eager"
            decoding="async"
          />
        ) : (
          <div className="absolute inset-0 flex flex-col items-center justify-center text-gray-600">
            <VideoOff className="w-16 h-16 mb-4 opacity-30" />
            <p className="text-sm font-medium">
              {connected ? 'Waiting for video stream...' : 'Not connected'}
            </p>
          </div>
        )}

        {/* FPS Overlay */}
        {currentFrame && (
          <div className="absolute top-3 left-3 bg-[#0a0a0a]/90 px-3 py-1.5 rounded border border-[#333]">
            <span className="text-white text-xs font-mono font-medium">
              {metrics.fps.toFixed(1)} FPS
            </span>
          </div>
        )}

        {/* Frame Count Overlay */}
        {currentFrame && (
          <div className="absolute top-3 right-3 bg-[#0a0a0a]/90 px-3 py-1.5 rounded border border-[#333]">
            <span className="text-gray-400 text-xs font-mono">
              Frame: {metrics.frame_count}
            </span>
          </div>
        )}

        {/* Source Info */}
        {currentFrame && metrics.video_source !== 'unknown' && (
          <div className="absolute bottom-3 left-3 bg-[#0a0a0a]/90 px-3 py-1.5 rounded border border-[#333]">
            <span className="text-gray-400 text-xs">
              {metrics.video_source}
            </span>
          </div>
        )}

        {/* Mode Indicator */}
        {currentFrame && (
          <div className="absolute bottom-3 right-3 bg-[#0a0a0a]/90 px-3 py-1.5 rounded border border-[#333]">
            <span className={`text-xs font-medium uppercase ${metrics.mode === 'manual' ? 'text-white' : 'text-green-400'
              }`}>
              {metrics.mode === 'manual' ? 'Manual' : 'Auto'}
            </span>
          </div>
        )}

        {/* Connection Status */}
        <div className={`absolute top-3 left-1/2 transform -translate-x-1/2 flex items-center gap-1.5 px-3 py-1.5 rounded border ${connected ? 'bg-[#0a0a0a]/90 border-green-800 text-green-400' : 'bg-[#0a0a0a]/90 border-red-800 text-red-400'
          }`}>
          {connected ? <Wifi className="w-3 h-3" /> : <WifiOff className="w-3 h-3" />}
          <span className="text-xs font-medium">{connected ? 'Live' : 'Offline'}</span>
        </div>
      </div>

      {/* Frame Info */}
      {frameMetadata && Object.keys(frameMetadata).length > 0 && (
        <div className="mt-2 text-xs text-gray-600">
          Last update: <span className="text-gray-500 font-mono">{new Date(frameMetadata.timestamp).toLocaleTimeString()}</span>
        </div>
      )}
    </div>
  );
};

export default VideoFeed;
