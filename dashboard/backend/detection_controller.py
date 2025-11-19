"""
Detection System Controller for Dashboard
Manages detection system lifecycle and configuration
"""

import os
import sys
import subprocess
import logging
import json
import asyncio
from pathlib import Path
from typing import Optional, Dict, Any
from aiohttp import web

# Configure logger early
logger = logging.getLogger(__name__)

# Add project root to path
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Import video config manager functions
try:
    from shared.config.video_config_manager import (
        has_video_config,
        get_video_config_path,
        list_configured_videos
    )
except ImportError:
    # Fallback if module structure is different
    has_video_config = lambda *args: False
    get_video_config_path = lambda *args: None
    list_configured_videos = lambda *args: []

# Import the detection streaming runner
try:
    from dashboard.backend.detection_runner import DetectionStreamingRunner
    IntegratedDetectionRunner = DetectionStreamingRunner
except ImportError:
    logger.warning(
        "DetectionStreamingRunner not available, will use subprocess mode")
    IntegratedDetectionRunner = None


class DetectionController:
    """
    Controller for managing the traffic detection system.

    Handles:
    - Starting/stopping detection
    - Video source management
    - Lane configuration
    - Detection settings
    """

    def __init__(self, streamer=None, stream_manager=None, event_loop=None):
        """
        Initialize the detection controller.

        Args:
            streamer: DashboardStreamer instance for WebSocket communication
            stream_manager: StreamManager instance for frame encoding
            event_loop: Optional asyncio event loop for background operations
        """
        self.streamer = streamer
        self.stream_manager = stream_manager
        self.event_loop = event_loop
        self.detection_runner = None
        self.detection_process = None
        self.is_running = False
        self.current_config = {}
        self.video_directory = Path(project_root) / "videos"
        self.config_directory = Path(project_root) / "config"

        # Initialize integrated detection runner if available
        if IntegratedDetectionRunner and streamer and stream_manager:
            self.detection_runner = IntegratedDetectionRunner(
                streamer, stream_manager, event_loop)
            logger.info(
                "DetectionController initialized with integrated runner")
        else:
            logger.info("DetectionController initialized (subprocess mode)")

    def setup_routes(self, app: web.Application):
        """Setup API routes."""
        app.router.add_get('/api/videos/list', self.list_videos)
        app.router.add_post('/api/videos/browse', self.browse_directory)
        app.router.add_get('/api/config/list', self.list_configured_videos)
        app.router.add_post('/api/config/check', self.check_config)
        app.router.add_post('/api/config/launch', self.launch_config_tool)
        app.router.add_get('/api/detection/status', self.get_detection_status)
        app.router.add_post('/api/detection/start', self.start_detection)
        app.router.add_post('/api/detection/stop', self.stop_detection)
        app.router.add_post('/api/detection/reset', self.reset_detection)

        logger.info("Detection controller routes configured")

    async def list_videos(self, request: web.Request) -> web.Response:
        """List available video files."""
        try:
            if not self.video_directory.exists():
                self.video_directory.mkdir(parents=True, exist_ok=True)

            videos = []
            for ext in ['*.mp4', '*.avi', '*.mov', '*.mkv']:
                videos.extend([
                    str(f.relative_to(project_root))
                    for f in self.video_directory.glob(ext)
                ])

            return web.json_response({
                'success': True,
                'videos': sorted(videos)
            })

        except Exception as e:
            logger.error(f"Error listing videos: {e}")
            return web.json_response({
                'success': False,
                'error': str(e)
            }, status=500)

    async def browse_directory(self, request: web.Request) -> web.Response:
        """Browse a directory for video files."""
        try:
            data = await request.json()
            directory = data.get('directory', '')

            if not directory:
                # Return common video directories
                common_dirs = [
                    str(self.video_directory),
                    str(Path.home() / 'Videos'),
                    str(Path.home() / 'Documents'),
                    str(Path.home() / 'Downloads'),
                ]
                return web.json_response({
                    'success': True,
                    'directories': [d for d in common_dirs if Path(d).exists()],
                    'files': []
                })

            dir_path = Path(directory)
            if not dir_path.exists() or not dir_path.is_dir():
                return web.json_response({
                    'success': False,
                    'error': 'Directory does not exist'
                }, status=400)

            # List subdirectories
            directories = [
                str(d) for d in dir_path.iterdir()
                if d.is_dir() and not d.name.startswith('.')
            ]

            # List video files
            video_files = []
            for ext in ['.mp4', '.avi', '.mov', '.mkv', '.MP4', '.AVI', '.MOV', '.MKV']:
                video_files.extend([
                    str(f) for f in dir_path.glob(f'*{ext}')
                ])

            return web.json_response({
                'success': True,
                'current_dir': str(dir_path),
                'parent_dir': str(dir_path.parent) if dir_path.parent != dir_path else None,
                'directories': sorted(directories),
                'files': sorted(video_files)
            })

        except Exception as e:
            logger.error(f"Error browsing directory: {e}")
            return web.json_response({
                'success': False,
                'error': str(e)
            }, status=500)

    async def list_configured_videos(self, request: web.Request) -> web.Response:
        """List all videos that have lane configurations."""
        try:
            configured_videos = []

            # Import the list function
            try:
                from shared.config.video_config_manager import list_configured_videos
            except ImportError:
                list_configured_videos = None

            if list_configured_videos:
                videos_dict = list_configured_videos(
                    str(self.config_directory))
                for video_name, config_path in videos_dict.items():
                    configured_videos.append({
                        'name': video_name,
                        'config_path': config_path,
                        'exists': os.path.exists(config_path)
                    })

            return web.json_response({
                'success': True,
                'configured_videos': configured_videos,
                'count': len(configured_videos)
            })

        except Exception as e:
            logger.error(f"Error listing configured videos: {e}")
            return web.json_response({
                'success': False,
                'error': str(e)
            }, status=500)

    async def check_config(self, request: web.Request) -> web.Response:
        """Check if a video has lane configuration."""
        try:
            data = await request.json()
            video_source = data.get('video_source')

            if not video_source:
                return web.json_response({
                    'success': False,
                    'error': 'video_source is required'
                }, status=400)

            # Check if configuration exists
            has_config = has_video_config(
                video_source,
                str(self.config_directory)
            )

            config_path = None
            if has_config:
                config_path = get_video_config_path(
                    video_source,
                    str(self.config_directory)
                )

            return web.json_response({
                'success': True,
                'has_config': has_config,
                'config_path': config_path
            })

        except Exception as e:
            logger.error(f"Error checking config: {e}", exc_info=True)
            return web.json_response({
                'success': False,
                'error': str(e)
            }, status=500)

    async def launch_config_tool(self, request: web.Request) -> web.Response:
        """Launch the lane configuration tool."""
        try:
            data = await request.json()
            video_source = data.get('video_source')

            if not video_source:
                return web.json_response({
                    'success': False,
                    'error': 'video_source is required'
                }, status=400)

            # Get python executable
            python_exe = sys.executable
            script_path = project_root / "shared" / "config" / "lane_config_tool.py"

            if not script_path.exists():
                script_path = project_root / "scripts" / "quick_lane_setup.py"

            if not script_path.exists():
                return web.json_response({
                    'success': False,
                    'error': 'Lane configuration tool not found'
                }, status=404)

            # Launch configuration tool in new process
            subprocess.Popen(
                [python_exe, str(script_path), '--video', video_source],
                cwd=str(project_root),
                creationflags=subprocess.CREATE_NEW_CONSOLE if sys.platform == 'win32' else 0
            )

            return web.json_response({
                'success': True,
                'message': 'Configuration tool launched. Please configure lanes and close the window when done.'
            })

        except Exception as e:
            logger.error(f"Error launching config tool: {e}")
            return web.json_response({
                'success': False,
                'error': str(e)
            }, status=500)

    async def get_detection_status(self, request: web.Request) -> web.Response:
        """Get current detection system status."""
        return web.json_response({
            'success': True,
            'is_running': self.is_running,
            'config': self.current_config
        })

    async def start_detection(self, request: web.Request) -> web.Response:
        """Start the detection system."""
        try:
            if self.is_running:
                return web.json_response({
                    'success': False,
                    'error': 'Detection is already running'
                }, status=400)

            data = await request.json()
            source = data.get('source', '0')
            lane_filtering = data.get('lane_filtering', True)
            config_path = data.get('config_path')

            # Use integrated runner if available, otherwise fall back to subprocess
            if self.detection_runner:
                # Start integrated detection (runs in-process, streams to dashboard)
                try:
                    # Set event loop reference if not already set
                    try:
                        current_loop = asyncio.get_running_loop()
                        if current_loop and not self.detection_runner.event_loop:
                            self.detection_runner.event_loop = current_loop
                            logger.debug(
                                f"Set event loop for detection runner")
                    except RuntimeError:
                        pass

                    self.detection_runner.start(
                        source=source,
                        lane_filtering=lane_filtering,
                        config_path=config_path
                    )
                    self.is_running = True
                    self.current_config = {
                        'source': source,
                        'lane_filtering': lane_filtering,
                        'config_path': config_path,
                        'mode': 'integrated'
                    }
                    logger.info(
                        f"Integrated detection started: source={source}")

                    return web.json_response({
                        'success': True,
                        'message': 'Detection started (streaming to dashboard)',
                        'mode': 'integrated'
                    })
                except Exception as e:
                    logger.error(
                        f"Integrated detection failed: {e}", exc_info=True)
                    return web.json_response({
                        'success': False,
                        'error': f'Failed to start detection: {str(e)}'
                    }, status=500)
            else:
                # Fallback: Start detection as subprocess (old method)
                python_exe = sys.executable
                script_path = project_root / "run_detection.py"

                cmd = [python_exe, str(script_path), '--source', source]

                if not lane_filtering:
                    cmd.append('--no-filter')
                elif config_path:
                    cmd.extend(['--lane-config', config_path])

                # Set environment variable to disable cv2 display window
                env = os.environ.copy()
                env['DASHBOARD_MODE'] = '1'

                self.detection_process = subprocess.Popen(
                    cmd,
                    cwd=str(project_root),
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    env=env,
                    creationflags=0  # Don't create new console window
                )

                self.is_running = True
                self.current_config = {
                    'source': source,
                    'lane_filtering': lane_filtering,
                    'config_path': config_path,
                    'mode': 'subprocess'
                }

                logger.info(f"Subprocess detection started: source={source}")

                return web.json_response({
                    'success': True,
                    'message': 'Detection started (separate window)',
                    'mode': 'subprocess'
                })

        except Exception as e:
            logger.error(f"Error starting detection: {e}")
            self.is_running = False
            return web.json_response({
                'success': False,
                'error': str(e)
            }, status=500)

    async def stop_detection(self, request: web.Request) -> web.Response:
        """Stop the detection system."""
        try:
            if not self.is_running:
                return web.json_response({
                    'success': False,
                    'error': 'Detection is not running'
                }, status=400)

            # Stop integrated runner if it's running
            if self.detection_runner and self.detection_runner.is_running:
                self.detection_runner.stop()

            # Stop subprocess if it's running
            if self.detection_process:
                self.detection_process.terminate()
                try:
                    self.detection_process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    self.detection_process.kill()
                    self.detection_process.wait()
                self.detection_process = None

            self.is_running = False
            self.current_config = {}

            logger.info("Detection stopped")

            return web.json_response({
                'success': True,
                'message': 'Detection stopped successfully'
            })

        except Exception as e:
            logger.error(f"Error stopping detection: {e}")
            return web.json_response({
                'success': False,
                'error': str(e)
            }, status=500)

    async def reset_detection(self, request: web.Request) -> web.Response:
        """Reset detection counters."""
        try:
            # Reset integrated runner if available
            if self.detection_runner:
                self.detection_runner.reset_counters()
                logger.info("Detection counters reset (integrated)")
                return web.json_response({
                    'success': True,
                    'message': 'Counters reset successfully'
                })
            else:
                logger.info(
                    "Reset requested but not available in subprocess mode")
                return web.json_response({
                    'success': False,
                    'message': 'Reset not available in subprocess mode'
                })

        except Exception as e:
            logger.error(f"Error resetting detection: {e}")
            return web.json_response({
                'success': False,
                'error': str(e)
            }, status=500)

    async def cleanup(self):
        """Cleanup resources on shutdown."""
        logger.info("Cleaning up detection controller...")

        # Stop integrated runner
        if self.detection_runner and self.detection_runner.is_running:
            self.detection_runner.stop()

        # Stop subprocess
        if self.detection_process:
            self.detection_process.terminate()
            try:
                self.detection_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.detection_process.kill()

        logger.info("Detection controller cleanup complete")


# CORS middleware
@web.middleware
async def cors_middleware(request, handler):
    """Add CORS headers to responses."""
    if request.method == "OPTIONS":
        response = web.Response()
    else:
        try:
            response = await handler(request)
        except web.HTTPException as ex:
            response = ex

    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'

    return response
