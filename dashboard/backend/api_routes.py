"""
REST API Routes for Dashboard Backend
Provides HTTP endpoints for system status, configuration, and historical data.
"""

from aiohttp import web
import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class DashboardAPI:
    """
    REST API handler for dashboard backend.

    Provides endpoints for:
    - System status
    - Configuration management
    - Historical metrics
    - Health checks
    """

    def __init__(self, streamer=None, stream_manager=None):
        """
        Initialize the API handler.

        Args:
            streamer: DashboardStreamer instance
            stream_manager: StreamManager instance
        """
        self.streamer = streamer
        self.stream_manager = stream_manager

        # Store recent metrics history (last 1000 data points)
        self.metrics_history = []
        self.max_history = 1000

        logger.info("DashboardAPI initialized")

    def setup_routes(self, app: web.Application):
        """
        Setup API routes on the aiohttp application.

        Args:
            app: aiohttp web application
        """
        app.router.add_get('/api/health', self.health_check)
        app.router.add_get('/api/status', self.get_status)
        app.router.add_get('/api/metrics/current', self.get_current_metrics)
        app.router.add_get('/api/metrics/history', self.get_metrics_history)
        app.router.add_get('/api/stream/stats', self.get_stream_stats)
        app.router.add_post('/api/stream/settings',
                            self.update_stream_settings)
        app.router.add_get('/api/config', self.get_config)

        logger.info("API routes configured")

    async def health_check(self, request: web.Request) -> web.Response:
        """
        Health check endpoint.

        Returns:
            JSON response with health status
        """
        return web.json_response({
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'service': 'Traffic Control Dashboard API'
        })

    async def get_status(self, request: web.Request) -> web.Response:
        """
        Get overall system status.

        Returns:
            JSON response with system status
        """
        status = {
            'timestamp': datetime.now().isoformat(),
            'websocket': {},
            'stream': {}
        }

        # WebSocket server status
        if self.streamer:
            status['websocket'] = self.streamer.get_server_status()

        # Stream manager status
        if self.stream_manager:
            status['stream'] = self.stream_manager.get_stats()

        return web.json_response(status)

    async def get_current_metrics(self, request: web.Request) -> web.Response:
        """
        Get current detection metrics.

        Returns:
            JSON response with current metrics
        """
        if not self.metrics_history:
            return web.json_response({
                'error': 'No metrics available yet',
                'timestamp': datetime.now().isoformat()
            }, status=404)

        # Return the most recent metrics
        current = self.metrics_history[-1]
        return web.json_response(current)

    async def get_metrics_history(self, request: web.Request) -> web.Response:
        """
        Get historical metrics data.

        Query parameters:
            limit: Number of recent data points to return (default: 100)

        Returns:
            JSON response with historical metrics
        """
        try:
            limit = int(request.query.get('limit', 100))
            limit = min(limit, self.max_history)  # Cap at max history
        except ValueError:
            limit = 100

        # Return the last N metrics
        history = self.metrics_history[-limit:] if self.metrics_history else []

        return web.json_response({
            'count': len(history),
            'data': history,
            'timestamp': datetime.now().isoformat()
        })

    async def get_stream_stats(self, request: web.Request) -> web.Response:
        """
        Get stream statistics.

        Returns:
            JSON response with stream stats
        """
        if not self.stream_manager:
            return web.json_response({
                'error': 'Stream manager not available'
            }, status=503)

        stats = self.stream_manager.get_stats()
        return web.json_response(stats)

    async def update_stream_settings(self, request: web.Request) -> web.Response:
        """
        Update stream settings.

        Request body:
            {
                "target_fps": int,
                "jpeg_quality": int,
                "max_width": int
            }

        Returns:
            JSON response with updated settings
        """
        if not self.stream_manager:
            return web.json_response({
                'error': 'Stream manager not available'
            }, status=503)

        try:
            data = await request.json()

            # Update settings
            self.stream_manager.update_settings(
                target_fps=data.get('target_fps'),
                jpeg_quality=data.get('jpeg_quality'),
                max_width=data.get('max_width')
            )

            return web.json_response({
                'success': True,
                'message': 'Settings updated',
                'settings': {
                    'target_fps': self.stream_manager.target_fps,
                    'jpeg_quality': self.stream_manager.jpeg_quality,
                    'max_width': self.stream_manager.max_width
                }
            })

        except json.JSONDecodeError:
            return web.json_response({
                'error': 'Invalid JSON in request body'
            }, status=400)
        except Exception as e:
            logger.error(f"Error updating stream settings: {e}")
            return web.json_response({
                'error': str(e)
            }, status=500)

    async def get_config(self, request: web.Request) -> web.Response:
        """
        Get current dashboard configuration.

        Returns:
            JSON response with configuration
        """
        config = {
            'websocket': {
                'host': self.streamer.host if self.streamer else 'unknown',
                'port': self.streamer.port if self.streamer else 0
            },
            'stream': {
                'target_fps': self.stream_manager.target_fps if self.stream_manager else 0,
                'jpeg_quality': self.stream_manager.jpeg_quality if self.stream_manager else 0,
                'max_width': self.stream_manager.max_width if self.stream_manager else 0
            } if self.stream_manager else {}
        }

        return web.json_response(config)

    def add_metrics(self, metrics: Dict[str, Any]):
        """
        Add metrics to history.

        Args:
            metrics: Metrics dictionary to store
        """
        # Add timestamp if not present
        if 'timestamp' not in metrics:
            metrics['timestamp'] = datetime.now().isoformat()

        # Add to history
        self.metrics_history.append(metrics)

        # Trim history if too large
        if len(self.metrics_history) > self.max_history:
            self.metrics_history = self.metrics_history[-self.max_history:]

    def clear_history(self):
        """Clear metrics history."""
        self.metrics_history.clear()
        logger.info("Metrics history cleared")


# CORS middleware for development
@web.middleware
async def cors_middleware(request, handler):
    """
    CORS middleware to allow cross-origin requests.
    For production, configure specific origins instead of '*'.
    """
    if request.method == 'OPTIONS':
        response = web.Response()
    else:
        response = await handler(request)

    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'

    return response


# Example usage
async def create_app():
    """Create and configure the web application."""
    from dashboard.backend.websocket_server import DashboardStreamer
    from dashboard.backend.stream_manager import StreamManager

    # Initialize components
    streamer = DashboardStreamer()
    stream_manager = StreamManager()
    api = DashboardAPI(streamer, stream_manager)

    # Setup app
    app = web.Application(middlewares=[cors_middleware])
    api.setup_routes(app)

    return app, streamer, stream_manager, api


if __name__ == '__main__':
    import asyncio

    logging.basicConfig(level=logging.INFO)

    async def main():
        app, streamer, stream_manager, api = await create_app()

        print("\n" + "="*60)
        print("🚀 Dashboard API Server")
        print("="*60)
        print("📡 API Endpoints:")
        print("  GET  /api/health")
        print("  GET  /api/status")
        print("  GET  /api/metrics/current")
        print("  GET  /api/metrics/history?limit=100")
        print("  GET  /api/stream/stats")
        print("  POST /api/stream/settings")
        print("  GET  /api/config")
        print("="*60 + "\n")

        # Start server
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, 'localhost', 8080)
        await site.start()

        print(f"✅ Server running at http://localhost:8080")
        print("Press Ctrl+C to stop\n")

        try:
            await asyncio.Event().wait()
        except KeyboardInterrupt:
            print("\n🛑 Shutting down...")
            await runner.cleanup()

    asyncio.run(main())
