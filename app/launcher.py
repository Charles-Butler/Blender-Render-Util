#!/usr/bin/env python3
"""
Render Manager — Desktop App Launcher
Starts the FastAPI backend in a daemon thread, then opens a native
PyWebView window. Shuts down cleanly when the window is closed.
"""

import sys
import os
import threading
import time
import argparse
import urllib.request
import urllib.error

# Resolve paths for both dev and PyInstaller bundle modes
if getattr(sys, 'frozen', False):
    # Inside .app bundle — all files extracted to sys._MEIPASS
    BASE_DIR = sys._MEIPASS
else:
    # Running from source — server/ is one level up from app/
    BASE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'server')

BASE_DIR = os.path.abspath(BASE_DIR)
sys.path.insert(0, BASE_DIR)

# Config storage: use persistent user dir in bundle, local dir in dev
if getattr(sys, 'frozen', False):
    CONFIG_DIR = os.path.join(os.path.expanduser('~'), 'Library', 'Application Support', 'RenderManager')
    os.makedirs(CONFIG_DIR, exist_ok=True)
    os.environ['RENDER_MANAGER_CONFIG_DIR'] = CONFIG_DIR

PORT = 8081
HOST = '127.0.0.1'
HEALTH_URL = f'http://{HOST}:{PORT}/health'
STARTUP_TIMEOUT = 15  # seconds to wait for server to be ready


def start_server(blend_file: str = None):
    """Start FastAPI/uvicorn in a daemon thread."""
    import uvicorn

    # Pre-populate blend file into config before server starts
    if blend_file and os.path.exists(blend_file):
        try:
            from config_manager import get_config
            config = get_config()
            config.add_recent_blend_file(blend_file)
            config.set('blender', 'last_blend_file', value=blend_file)
            print(f'✓ Blend file pre-loaded: {os.path.basename(blend_file)}')
        except Exception as e:
            print(f'⚠️  Could not pre-load blend file: {e}')

    config = uvicorn.Config(
        'app:app',
        host=HOST,
        port=PORT,
        log_level='warning',
        access_log=False,
    )
    server = uvicorn.Server(config)

    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()
    return server, thread


def wait_for_server(timeout: int = STARTUP_TIMEOUT) -> bool:
    """Poll /health until the server responds or timeout is reached."""
    print('⏳ Waiting for server to start...')
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(HEALTH_URL, timeout=1) as resp:
                if resp.status == 200:
                    print('✓ Server ready')
                    return True
        except Exception:
            pass
        time.sleep(0.25)
    print('❌ Server did not start in time')
    return False


def open_window():
    """Open the PyWebView native window."""
    import webview

    window = webview.create_window(
        title='Render Manager',
        url=f'http://{HOST}:{PORT}',
        width=1280,
        height=820,
        min_size=(900, 600),
        resizable=True,
        text_select=False,
    )

    # Start the webview (blocks until window is closed)
    webview.start(debug=False)


def main():
    parser = argparse.ArgumentParser(description='Render Manager')
    parser.add_argument(
        '--blend-file',
        type=str,
        default=None,
        help='Path to .blend file to pre-select (passed from Blender add-on)'
    )
    args = parser.parse_args()

    print('=' * 50)
    print('  Render Manager v5.2.0')
    print('=' * 50)

    # Start backend
    server, thread = start_server(blend_file=args.blend_file)

    # Wait for it to be ready
    if not wait_for_server():
        print('❌ Failed to start server. Exiting.')
        sys.exit(1)

    # Open native window — blocks until closed
    open_window()

    # Window closed — shut down server
    print('👋 Window closed, shutting down...')
    server.should_exit = True
    thread.join(timeout=3)


if __name__ == '__main__':
    main()
