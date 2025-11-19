"""
Dashboard Backend Package
Real-time traffic monitoring dashboard backend with WebSocket streaming and REST API.
"""

from .websocket_server import DashboardStreamer
from .stream_manager import StreamManager
from .api_routes import DashboardAPI, cors_middleware
from .detection_runner import DetectionStreamingRunner
import sys
from pathlib import Path

# Ensure project root is in path BEFORE any relative imports
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# NOW do the relative imports


__all__ = [
    'DashboardStreamer',
    'StreamManager',
    'DashboardAPI',
    'cors_middleware',
    'DetectionStreamingRunner',
]

__version__ = '1.0.0'
