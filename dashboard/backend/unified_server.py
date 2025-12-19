#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unified Dashboard Server
Handles BOTH traffic detection AND signal control in a single server.
"""

# THIS MUST BE FIRST - sets up sys.path before other dashboard imports
import setup_path  # noqa: F401 (imported but unused - needed for side effects)

# Standard library imports
import sys
import os

# Set UTF-8 encoding for Windows console
if sys.platform == 'win32':
    import codecs
    if sys.stdout.encoding != 'utf-8':
        sys.stdout.reconfigure(encoding='utf-8')

import signal
import logging
import asyncio
import json
from pathlib import Path
from datetime import datetime

# Third-party imports
from aiohttp import web

# Dashboard imports (path is now set up)
from dashboard.backend.api_routes import DashboardAPI, cors_middleware
from dashboard.backend.stream_manager import StreamManager
from dashboard.backend.websocket_server import DashboardStreamer
from dashboard.backend.detection_controller import DetectionController

# Traffic signals imports
from traffic_signals.core.indian_traffic_signal import IntersectionController, SignalState
from dashboard.backend.dynamic_timing_integration import DynamicTimingIntegration

# Project root for other modules
project_root = Path(__file__).resolve().parent.parent.parent

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('UnifiedServer')


class UnifiedDashboardServer:
    """Unified server handling both detection and traffic signals."""

    def __init__(self, host='0.0.0.0', port=8765):
        """
        Initialize the unified server.

        Args:
            host: Host address
            port: Server port for both WebSocket and HTTP API
        """
        self.host = host
        self.port = port

        logger.info(f"Initializing Unified Dashboard Server on {host}:{port}")

        # ============================================================
        # TRAFFIC SIGNAL SYSTEM COMPONENTS (INIT FIRST)
        # ============================================================
        self.signal_controller = self._init_signal_controller()
        self.dynamic_timing = DynamicTimingIntegration(self.signal_controller)

        # ============================================================
        # DETECTION SYSTEM COMPONENTS
        # ============================================================
        self.streamer = DashboardStreamer(host, port)
        # 🔧 Pass dynamic_timing to streamer for real-time vehicle count updates
        self.streamer.dynamic_timing = self.dynamic_timing

        self.stream_manager = StreamManager()
        self.api = DashboardAPI(self.streamer, self.stream_manager)
        self.detection_controller = DetectionController(
            self.streamer, self.stream_manager)

        # Setup all routes
        self._setup_detection_routes()
        self._setup_signal_routes()
        self._setup_health_routes()

        # Add middleware
        self.streamer.app.middlewares.append(cors_middleware)

        self.runner = None
        self.site = None
        self.is_running = False

        logger.info("✅ Unified server initialized")

    def _init_signal_controller(self):
        """Initialize and configure the traffic signal controller."""
        logger.info("Initializing traffic signal controller...")

        # Use the standard IntersectionController with proper phase management
        controller = IntersectionController()
        controller.add_lane('north', 'NORTH')
        controller.add_lane('south', 'SOUTH')
        controller.add_lane('east', 'EAST')
        controller.add_lane('west', 'WEST')
        controller.start()

        # Store reference for dynamic timing updates
        self.dynamic_timing_enabled = True
        logger.info("✅ Traffic signal controller initialized")
        logger.info(
            "   Mode: STANDARD PHASE MANAGEMENT with DYNAMIC TIMING capability")
        return controller

    def _setup_detection_routes(self):
        """Setup detection system API routes."""
        logger.info("Setting up detection routes...")

        # Use the existing API routes from DashboardAPI
        self.api.setup_routes(self.streamer.app)
        self.detection_controller.setup_routes(self.streamer.app)

        logger.info("✅ Detection routes configured")

    async def _handle_get_signals_status(self, request: web.Request) -> web.Response:
        """Get current signal status for all directions."""
        try:
            signals = {}
            controller = self.signal_controller

            # Get current phase info
            current_phase = controller.current_phase
            phase_elapsed = controller.phase_elapsed_time
            
            # Phase sequence: N(1) -> E(3) -> S(5) -> W(7) with yellows in between
            # Map direction to their GREEN phase number
            direction_to_green_phase = {
                'north': 1,  # PHASE_1
                'east': 3,   # PHASE_3
                'south': 5,  # PHASE_5
                'west': 7,   # PHASE_7
            }
            
            # Calculate remaining time in current phase
            current_phase_num = current_phase.value
            current_phase_duration = controller.phase_timings.get(current_phase, 0)
            time_left_in_current_phase = max(0, current_phase_duration - phase_elapsed)

            for direction in ['north', 'south', 'east', 'west']:
                lane = controller.lanes[direction]
                green_phase_num = direction_to_green_phase[direction]
                
                if controller.emergency_active and controller.emergency_start_time:
                    # During emergency
                    emergency_elapsed = (datetime.now() - controller.emergency_start_time).total_seconds()
                    if lane.ambulance_active:
                        time_remaining = max(0, 45 - emergency_elapsed)
                    else:
                        time_remaining = max(0, 45 - emergency_elapsed)
                elif lane.current_state.value == 'GREEN':
                    # This direction is currently green - show remaining green time
                    time_remaining = time_left_in_current_phase
                elif lane.current_state.value == 'YELLOW':
                    # This direction is yellow - show remaining yellow time
                    time_remaining = time_left_in_current_phase
                else:
                    # RED - calculate cumulative wait until this direction gets GREEN
                    time_remaining = self._calculate_wait_until_green(
                        current_phase_num, 
                        green_phase_num,
                        time_left_in_current_phase,
                        controller.phase_timings
                    )
                
                signals[direction] = {
                    'state': lane.current_state.value,
                    'elapsed': round(lane.elapsed_time, 2),
                    'timeRemaining': round(time_remaining, 1),
                    'isAmbulance': lane.ambulance_active,
                }

            stats = controller.get_statistics()

            response = {
                'signals': signals,
                'statistics': {
                    'currentPhase': stats['current_phase'],
                    'isRunning': stats['is_running'],
                    'totalAmbulances': stats['total_ambulances'],
                    'completedAmbulances': stats['completed_ambulances'],
                    'activeEmergencies': stats.get('active_emergencies', 0),
                },
                'timestamp': datetime.now().isoformat(),
            }

            return web.json_response(response, status=200)
        except Exception as e:
            logger.error(f"Error getting signal status: {e}")
            return web.json_response(
                {'error': str(e)},
                status=500
            )

    def _calculate_wait_until_green(self, current_phase_num: int, target_green_phase: int, 
                                     time_left_current: float, phase_timings: dict) -> float:
        """
        Calculate cumulative wait time until a direction gets GREEN.
        
        Phase structure (9 phases total, wraps around):
        1=N_GREEN, 2=N_YELLOW, 3=E_GREEN, 4=E_YELLOW, 
        5=S_GREEN, 6=S_YELLOW, 7=W_GREEN, 8=W_YELLOW, 9=ALL_RED
        
        Example: If current=1 (N GREEN) and target=5 (S GREEN):
        Wait = time_left_phase_1 + phase_2 + phase_3 + phase_4 = remaining_N + Y + E_green + E_yellow
        """
        from traffic_signals.core.indian_traffic_signal import IntersectionPhase
        
        total_wait = time_left_current
        
        # Get list of phases
        phases = list(IntersectionPhase)
        total_phases = len(phases)  # 9 phases
        
        # Start from the next phase after current
        current_idx = current_phase_num - 1  # Convert to 0-indexed
        target_idx = target_green_phase - 1
        
        # Move through phases until we reach target
        idx = (current_idx + 1) % total_phases
        
        while idx != target_idx:
            phase = phases[idx]
            phase_duration = phase_timings.get(phase, 0)
            total_wait += phase_duration
            idx = (idx + 1) % total_phases
            
            # Safety: prevent infinite loop
            if total_wait > 500:
                break
        
        return total_wait

    async def _handle_trigger_ambulance(self, request: web.Request) -> web.Response:
        """Trigger ambulance mode for a specific direction."""
        try:
            data = await request.json()
            direction = data.get('direction', 'north').lower()
            confidence = data.get('confidence', 0.95)

            if direction not in ['north', 'south', 'east', 'west']:
                return web.json_response(
                    {'error': f'Invalid direction: {direction}'},
                    status=400
                )

            success = self.signal_controller.activate_ambulance(
                direction, confidence)

            logger.info(f"🚑 Ambulance triggered for {direction} "
                        f"(confidence: {confidence})")

            return web.json_response({
                'success': success,
                'direction': direction,
                'confidence': confidence,
                'message': f'Ambulance mode activated for {direction}'
                if success else 'Ambulance trigger failed',
            }, status=200 if success else 400)

        except Exception as e:
            logger.error(f"Error triggering ambulance: {e}")
            return web.json_response(
                {'error': str(e)},
                status=500
            )

    async def _handle_reset_signals(self, request: web.Request) -> web.Response:
        """Reset the signal system to initial state."""
        try:
            self.signal_controller.reset()
            self.signal_controller.start()

            logger.info("🔄 Signal system reset")

            return web.json_response({
                'success': True,
                'message': 'Signal system reset',
            }, status=200)

        except Exception as e:
            logger.error(f"Error resetting signals: {e}")
            return web.json_response(
                {'error': str(e)},
                status=500
            )

    async def _handle_pause_signals(self, request: web.Request) -> web.Response:
        """Pause the signal system."""
        try:
            self.signal_controller.stop()

            logger.info("⏸️  Signal system paused")

            return web.json_response({
                'success': True,
                'message': 'Signal system paused',
            }, status=200)

        except Exception as e:
            logger.error(f"Error pausing signals: {e}")
            return web.json_response(
                {'error': str(e)},
                status=500
            )

    async def _handle_resume_signals(self, request: web.Request) -> web.Response:
        """Resume the signal system."""
        try:
            self.signal_controller.start()

            logger.info("▶️  Signal system resumed")

            return web.json_response({
                'success': True,
                'message': 'Signal system resumed',
            }, status=200)

        except Exception as e:
            logger.error(f"Error resuming signals: {e}")
            return web.json_response(
                {'error': str(e)},
                status=500
            )

    async def _handle_select_lane(self, request: web.Request) -> web.Response:
        """
        Select a lane for dynamic timing.

        POST /api/signals/select-lane
        JSON: {"lane": "east"}
        """
        try:
            data = await request.json()
            lane = data.get('lane', '').lower()

            if lane not in ['north', 'south', 'east', 'west']:
                return web.json_response(
                    {'error': f'Invalid lane: {lane}'},
                    status=400
                )

            # Select lane for dynamic timing
            result = self.dynamic_timing.select_lane(lane)

            if result['status'] != 'success':
                return web.json_response(result, status=400)

            logger.info(f"✅ Lane selected: {lane.upper()}")

            return web.json_response(result, status=200)

        except json.JSONDecodeError:
            return web.json_response(
                {'error': 'Invalid JSON'},
                status=400
            )
        except Exception as e:
            logger.error(f"Error selecting lane: {e}")
            return web.json_response(
                {'error': str(e)},
                status=500
            )

    async def _handle_vehicle_count_update(self, request: web.Request) -> web.Response:
        """
        Update vehicle count for selected lane and adjust signal timing dynamically.

        POST /api/signals/vehicle-count
        JSON: {"count": 12}
        """
        try:
            data = await request.json()
            vehicle_count = data.get('count', 0)

            if self.dynamic_timing.selected_lane is None:
                return web.json_response(
                    {'error': 'No lane selected. Call /api/signals/select-lane first'},
                    status=400
                )

            # Update dynamic timing with vehicle count for selected lane
            result = self.dynamic_timing.update_vehicle_count(vehicle_count)

            if result['status'] != 'success':
                return web.json_response(result, status=400)

            # Return timing information
            response = {
                'success': True,
                'selected_lane': result['selected_lane'],
                'vehicle_count': vehicle_count,
                'timing': result['timing'],
                'message': f'Timing updated for {result["selected_lane"]} with {vehicle_count} vehicles',
            }

            return web.json_response(response, status=200)

        except json.JSONDecodeError:
            return web.json_response(
                {'error': 'Invalid JSON'},
                status=400
            )
        except Exception as e:
            logger.error(f"Error updating vehicle count: {e}")
            return web.json_response(
                {'error': str(e)},
                status=500
            )

    async def _handle_dynamic_timing_status(self, request: web.Request) -> web.Response:
        """Get current dynamic timing status."""
        try:
            status = self.dynamic_timing.get_current_status()
            return web.json_response(status, status=200)
        except Exception as e:
            logger.error(f"Error getting dynamic timing status: {e}")
            return web.json_response(
                {'error': str(e)},
                status=500
            )

    async def _handle_dynamic_timing_stats(self, request: web.Request) -> web.Response:
        """Get detailed dynamic timing statistics."""
        try:
            stats = self.dynamic_timing.get_statistics()
            return web.json_response(stats, status=200)
        except Exception as e:
            logger.error(f"Error getting dynamic timing stats: {e}")
            return web.json_response(
                {'error': str(e)},
                status=500
            )

    def _setup_signal_routes(self):
        """Setup traffic signal API routes."""
        logger.info("Setting up signal routes...")

        app = self.streamer.app
        if app is None:
            logger.error("❌ Application is None - cannot setup routes")
            raise RuntimeError("Application object is None")

        # Register signal routes
        app.router.add_get('/api/signals/status',
                           self._handle_get_signals_status)
        app.router.add_post('/api/signals/ambulance',
                            self._handle_trigger_ambulance)
        app.router.add_post('/api/signals/reset', self._handle_reset_signals)
        app.router.add_post('/api/signals/pause', self._handle_pause_signals)
        app.router.add_post('/api/signals/resume', self._handle_resume_signals)

        # Dynamic timing routes
        app.router.add_post('/api/signals/select-lane',
                            self._handle_select_lane)
        app.router.add_post('/api/signals/vehicle-count',
                            self._handle_vehicle_count_update)
        app.router.add_get('/api/signals/dynamic-timing/status',
                           self._handle_dynamic_timing_status)
        app.router.add_get('/api/signals/dynamic-timing/stats',
                           self._handle_dynamic_timing_stats)

        logger.info("✅ Signal routes configured")

    async def _handle_health_check(self, request: web.Request) -> web.Response:
        """Health check endpoint."""
        return web.json_response({
            'status': 'ok',
            'service': 'unified-traffic-control-api',
            'timestamp': datetime.now().isoformat()
        })

    def _setup_health_routes(self):
        """Setup health check routes."""
        app = self.streamer.app
        app.router.add_get('/health', self._handle_health_check)

    async def start(self):
        """Start the unified server."""
        logger.info("Starting unified server...")

        try:
            self.runner = web.AppRunner(self.streamer.app)
            await self.runner.setup()
            self.site = web.TCPSite(self.runner, self.host, self.port)
            await self.site.start()

            logger.info(f"✅ Unified server started successfully!")
            logger.info(f"   WebSocket: ws://{self.host}:{self.port}")
            logger.info(f"   API: http://{self.host}:{self.port}/api")
            logger.info(
                f"   Signals API: http://{self.host}:{self.port}/api/signals")

        except Exception as e:
            logger.error(f"Failed to start server: {e}")
            raise

    async def stop(self):
        """Stop the unified server."""
        logger.info("Stopping unified server...")

        try:
            # Cleanup detection controller
            await self.detection_controller.cleanup()

            # Stop signal controller
            if self.signal_controller:
                self.signal_controller.stop()

            if self.site:
                await self.site.stop()

            if self.runner:
                await self.runner.cleanup()

            await self.streamer.stop()

            logger.info("✅ Unified server stopped")

        except Exception as e:
            logger.error(f"Error stopping server: {e}")

    async def _update_signals(self):
        """Continuously update signal controller."""
        while self.is_running:
            try:
                if self.signal_controller and self.signal_controller.is_running:
                    self.signal_controller.update(0.1)  # Update every 100ms
                await asyncio.sleep(0.1)
            except Exception as e:
                logger.error(f"Error updating signals: {e}")
                await asyncio.sleep(0.1)

    async def run_forever(self):
        """Run the server forever."""
        try:
            # Start signal update loop
            self.is_running = True
            update_task = asyncio.create_task(self._update_signals())

            while True:
                await asyncio.sleep(1)
        except asyncio.CancelledError:
            self.is_running = False
            pass


async def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Unified Traffic Control Dashboard Server",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Start with default settings
  python unified_server.py
  
  # Start on custom port
  python unified_server.py --port 9000
  
  # Start on custom host
  python unified_server.py --host 192.168.1.100
  
  # Enable debug logging
  python unified_server.py --debug
        """
    )

    parser.add_argument(
        '--host',
        default='0.0.0.0',
        help='Server host (default: 0.0.0.0)'
    )
    parser.add_argument(
        '--port',
        type=int,
        default=8765,
        help='Server port (default: 8765)'
    )
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Enable debug logging'
    )

    args = parser.parse_args()

    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
        logging.getLogger('aiohttp').setLevel(logging.DEBUG)

    # Create server
    server = UnifiedDashboardServer(host=args.host, port=args.port)

    # Setup signal handlers for graceful shutdown
    def signal_handler(sig, frame):
        logger.info("\n🛑 Shutdown signal received...")
        raise KeyboardInterrupt()

    signal.signal(signal.SIGINT, signal_handler)
    if sys.platform != 'win32':
        signal.signal(signal.SIGTERM, signal_handler)

    # Print banner
    print("\n" + "="*70)
    print("  🚦 UNIFIED TRAFFIC CONTROL SYSTEM DASHBOARD")
    print("="*70)
    print(f"  📡 WebSocket Server: ws://{args.host}:{args.port}")
    print(f"  🌐 API Server: http://{args.host}:{args.port}/api")
    print(f"  🚦 Signals API: http://{args.host}:{args.port}/api/signals")
    print("="*70)
    print("\n  📋 Available Features:")
    print("     ✅ Live Detection System")
    print("     ✅ Traffic Signal Control")
    print("     ✅ Real-time Metrics")
    print("     ✅ Emergency Alerts")
    print("     ✅ Ambulance Priority")
    print("\n  📊 Detection Endpoints:")
    print("     GET  /api/status              - System status")
    print("     GET  /api/metrics/current     - Current metrics")
    print("     GET  /api/metrics/history     - Historical metrics")
    print("\n  🚦 Signal Endpoints:")
    print("     GET  /api/signals/status      - Signal status")
    print("     POST /api/signals/ambulance   - Trigger ambulance")
    print("     POST /api/signals/reset       - Reset signals")
    print("     POST /api/signals/pause       - Pause signals")
    print("     POST /api/signals/resume      - Resume signals")
    print("\n  ⚙️  Press Ctrl+C to stop")
    print("="*70 + "\n")

    try:
        # Start server
        logger.info("Starting unified server...")
        await server.start()
        logger.info("✅ Unified server started successfully")

        # Run forever
        await server.run_forever()

    except KeyboardInterrupt:
        logger.info("\n🛑 Keyboard interrupt received")
    except Exception as e:
        logger.error(f"Server error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        logger.info("Cleaning up...")
        await server.stop()
        logger.info("Server stopped")


if __name__ == '__main__':
    if sys.platform == 'win32':
        # Windows-specific event loop policy
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
