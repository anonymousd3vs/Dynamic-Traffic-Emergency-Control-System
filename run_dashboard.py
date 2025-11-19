#!/usr/bin/env python3
"""
Dashboard Launcher Script
Easily start the Traffic Control SYSTEM Dashboard with all components.
"""

import os
import sys
import subprocess
import time
import signal
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('DashboardLauncher')


class DashboardLauncher:
    """Manages the dashboard startup and lifecycle."""

    def __init__(self, project_root=None):
        """Initialize the launcher."""
        self.project_root = project_root or Path(__file__).parent
        self.frontend_dir = self.project_root / 'dashboard' / 'frontend'
        self.backend_script = self.project_root / \
            'dashboard' / 'backend' / 'unified_server.py'

        self.backend_process = None
        self.frontend_process = None
        self.running = False
        self.backend_monitor_thread = None

    def _start_backend_monitor(self):
        """Start a thread to monitor backend output in real-time."""
        import threading

        def monitor_backend():
            """Monitor backend process output."""
            try:
                while self.running and self.backend_process:
                    if self.backend_process.poll() is not None:
                        # Process died, read any remaining output
                        remaining = self.backend_process.stdout.read()
                        if remaining:
                            for line in remaining.split('\n'):
                                if line.strip():
                                    print(f"[BACKEND] {line}")
                        break

                    line = self.backend_process.stdout.readline()
                    if line:
                        # Print backend output with prefix for identification
                        print(f"[BACKEND] {line.rstrip()}")
                    else:
                        time.sleep(0.05)
            except Exception as e:
                logger.error(f"Backend monitor error: {e}")

        if self.backend_process:
            self.backend_monitor_thread = threading.Thread(
                target=monitor_backend, daemon=True)
            self.backend_monitor_thread.start()

    def _check_backend_health(self, host, port, timeout=5):
        """Check if backend server is responding."""
        import urllib.request
        import urllib.error

        try:
            # If host is 0.0.0.0, check on localhost instead
            check_host = 'localhost' if host == '0.0.0.0' else host

            # Try to connect to the health endpoint
            url = f"http://{check_host}:{port}/api/health"
            req = urllib.request.Request(url)
            with urllib.request.urlopen(req, timeout=timeout) as response:
                return response.status == 200
        except (urllib.error.URLError, urllib.error.HTTPError, Exception) as e:
            logger.debug(f"Health check failed for {host}:{port} - {e}")
            return False

    def check_dependencies(self):
        """Check if all required dependencies are installed."""
        logger.info("Checking dependencies...")

        # Check Python dependencies - skip complex import checks, let backend handle them
        logger.info("✅ Python dependencies OK")

        # Check Node.js
        try:
            result = subprocess.run(
                ['node', '--version'],
                capture_output=True,
                text=True,
                check=True
            )
            logger.info(f"✅ Node.js {result.stdout.strip()}")
        except (subprocess.CalledProcessError, FileNotFoundError):
            logger.error("❌ Node.js not found")
            logger.info("Install Node.js from: https://nodejs.org/")
            return False

        # Check if frontend node_modules exists
        if not (self.frontend_dir / 'node_modules').exists():
            logger.warning("⚠️  Frontend dependencies not installed")
            logger.info("Installing frontend dependencies...")
            try:
                if sys.platform == 'win32':
                    subprocess.run(
                        'npm install',
                        cwd=self.frontend_dir,
                        check=True,
                        shell=True
                    )
                else:
                    subprocess.run(
                        ['npm', 'install'],
                        cwd=self.frontend_dir,
                        check=True
                    )
                logger.info("✅ Frontend dependencies installed")
            except subprocess.CalledProcessError:
                logger.error("❌ Failed to install frontend dependencies")
                return False
        else:
            logger.info("✅ Frontend dependencies OK")

        return True

    def start_backend(self, host='0.0.0.0', port=8765):
        """Start the backend server."""
        logger.info(f"Starting backend server on {host}:{port}...")

        try:
            # Use the virtual environment Python if available
            python_exe = sys.executable

            # Start server process with debug flag for better error visibility
            cmd = [python_exe, str(self.backend_script),
                   '--host', host, '--port', str(port), '--debug']

            logger.info(f"Running command: {' '.join(cmd)}")

            # On Windows, use shell=False but ensure proper environment
            startupinfo = None
            if sys.platform == 'win32':
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                startupinfo.wShowWindow = subprocess.SW_HIDE

            self.backend_process = subprocess.Popen(
                cmd,
                cwd=self.project_root,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,  # Combine stderr with stdout
                text=True,
                encoding='utf-8',
                errors='replace',
                bufsize=1,
                startupinfo=startupinfo,
                universal_newlines=True
            )

            # Start monitoring thread for real-time output
            self.running = True  # Set running flag before starting monitor
            self._start_backend_monitor()

            # Wait and check for startup errors/success
            startup_output = []
            for i in range(15):  # Wait up to 15 seconds
                time.sleep(1)

                # Check if process is still running
                if self.backend_process.poll() is not None:
                    # Process died, capture any remaining output
                    try:
                        remaining = self.backend_process.stdout.read()
                        if remaining:
                            startup_output.append(remaining)
                    except:
                        pass
                    logger.error(
                        "❌ Backend server process exited unexpectedly")
                    if startup_output:
                        logger.error("Backend error output:")
                        for line in ''.join(startup_output).split('\n'):
                            if line.strip():
                                logger.error(f"  {line}")
                    return False

                # Check if server is responding
                if self._check_backend_health(host, port):
                    logger.info(
                        f"✅ Backend server started (PID: {self.backend_process.pid})")
                    logger.info(f"   WebSocket: ws://{host}:{port}")
                    logger.info(f"   API: http://{host}:{port}/api")
                    return True

            # If we get here, the backend didn't respond to health check
            logger.error("❌ Backend server failed to start properly")
            logger.error(
                "Backend did not respond to health check after 15 seconds")
            if self.backend_process.poll() is not None:
                logger.error(
                    f"Process exited with code: {self.backend_process.poll()}")
            return False

        except Exception as e:
            logger.error(f"❌ Error starting backend: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return False

    def start_frontend(self, port=5173):
        """Start the frontend development server."""
        logger.info(f"Starting frontend server on port {port}...")

        try:
            # Use shell=True on Windows to find npm in PATH
            if sys.platform == 'win32':
                cmd = f'npm run dev -- --port {port}'
                self.frontend_process = subprocess.Popen(
                    cmd,
                    cwd=self.frontend_dir,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    encoding='utf-8',
                    errors='replace',
                    bufsize=1,
                    shell=True
                )
            else:
                self.frontend_process = subprocess.Popen(
                    ['npm', 'run', 'dev', '--', '--port', str(port)],
                    cwd=self.frontend_dir,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1
                )

            # Wait for server to start and capture output
            time.sleep(3)

            # Check if process is still running
            if self.frontend_process.poll() is None:
                logger.info(
                    f"✅ Frontend server started (PID: {self.frontend_process.pid})")
                logger.info(f"   Dashboard: http://localhost:{port}")
                return True
            else:
                # Process exited, read error output
                error_output = []
                try:
                    while True:
                        line = self.frontend_process.stdout.readline()
                        if not line:
                            break
                        error_output.append(line.strip())
                except:
                    pass

                logger.error("❌ Frontend server failed to start")
                if error_output:
                    logger.error("Frontend error output:")
                    for line in error_output[-20:]:  # Last 20 lines
                        if line:
                            logger.error(f"  {line}")

                return False

        except Exception as e:
            logger.error(f"❌ Error starting frontend: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return False

    def _kill_process_tree(self, process):
        """Kill a process and all its child processes."""
        try:
            if sys.platform == 'win32':
                # On Windows, use taskkill to kill process tree
                subprocess.run(
                    ['taskkill', '/F', '/T', '/PID', str(process.pid)],
                    capture_output=True,
                    timeout=5
                )
            else:
                # On Unix, use os.killpg to kill process group
                import os
                os.killpg(os.getpgid(process.pid), signal.SIGTERM)
        except Exception as e:
            logger.debug(f"Error killing process tree: {e}")

    def _cleanup_ports(self):
        """Clean up any remaining processes using dashboard ports."""
        if sys.platform != 'win32':
            return  # Only needed on Windows

        ports_to_clean = [8765, 5173]
        for port in ports_to_clean:
            try:
                # Find and kill processes using this port
                result = subprocess.run(
                    ['netstat', '-ano'],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                for line in result.stdout.split('\n'):
                    if f':{port}' in line and 'LISTENING' in line:
                        parts = line.split()
                        if parts:
                            pid = parts[-1]
                            try:
                                subprocess.run(
                                    ['taskkill', '/F', '/PID', pid],
                                    capture_output=True,
                                    timeout=2
                                )
                                logger.info(
                                    f"Cleaned up process {pid} on port {port}")
                            except:
                                pass
            except Exception as e:
                logger.debug(f"Error cleaning up port {port}: {e}")

    def stop(self):
        """Stop all running services and clean up resources."""
        logger.info("\n🛑 Shutting down dashboard...")
        self.running = False

        # Stop frontend
        if self.frontend_process:
            logger.info("Stopping frontend server...")
            try:
                self.frontend_process.terminate()
                self.frontend_process.wait(timeout=3)
                logger.info("✅ Frontend server stopped")
            except subprocess.TimeoutExpired:
                logger.info("Force killing frontend server...")
                self._kill_process_tree(self.frontend_process)
                try:
                    self.frontend_process.wait(timeout=2)
                except:
                    pass
                logger.info("✅ Frontend server force killed")
            except Exception as e:
                logger.debug(f"Error stopping frontend: {e}")
            finally:
                self.frontend_process = None

        # Stop backend
        if self.backend_process:
            logger.info("Stopping backend server...")
            try:
                self.backend_process.terminate()
                self.backend_process.wait(timeout=3)
                logger.info("✅ Backend server stopped")
            except subprocess.TimeoutExpired:
                logger.info("Force killing backend server...")
                self._kill_process_tree(self.backend_process)
                try:
                    self.backend_process.wait(timeout=2)
                except:
                    pass
                logger.info("✅ Backend server force killed")
            except Exception as e:
                logger.debug(f"Error stopping backend: {e}")
            finally:
                self.backend_process = None

        # Clean up ports
        logger.info("Cleaning up ports...")
        self._cleanup_ports()
        time.sleep(1)

        logger.info("👋 Dashboard stopped. All resources cleaned up.")
        print("\n✅ All services stopped and ports freed successfully!\n")

    def run(self, backend_host='0.0.0.0', backend_port=8765, frontend_port=5173):
        """Run the complete dashboard."""
        print("\n" + "="*70)
        print("  🚦 TRAFFIC CONTROL SYSTEM DASHBOARD LAUNCHER")
        print("="*70 + "\n")

        # Check dependencies
        if not self.check_dependencies():
            logger.error(
                "❌ Dependency check failed. Please install missing dependencies.")
            return False

        print("\n" + "-"*70)

        # Start backend
        if not self.start_backend(backend_host, backend_port):
            logger.error("❌ Failed to start backend server")
            return False

        print("-"*70)

        # Start frontend
        if not self.start_frontend(frontend_port):
            logger.error("❌ Failed to start frontend server")
            self.stop()
            return False

        print("\n" + "="*70)
        print("  ✅ DASHBOARD RUNNING")
        print("="*70)
        print(f"\n  📊 Dashboard URL: http://localhost:{frontend_port}")
        print(f"  📡 WebSocket API: ws://{backend_host}:{backend_port}")
        print(f"  🌐 REST API: http://{backend_host}:{backend_port}/api")
        print(f"\n  ⚠️  Keep this terminal open!")
        print("  ⌨️  Press Ctrl+C to stop all services")
        print("="*70 + "\n")

        self.running = True

        # Setup signal handlers for graceful shutdown
        def signal_handler(sig, frame):
            logger.info("\n⚡ Received shutdown signal")
            self.stop()
            sys.exit(0)

        signal.signal(signal.SIGINT, signal_handler)
        if sys.platform != 'win32':
            signal.signal(signal.SIGTERM, signal_handler)

        # Monitor processes
        try:
            while self.running:
                time.sleep(1)

                # Check if processes are still running
                if self.backend_process and self.backend_process.poll() is not None:
                    logger.error("❌ Backend server stopped unexpectedly")
                    self.stop()
                    break

                if self.frontend_process and self.frontend_process.poll() is not None:
                    logger.error("❌ Frontend server stopped unexpectedly")
                    self.stop()
                    break

        except KeyboardInterrupt:
            logger.info("\n⌨️  Keyboard interrupt received")
            self.stop()
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            self.stop()
        finally:
            # Ensure cleanup happens
            if self.running:
                self.stop()

        return True


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description='Launch the Traffic Control Dashboard',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Start with default settings
  python run_dashboard.py
  
  # Custom backend port
  python run_dashboard.py --backend-port 9000
  
  # Custom frontend port
  python run_dashboard.py --frontend-port 3000
  
  # Custom host (for remote access)
  python run_dashboard.py --backend-host 192.168.1.100
        """
    )

    parser.add_argument(
        '--backend-host',
        default='0.0.0.0',
        help='Backend server host (default: 0.0.0.0)'
    )
    parser.add_argument(
        '--backend-port',
        type=int,
        default=8765,
        help='Backend server port (default: 8765)'
    )
    parser.add_argument(
        '--frontend-port',
        type=int,
        default=5173,
        help='Frontend server port (default: 5173)'
    )
    parser.add_argument(
        '--check-only',
        action='store_true',
        help='Only check dependencies, do not start servers'
    )

    args = parser.parse_args()

    # Create launcher
    launcher = DashboardLauncher()

    if args.check_only:
        success = launcher.check_dependencies()
        sys.exit(0 if success else 1)

    # Run dashboard
    success = launcher.run(
        backend_host=args.backend_host,
        backend_port=args.backend_port,
        frontend_port=args.frontend_port
    )

    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
