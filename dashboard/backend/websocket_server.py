"""
WebSocket Server for Real-time Dashboard Updates
Handles client connections and broadcasts detection data to connected clients.
"""

import asyncio
import json
import logging
from typing import Set, Dict, Any
from datetime import datetime
import socketio
from aiohttp import web

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DashboardStreamer:
    """
    Manages WebSocket connections and broadcasts real-time traffic data.

    Features:
    - Client connection management
    - Real-time data broadcasting
    - Frame streaming (base64 encoded)
    - Automatic reconnection handling
    """

    def __init__(self, host: str = 'localhost', port: int = 8765):
        """
        Initialize the dashboard streamer.

        Args:
            host: Server host address
            port: Server port number
        """
        self.host = host
        self.port = port
        self.dynamic_timing = None  # Will be set by unified_server

        # Socket.IO server setup with increased timeouts
        self.sio = socketio.AsyncServer(
            async_mode='aiohttp',
            cors_allowed_origins='*',  # Allow all origins for development
            logger=True,
            engineio_logger=True,
            ping_timeout=120,  # 2 minutes before considering client dead
            ping_interval=30,  # Send ping every 30 seconds
            max_http_buffer_size=10000000,  # 10MB for large frames
            allow_upgrades=True,
            compression=True
        )

        # AIOHTTP web application
        self.app = web.Application()
        self.sio.attach(self.app)

        # Connected clients tracking
        self.clients: Set[str] = set()

        # Statistics
        self.stats = {
            'total_connections': 0,
            'total_messages_sent': 0,
            'start_time': datetime.now()
        }

        # Setup event handlers
        self._setup_handlers()

        logger.info(f"DashboardStreamer initialized on {host}:{port}")

    def _setup_handlers(self):
        """Setup Socket.IO event handlers."""

        @self.sio.event
        async def connect(sid, environ):
            """Handle client connection."""
            self.clients.add(sid)
            self.stats['total_connections'] += 1
            logger.info(
                f"Client connected: {sid} (Total: {len(self.clients)})")

            # Send initial connection confirmation
            await self.sio.emit('connection_established', {
                'sid': sid,
                'timestamp': datetime.now().isoformat(),
                'message': 'Connected to Traffic Control Dashboard'
            }, room=sid)

        @self.sio.event
        async def disconnect(sid):
            """Handle client disconnection."""
            if sid in self.clients:
                self.clients.remove(sid)
            logger.info(
                f"Client disconnected: {sid} (Remaining: {len(self.clients)})")

        @self.sio.event
        async def ping(sid, data):
            """Handle ping from client."""
            logger.debug(f"Ping received from {sid}")
            await self.sio.emit('pong', {'timestamp': datetime.now().isoformat()}, room=sid)

        @self.sio.event
        async def request_status(sid, data):
            """Handle status request from client."""
            status = self.get_server_status()
            await self.sio.emit('server_status', status, room=sid)

        @self.sio.event
        async def error(sid, data):
            """Handle client errors."""
            logger.error(f"Client {sid} error: {data}")

        # Handle connection errors
        @self.sio.on('connect_error')
        async def connect_error(sid, data):
            logger.error(f"Connection error for {sid}: {data}")

        # Handle general errors
        @self.sio.on('*')
        async def catch_all(event, sid, data):
            logger.debug(f"Unhandled event '{event}' from {sid}: {data}")

    async def broadcast_metrics(self, data: Dict[str, Any]):
        """
        Broadcast system metrics to all connected clients.

        Args:
            data: Dictionary containing metrics (fps, vehicle_count, etc.)
        """
        if not self.clients:
            return

        message = {
            'type': 'metrics',
            'timestamp': datetime.now().isoformat(),
            'data': data
        }

        try:
            # ✅ FIXED: Changed from 'metrics_update' to 'metrics'
            await self.sio.emit('metrics', message)
            self.stats['total_messages_sent'] += 1
        except Exception as e:
            logger.error(f"Error broadcasting metrics: {e}")

    async def broadcast_frame(self, frame_data: str, metadata: Dict[str, Any] = None):
        """
        Broadcast video frame to all connected clients.

        Args:
            frame_data: Base64 encoded JPEG frame
            metadata: Optional frame metadata (fps, frame_count, etc.)
        """
        if not self.clients:
            return

        message = {
            'type': 'frame',
            'timestamp': datetime.now().isoformat(),
            'frame': frame_data,
            'metadata': metadata or {}
        }

        try:
            # ✅ FIXED: Changed from 'frame_update' to 'frame'
            await self.sio.emit('frame', message)
            self.stats['total_messages_sent'] += 1
        except Exception as e:
            logger.error(f"Error broadcasting frame: {e}")

    async def broadcast_alert(self, alert_type: str, data: Dict[str, Any]):
        """
        Broadcast alert to all connected clients.

        Args:
            alert_type: Type of alert (e.g., 'ambulance_detected')
            data: Alert data
        """
        if not self.clients:
            return

        message = {
            'type': 'alert',
            'alert_type': alert_type,
            'timestamp': datetime.now().isoformat(),
            'data': data
        }

        try:
            await self.sio.emit('alert', message)
            self.stats['total_messages_sent'] += 1
            logger.info(f"Alert broadcasted: {alert_type}")
        except Exception as e:
            logger.error(f"Error broadcasting alert: {e}")

    def update_from_detector(self, detector, signal_controller=None):
        """
        Update dashboard with data from traffic detector (synchronous wrapper).
        This method can be called from the main detection thread.

        Args:
            detector: ONNXTrafficDetector instance
            signal_controller: Optional MultiDynamicSignalController for dynamic timing
        """
        # Calculate active vehicles from tracker objects
        active_vehicles = 0
        if hasattr(detector, 'tracker') and detector.tracker:
            if hasattr(detector.tracker, 'objects'):
                active_vehicles = len(detector.tracker.objects)

        # Determine mode based on detection configuration
        mode = 'unknown'
        if hasattr(detector, 'lane_enabled') and detector.lane_enabled:
            mode = 'zone_counting'
        else:
            mode = 'line_crossing'

        # Get vehicle count and current zone
        vehicle_count = getattr(detector, 'vehicle_count', 0)
        current_zone = getattr(detector, 'current_zone', None)

        data = {
            'fps': getattr(detector, 'fps', 0),
            'frame_count': getattr(detector, 'frame_count', 0),
            # ✅ FIXED: Use vehicle_count, not tracker.total_count
            'vehicle_count': vehicle_count,
            'active_vehicles': active_vehicles,  # ✅ FIXED: Proper count from tracker.objects
            'ambulance_detected': getattr(detector, 'ambulance_detected', False),
            'ambulance_stable': getattr(detector, 'ambulance_stable', False),
            'ambulance_confidence': getattr(detector, 'ambulance_confidence', 0.0),
            'mode': mode,
            'video_source': getattr(detector, 'video_source', 'unknown')
        }

        # 🔧 NEW: Update dynamic timing with vehicle count if available
        if self.dynamic_timing and self.dynamic_timing.selected_lane:
            try:
                result = self.dynamic_timing.update_vehicle_count(
                    vehicle_count)
                if result['status'] == 'success':
                    # Add timing info to data for frontend
                    data['timing_update'] = result['timing']
            except Exception as e:
                logger.debug(f"Could not update dynamic timing: {e}")

        # Schedule the coroutine in the event loop
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                asyncio.create_task(self.broadcast_metrics(data))
            else:
                loop.run_until_complete(self.broadcast_metrics(data))
        except RuntimeError:
            # No event loop, skip this update
            logger.warning("No event loop available for dashboard update")

    def get_server_status(self) -> Dict[str, Any]:
        """Get server status and statistics."""
        uptime = (datetime.now() - self.stats['start_time']).total_seconds()

        return {
            'connected_clients': len(self.clients),
            'total_connections': self.stats['total_connections'],
            'total_messages_sent': self.stats['total_messages_sent'],
            'uptime_seconds': uptime,
            'timestamp': datetime.now().isoformat()
        }

    async def start(self):
        """Start the WebSocket server."""
        runner = web.AppRunner(self.app)
        await runner.setup()
        site = web.TCPSite(runner, self.host, self.port)
        await site.start()
        logger.info(
            f"Dashboard server started at http://{self.host}:{self.port}")

    async def stop(self):
        """Stop the WebSocket server."""
        # Disconnect all connected clients
        for sid in list(self.clients):
            try:
                await self.sio.disconnect(sid)
            except Exception as e:
                logger.warning(f"Error disconnecting client {sid}: {e}")
        logger.info("Dashboard server stopped")


# Standalone server for testing
async def main():
    """Run standalone WebSocket server for testing."""
    streamer = DashboardStreamer(host='0.0.0.0', port=8765)
    await streamer.start()

    print("\n" + "="*60)
    print("🚀 Dashboard WebSocket Server Running")
    print("="*60)
    print(f"📡 Server: http://localhost:8765")
    print(f"👥 Connected clients: 0")
    print("Press Ctrl+C to stop")
    print("="*60 + "\n")

    try:
        # Keep server running
        while True:
            await asyncio.sleep(1)

            # Broadcast test data every 5 seconds
            if int(asyncio.get_event_loop().time()) % 5 == 0:
                test_data = {
                    'fps': 5.2,
                    'frame_count': 1234,
                    'vehicle_count': 45,
                    'active_vehicles': 8,
                    'ambulance_detected': False
                }
                await streamer.broadcast_metrics(test_data)
    except KeyboardInterrupt:
        print("\n\n🛑 Shutting down server...")
        await streamer.stop()


if __name__ == '__main__':
    asyncio.run(main())
