"""
Detection Runner for Dashboard Integration
Runs traffic detection and streams frames to connected clients via WebSocket.
"""

from core.detectors.traffic_detector import ONNXTrafficDetector
import os
import sys
import logging
import cv2
import base64
import asyncio
import threading
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Import detection system

logger = logging.getLogger(__name__)


# Custom exception hook for threads to log uncaught exceptions
def thread_exception_hook(args):
    """Log uncaught exceptions in threads"""
    logger.error(
        f"🔴 UNCAUGHT THREAD EXCEPTION: {args.exc_type.__name__}: {args.exc_value}")
    import traceback
    logger.error(f"Thread: {args.thread}")
    logger.error(
        f"Full traceback:\n{''.join(traceback.format_exception(args.exc_type, args.exc_value, args.exc_traceback))}")


# Install the custom exception hook
threading.excepthook = thread_exception_hook


class DetectionStreamingRunner:
    """
    Runs traffic detection and streams frames to dashboard via WebSocket.

    Features:
    - In-process detection (no subprocess overhead)
    - Real-time frame streaming to connected clients
    - Metrics broadcasting
    - Safe cleanup and shutdown
    """

    def __init__(self, streamer, stream_manager, event_loop=None):
        """
        Initialize the detection streaming runner.

        Args:
            streamer: DashboardStreamer instance (for WebSocket broadcast)
            stream_manager: StreamManager instance (for frame encoding)
            event_loop: Optional asyncio event loop (will be auto-detected if not provided)
        """
        self.streamer = streamer
        self.stream_manager = stream_manager
        self.detector = None
        self.is_running = False
        self.detection_thread = None
        self.event_loop = event_loop  # Store event loop reference

        # Store reference to socket.io server for event loop access
        if streamer and hasattr(streamer, 'sio'):
            self.sio = streamer.sio
        else:
            self.sio = None

        logger.info("DetectionStreamingRunner initialized")

    def start(
        self,
        source: str = '0',
        lane_filtering: bool = True,
        config_path: Optional[str] = None
    ):
        """
        Start the detection system and frame streaming.

        Args:
            source: Video source (file path, 0 for webcam, or stream URL)
            lane_filtering: Whether to use lane-based filtering
            config_path: Path to lane configuration file
        """
        if self.is_running:
            logger.warning("Detection already running")
            return

        try:
            logger.info(
                f"Starting detection: source={source}, lane_filtering={lane_filtering}")

            # Start detection in background thread
            self.is_running = True
            self.detection_thread = threading.Thread(
                target=self._run_detection_loop,
                args=(source, lane_filtering, config_path),
                daemon=False
            )
            self.detection_thread.start()

            logger.info("Detection streaming runner started")

        except Exception as e:
            logger.error(f"Failed to start detection: {e}", exc_info=True)
            self.is_running = False
            raise

    def stop(self):
        """Stop the detection system and cleanup resources."""
        logger.info("Stopping detection streaming runner...")

        self.is_running = False

        # Stop detector
        if self.detector:
            try:
                self.detector.stop()
            except Exception as e:
                logger.error(f"Error stopping detector: {e}")

        # Wait for thread to finish
        if self.detection_thread and self.detection_thread.is_alive():
            self.detection_thread.join(timeout=5)

        logger.info("Detection streaming runner stopped")

    def reset_counters(self):
        """Reset detection counters."""
        if self.detector:
            self.detector.reset_counters()
            logger.info("Detection counters reset")

    def _run_detection_loop(
        self,
        source: str,
        lane_filtering: bool,
        config_path: Optional[str]
    ):
        """
        Main detection loop running in background thread.

        Args:
            source: Video source
            lane_filtering: Whether to use lane filtering
            config_path: Path to lane config
        """
        logger.info("=== STARTING DETECTION LOOP ===")
        try:
            # Initialize detector
            logger.info("Initializing detector...")

            # Prepare detector initialization parameters
            detector_kwargs = {}
            if lane_filtering and config_path:
                logger.info(f"Loading lane config: {config_path}")
                detector_kwargs['lane_config_path'] = config_path
            elif not lane_filtering:
                logger.info("Lane filtering disabled")
                detector_kwargs['lane_config_path'] = None

            # Create detector with appropriate configuration
            logger.info(f"Creating detector with kwargs: {detector_kwargs}")
            self.detector = ONNXTrafficDetector(**detector_kwargs)
            logger.info("✅ Detector created successfully")

            # Set environment variable for headless mode
            os.environ['DASHBOARD_MODE'] = '1'

            # Open video source
            logger.info(f"Opening video source: {source}")
            cap = cv2.VideoCapture(int(source) if source.isdigit() else source)

            if not cap.isOpened():
                logger.error(f"Failed to open video source: {source}")
                return

            # Get video properties
            fps = cap.get(cv2.CAP_PROP_FPS) or 30
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

            logger.info(f"Video properties: {width}x{height} @ {fps} FPS")

            frame_count = 0
            # ✅ OPTIMIZED: Increase FPS for smoother video (20-25 FPS for smooth playback)
            # Higher FPS = smoother video, but more bandwidth
            # Tradeoff: 25 FPS is smooth enough for most users
            frame_broadcast_interval = max(
                1, int(fps / 25))  # Broadcast at ~25 FPS

            # ✅ CRITICAL: Metrics at 5-10 FPS to detect ambulance state changes rapidly
            # When ambulance leaves frame, we want alert off within 200ms not 1 second
            # Metrics every ~10 FPS (100ms at 30fps)
            metric_interval = max(1, int(fps / 10))

            # Detection loop
            logger.info("Starting detection loop...")
            while self.is_running:
                try:
                    ret, frame = cap.read()

                    if not ret:
                        logger.info("End of video or read error")
                        break
                except Exception as e:
                    logger.error(
                        f"❌ Error reading frame from video: {e}", exc_info=True)
                    break

                try:
                    # Run detection on frame with super detailed logging
                    sys.stdout.write(
                        f"[FRAME_PROCESS] Starting frame {frame_count} processing\n")
                    sys.stdout.flush()
                    logger.debug(f"Processing frame {frame_count}...")

                    sys.stdout.write(
                        f"[FRAME_PROCESS] Calling detector.process_frame()\n")
                    sys.stdout.flush()
                    output_frame = self.detector.process_frame(frame)

                    sys.stdout.write(
                        f"[FRAME_PROCESS] process_frame() returned successfully\n")
                    sys.stdout.flush()
                    logger.debug(f"Frame {frame_count} processed successfully")

                    # If process_frame returns None, skip this frame
                    if output_frame is None:
                        logger.debug(
                            f"Frame {frame_count} returned None, skipping")
                        continue

                    frame_count += 1

                    # Get detection results from detector attributes
                    logger.debug(
                        f"Getting detector attributes for frame {frame_count}")
                    vehicle_count = getattr(self.detector, 'vehicle_count', 0)
                    tracked_objects = getattr(self.detector, 'tracker', {})
                    if hasattr(tracked_objects, 'objects'):
                        detected_count = len(tracked_objects.objects)
                    else:
                        detected_count = 0
                    logger.debug(
                        f"Detected {vehicle_count} vehicles, {detected_count} tracked objects")

                    # Broadcast frame at interval (not every frame to reduce bandwidth)
                    if frame_count % frame_broadcast_interval == 0:
                        # Encode frame to base64 JPEG
                        frame_base64 = self._encode_frame(output_frame)

                        # Prepare metadata
                        metadata = {
                            'frame_count': frame_count,
                            'fps': getattr(self.detector, 'fps', 0),
                            'timestamp': datetime.now().isoformat(),
                            'vehicle_count': vehicle_count
                        }

                        # Broadcast to WebSocket (with error handling)
                        try:
                            loop = self._get_event_loop()
                            if loop and loop.is_running():
                                asyncio.run_coroutine_threadsafe(
                                    self.streamer.broadcast_frame(
                                        frame_base64, metadata),
                                    loop
                                )
                            else:
                                logger.debug(
                                    "Event loop not running for frame broadcast")
                        except Exception as be:
                            logger.debug(f"Frame broadcast error: {be}")

                    # Broadcast metrics periodically
                    if frame_count % metric_interval == 0:
                        try:
                            loop = self._get_event_loop()
                            if loop and loop.is_running():
                                asyncio.run_coroutine_threadsafe(
                                    self._broadcast_metrics(),
                                    loop
                                )
                            else:
                                logger.info(
                                    f"⚠️ Event loop issue: loop={loop}, running={loop.is_running() if loop else 'N/A'}")
                        except Exception as me:
                            logger.error(
                                f"❌ Metrics broadcast error: {me}", exc_info=True)

                except Exception as e:
                    sys.stdout.write(
                        f"[FRAME_PROCESS_ERROR] Exception during frame processing: {type(e).__name__}: {e}\n")
                    sys.stdout.flush()
                    sys.stderr.write(
                        f"[FRAME_PROCESS_ERROR] Exception during frame processing: {type(e).__name__}: {e}\n")
                    sys.stderr.flush()
                    logger.error(
                        f"❌ CRITICAL: Error processing frame {frame_count}: {e}", exc_info=True)
                    import traceback
                    logger.error(f"Stack trace:\n{traceback.format_exc()}")
                    logger.error(
                        "Stopping detection due to frame processing error")
                    # Don't continue on critical errors - stop detection
                    break

            # Cleanup
            cap.release()
            logger.info(
                f"Detection loop ended. Processed {frame_count} frames.")

        except Exception as e:
            logger.error(f"🔴 DETECTION LOOP EXCEPTION: {e}", exc_info=True)
            import traceback
            logger.error(f"Full traceback:\n{traceback.format_exc()}")
        except BaseException as be:
            logger.error(
                f"🔴 CRITICAL DETECTION LOOP ERROR (BaseException): {be}", exc_info=True)
            import traceback
            logger.error(f"Full traceback:\n{traceback.format_exc()}")
        finally:
            logger.info("=== DETECTION LOOP ENDING ===")
            self.is_running = False
            if self.detector:
                try:
                    # Cleanup detector resources if method exists
                    if hasattr(self.detector, 'stop'):
                        self.detector.stop()
                except Exception as cleanup_error:
                    logger.warning(
                        f"Error during detector cleanup: {cleanup_error}")

    def _encode_frame(self, frame) -> str:
        """
        Encode frame to base64 JPEG with optimized compression.

        Args:
            frame: OpenCV frame

        Returns:
            Base64 encoded JPEG string
        """
        try:
            # Resize if needed to reduce bandwidth
            if frame.shape[1] > 1280:
                ratio = 1280 / frame.shape[1]
                height = int(frame.shape[0] * ratio)
                frame = cv2.resize(frame, (1280, height),
                                   interpolation=cv2.INTER_LINEAR)

            # ✅ OPTIMIZED: JPEG quality 75 for better speed (still maintains good quality)
            ret, buffer = cv2.imencode(
                '.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 75])

            if not ret:
                logger.error("Failed to encode frame")
                return ""

            # Convert to base64 string
            frame_bytes = buffer.tobytes()
            frame_base64 = base64.b64encode(frame_bytes).decode('utf-8')

            return frame_base64

        except Exception as e:
            logger.error(f"Error encoding frame: {e}")
            return ""

    async def _broadcast_metrics(self):
        """Broadcast detection metrics to connected clients."""
        if not self.detector:
            return

        try:
            # Get metrics from detector
            active_vehicles = 0
            if hasattr(self.detector, 'tracker') and self.detector.tracker:
                if hasattr(self.detector.tracker, 'objects'):
                    active_vehicles = len(self.detector.tracker.objects)

            mode = 'zone_counting' if getattr(
                self.detector, 'lane_enabled', False) else 'line_crossing'

            metrics = {
                'fps': getattr(self.detector, 'fps', 0),
                'frame_count': getattr(self.detector, 'frame_count', 0),
                'vehicle_count': getattr(self.detector, 'vehicle_count', 0),
                'active_vehicles': active_vehicles,
                'ambulance_detected': getattr(self.detector, 'ambulance_detected', False),
                'ambulance_stable': getattr(self.detector, 'ambulance_stable', False),
                'ambulance_confidence': getattr(self.detector, 'ambulance_confidence', 0.0),
                'mode': mode,
                'video_source': getattr(self.detector, 'video_source', 'detection')
            }

            await self.streamer.broadcast_metrics(metrics)

        except Exception as e:
            logger.error(f"Error broadcasting metrics: {e}")

    def _get_event_loop(self):
        """Get the WebSocket server's event loop."""
        try:
            # Try to get all running tasks to find the event loop
            try:
                running_loops = asyncio.all_tasks()
                if running_loops:
                    task = next(iter(running_loops))
                    loop = task.get_loop()
                    if loop and loop.is_running():
                        logger.debug(
                            f"✅ Found running loop via asyncio.all_tasks()")
                        return loop
            except Exception as e:
                logger.debug(f"Could not access running tasks: {e}")

            # Method 1: Try to get loop from aiohttp app (new approach)
            if self.streamer and hasattr(self.streamer, 'app'):
                try:
                    app = self.streamer.app
                    # Try to get the loop from the app's internal state
                    if hasattr(app, '_loop'):
                        loop = app._loop
                        if loop and loop.is_running():
                            logger.debug(f"✅ Found running loop via app._loop")
                            return loop
                except Exception as e:
                    logger.debug(f"Could not access app._loop: {e}")

            # Method 2: Try to access through sio app context
            if self.sio and hasattr(self.sio, 'app'):
                try:
                    app = self.sio.app
                    if hasattr(app, '_loop') and app._loop:
                        loop = app._loop
                        if loop and loop.is_running():
                            logger.debug(
                                f"✅ Found running loop via sio.app._loop")
                            return loop
                except Exception as e:
                    logger.debug(f"Could not access sio.app._loop: {e}")

        except Exception as e:
            logger.error(f"Error in _get_event_loop: {e}")

        logger.warning(f"⚠️ Could not find running event loop")
        return None
