#!/usr/bin/env python3
"""Main launcher for STA Starship Simulator Mac app.

This script is the entry point for the PyInstaller-built .app bundle.
It starts the Flask server and opens the browser.
"""

import os
import socket
import subprocess
import sys
import threading
import time
import webbrowser
from pathlib import Path


def get_resource_path(relative_path: str) -> Path:
    """Get absolute path to resource, works for dev and PyInstaller."""
    if getattr(sys, 'frozen', False):
        # Running in PyInstaller bundle
        base_path = Path(sys._MEIPASS)
    else:
        # Running in normal Python environment
        base_path = Path(__file__).parent

    return base_path / relative_path


def find_available_port(start_port: int = 5001, max_attempts: int = 100) -> int:
    """Find an available port starting from start_port."""
    for port in range(start_port, start_port + max_attempts):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('127.0.0.1', port))
                return port
        except OSError:
            continue
    raise RuntimeError(f"No available port found between {start_port} and {start_port + max_attempts}")


def wait_for_server(host: str, port: int, timeout: float = 30.0) -> bool:
    """Wait for the server to become available."""
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(1)
                s.connect((host, port))
                return True
        except (socket.error, socket.timeout):
            time.sleep(0.1)
    return False


def get_local_ip() -> str:
    """Get the local IP address for network access."""
    try:
        # Create a dummy connection to find our local IP
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            return s.getsockname()[0]
    except Exception:
        return "127.0.0.1"


def check_for_updates_background():
    """Check for updates in the background and notify if available."""
    try:
        from sta.updater import check_for_updates
        from sta.version import __version__

        update = check_for_updates()
        if update:
            print(f"\n{'='*50}")
            print(f"  UPDATE AVAILABLE: v{update.version}")
            print(f"  Current version: v{__version__}")
            print(f"  Download at: https://github.com/tommertron/staStarShipSimulator/releases")
            print(f"{'='*50}\n")
    except Exception as e:
        # Don't crash on update check failure
        pass


def run_server(host: str, port: int):
    """Run the Flask server."""
    # Set up environment
    os.environ['FLASK_APP'] = 'sta.web.app:create_app'

    # Import and create the app
    from sta.web.app import create_app
    app = create_app()

    # Use werkzeug's server directly for simplicity in the app bundle
    from werkzeug.serving import run_simple

    # Suppress werkzeug logs after initial startup
    import logging
    log = logging.getLogger('werkzeug')
    log.setLevel(logging.ERROR)

    run_simple(host, port, app, use_reloader=False, use_debugger=False, threaded=True)


def main():
    """Main entry point for the launcher."""
    from sta.version import __version__

    print("=" * 50)
    print("  STA Starship Simulator")
    print(f"  Version {__version__}")
    print("=" * 50)
    print()

    # Check for updates in background
    update_thread = threading.Thread(target=check_for_updates_background, daemon=True)
    update_thread.start()

    # Find available port
    port = find_available_port(5001)
    host = '0.0.0.0'  # Listen on all interfaces for network play

    local_ip = get_local_ip()

    print(f"Starting server on port {port}...")
    print()

    # Start server in background thread
    server_thread = threading.Thread(target=run_server, args=(host, port), daemon=True)
    server_thread.start()

    # Wait for server to be ready
    if not wait_for_server('127.0.0.1', port):
        print("ERROR: Server failed to start!")
        sys.exit(1)

    print("Server started!")
    print()
    print("=" * 50)
    print("  Access the app at:")
    print()
    print(f"  Local:   http://127.0.0.1:{port}")
    print(f"  Network: http://{local_ip}:{port}")
    print()
    print("  Share the Network URL with players!")
    print("=" * 50)
    print()
    print("Press Ctrl+C to stop the server")
    print()

    # Open browser to local URL
    webbrowser.open(f'http://127.0.0.1:{port}')

    # Keep running until interrupted
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nShutting down...")


if __name__ == '__main__':
    main()
