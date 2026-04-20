#!/usr/bin/env python3
"""
Blender Render Monitor - FastAPI Server
Provides real-time monitoring of Blender batch renders via web interface
"""

import asyncio
import argparse
import os
import socket
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from monitor import LogMonitor
from config_manager import get_config

# Initialize FastAPI app
app = FastAPI(
    title="Blender Render Monitor",
    description="Real-time monitoring for Blender batch rendering",
    version="5.3.0"
)

# Enable CORS for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global state
_server_port: int = 8081  # Updated by main() before uvicorn starts
monitor: Optional[LogMonitor] = None
current_log_file: str = ""
render_state: Dict[str, Any] = {
    "project_name": "",
    "status": "idle",
    "current_batch": 0,
    "total_batches": 0,
    "current_frame": 0,
    "batch_start_frame": 0,
    "batch_end_frame": 0,
    "total_frames": 0,
    "frames_completed": 0,
    "batch_progress": 0,
    "overall_progress": 0,
    "avg_frame_time": 0,
    "frame_time": 0,
    "batch_eta": "00:00:00",
    "overall_eta": "00:00:00",
    "elapsed_time": "00:00:00",
    "errors": [],
    "start_time": None,
    "end_time": None,
    "log_file": "",
    "configured_batches": [],  # All batches that were configured for this render
    "batches": []  # Batches detected from log (will be merged with configured_batches)
}

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        print(f"✓ Client connected. Total connections: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
        print(f"✗ Client disconnected. Total connections: {len(self.active_connections)}")

    async def broadcast(self, message: dict):
        """Broadcast message to all connected clients"""
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                print(f"Error broadcasting to client: {e}")

manager = ConnectionManager()


# API Endpoints

@app.get("/")
async def root():
    """Serve the main HTML page"""
    dist_dir = Path(__file__).parent / "frontend" / "dist"
    index_path = dist_dir / "index.html"

    if index_path.exists():
        return FileResponse(
            index_path,
            headers={
                "Cache-Control": "no-cache, no-store, must-revalidate",
                "Pragma": "no-cache",
                "Expires": "0"
            }
        )
    else:
        # Return simple status page if frontend hasn't been built yet
        return HTMLResponse(content=f"""
        <html>
            <head><title>Blender Render Monitor</title></head>
            <body>
                <h1>🎬 Blender Render Monitor</h1>
                <p>Server is running!</p>
                <p>Status: {render_state['status']}</p>
                <p>API Documentation: <a href="/docs">/docs</a></p>
            </body>
        </html>
        """)


@app.get("/api/status")
async def get_status():
    """Get current render status"""
    return {
        "status": "ok",
        "timestamp": datetime.now().isoformat(),
        "render_state": render_state
    }


@app.get("/api/queue")
async def get_queue():
    """Get batch queue information"""
    queue_data = {
        "total_batches": render_state.get("total_batches", 0),
        "current_batch": render_state.get("current_batch", 0),
        "batches": []  # Will be populated by log monitor
    }
    return queue_data


@app.get("/api/stats")
async def get_stats():
    """Get rendering statistics"""
    return {
        "frames_completed": render_state.get("frames_completed", 0),
        "total_frames": render_state.get("total_frames", 0),
        "avg_frame_time": render_state.get("avg_frame_time", 0),
        "elapsed_time": render_state.get("elapsed_time", "00:00:00"),
        "overall_eta": render_state.get("overall_eta", "00:00:00")
    }


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates"""
    await manager.connect(websocket)

    try:
        # Send initial state
        print(f"Sending initial state to WebSocket client")
        await websocket.send_json({
            "type": "init",
            "data": render_state
        })
        print(f"Initial state sent successfully")

        # Keep connection alive with periodic heartbeat
        while True:
            # Send periodic updates every 2 seconds
            await asyncio.sleep(2)
            await websocket.send_json({
                "type": "heartbeat",
                "data": render_state
            })

    except WebSocketDisconnect:
        print(f"WebSocket client disconnected normally")
        manager.disconnect(websocket)
    except Exception as e:
        print(f"WebSocket error: {e}")
        import traceback
        traceback.print_exc()
        manager.disconnect(websocket)


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "version": "5.3.0"}


@app.get("/api/config")
async def get_configuration():
    """Get current configuration"""
    config = get_config()
    return {
        "status": "ok",
        "config": config.get_all()
    }


@app.get("/api/current-render")
async def get_current_render():
    """Get current render configuration from config.json (static data - faster than memory)"""
    config = get_config()
    current_render = config.get_current_render()
    return {
        "status": "ok",
        "current_render": current_render
    }


@app.post("/api/config")
async def update_configuration(updates: Dict[str, Any]):
    """Update configuration settings"""
    config = get_config()

    # Update settings based on provided data
    for key_path, value in updates.items():
        keys = key_path.split('.')
        config.set(*keys, value=value)

    return {
        "status": "ok",
        "message": "Configuration updated",
        "config": config.get_all()
    }


@app.get("/api/batch-profiles")
async def get_batch_profiles():
    """Get all saved batch profiles"""
    config = get_config()
    profiles = config.get_all_batch_profiles()

    return {
        "status": "ok",
        "profiles": profiles
    }


@app.get("/api/batch-profiles/{profile_name}")
async def get_batch_profile(profile_name: str):
    """Get a specific batch profile"""
    config = get_config()
    profile = config.get_batch_profile(profile_name)

    if profile:
        return {
            "status": "ok",
            "profile": profile
        }
    else:
        return {
            "status": "error",
            "message": f"Profile '{profile_name}' not found"
        }


@app.post("/api/batch-profiles")
async def save_batch_profile(data: Dict[str, Any]):
    """Save a batch profile"""
    profile_name = data.get('name', '')
    batches = data.get('batches', [])

    if not profile_name or not batches:
        return {
            "status": "error",
            "message": "Profile name and batches are required"
        }

    config = get_config()
    config.save_batch_profile(profile_name, batches)

    return {
        "status": "ok",
        "message": f"Profile '{profile_name}' saved successfully"
    }


@app.delete("/api/batch-profiles/{profile_name}")
async def delete_batch_profile(profile_name: str):
    """Delete a batch profile"""
    config = get_config()
    success = config.delete_batch_profile(profile_name)

    if success:
        return {
            "status": "ok",
            "message": f"Profile '{profile_name}' deleted"
        }
    else:
        return {
            "status": "error",
            "message": f"Profile '{profile_name}' not found"
        }


@app.get("/api/blend-files")
async def get_blend_files():
    """Get list of recent blend files and scan for available files"""
    config = get_config()

    # Get recent files from config
    recent_files = config.get_recent_blend_files()
    last_file = config.get_last_blend_file()

    # TODO: Scan common directories for .blend files
    # This could be enhanced to scan user's Documents, Desktop, etc.

    return {
        "status": "ok",
        "recent_files": recent_files,
        "last_file": last_file
    }


@app.post("/api/blend-files/add")
async def add_blend_file(data: Dict[str, str]):
    """Add a blend file to recent files"""
    filepath = data.get('filepath', '')

    if not filepath:
        return {"status": "error", "message": "No filepath provided"}

    config = get_config()
    config.add_recent_blend_file(filepath)

    return {
        "status": "ok",
        "message": "Blend file added to recent files",
        "recent_files": config.get_recent_blend_files()
    }


@app.get("/api/blend-files/browse")
async def browse_blend_files(directory: Optional[str] = None):
    """
    Browse for .blend files in a directory

    Args:
        directory: Directory to scan (defaults to common Blender directories)
    """
    import glob

    blend_files = []

    if directory:
        # Scan specified directory
        pattern = f"{directory}/**/*.blend"
        blend_files = glob.glob(pattern, recursive=True)
    else:
        # Scan common directories
        common_dirs = [
            "/Users/me/Podcast/3D-Animation/WIP - Blender",
            "/Users/me/Podcast/3D-Animation/Scenes",
            str(Path.home() / "Documents"),
            str(Path.home() / "Desktop")
        ]

        for dir_path in common_dirs:
            if Path(dir_path).exists():
                pattern = f"{dir_path}/**/*.blend"
                found = glob.glob(pattern, recursive=True)
                blend_files.extend(found)

    # Sort by modification time (most recent first)
    blend_files.sort(key=lambda x: Path(x).stat().st_mtime if Path(x).exists() else 0, reverse=True)

    # Limit to 50 most recent
    blend_files = blend_files[:50]

    return {
        "status": "ok",
        "blend_files": blend_files,
        "count": len(blend_files)
    }


@app.post("/api/render/start")
async def start_render(render_config: Dict[str, Any]):
    """
    Start a new batch render job

    Expected payload:
    {
        "projectName": "MyProject",
        "blendFile": "/path/to/file.blend",
        "batches": [...],
        "totalBatches": 8,
        "totalFrames": 500
    }
    """
    try:
        import subprocess
        import time
        import json
        import tempfile
        from datetime import datetime

        # Extract config
        project_name = render_config.get('projectName', '')
        blend_file = render_config.get('blendFile', '')
        batches = render_config.get('batches', [])

        if not project_name or not blend_file or not batches:
            return {"status": "error", "message": "Missing required fields"}

        # Verify blend file exists
        if not os.path.exists(blend_file):
            return {"status": "error", "message": f"Blend file not found: {blend_file}"}

        # Generate timestamp
        timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')

        # Create output directory (relative to parent of server dir)
        renders_dir = Path(__file__).parent.parent / "renders"
        renders_dir.mkdir(exist_ok=True)

        output_dir = renders_dir / f"{project_name}_{timestamp}"
        output_dir.mkdir(exist_ok=True)

        # Create log file path
        log_file = output_dir / f"{project_name}_{timestamp}_render_log.txt"

        # Create a temporary JSON config file for the bash script to read
        config_data = {
            "project_name": project_name,
            "blend_file": blend_file,
            "batches": batches,
            "output_dir": str(output_dir),
            "log_file": str(log_file),
            "timestamp": timestamp
        }

        # Write config to temp file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as temp_config:
            json.dump(config_data, temp_config, indent=2)
            temp_config_path = temp_config.name

        print(f"✓ Created render config at: {temp_config_path}")
        print(f"✓ Config: {json.dumps(config_data, indent=2)}")

        # Locate render script - bundled app uses sys._MEIPASS, dev uses repo root
        import sys as _sys
        if getattr(_sys, 'frozen', False):
            script_dir = Path(_sys._MEIPASS)
        else:
            script_dir = Path(__file__).parent.parent

        render_script = script_dir / "batchedFrame_render.sh"

        if not render_script.exists():
            os.unlink(temp_config_path)  # Clean up temp file
            return {"status": "error", "message": f"Render script not found at: {render_script}"}

        # Build the AppleScript command to open Terminal and run the script
        applescript = f'''
        tell application "Terminal"
            activate
            do script "cd '{script_dir}' && export RENDER_CONFIG_FILE='{temp_config_path}' && ./batchedFrame_render.sh; echo '\\nPress any key to close this window...'; read -n 1; exit"
        end tell
        '''

        # Launch Terminal with the render script
        subprocess.Popen(
            ['osascript', '-e', applescript],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

        print(f"✓ Launched render in Terminal")
        print(f"✓ Log file will be at: {log_file}")

        # Calculate total frames
        total_frames = sum(batch['end'] - batch['start'] + 1 for batch in batches)

        # Transform batches to include status tracking
        configured_batches = []
        for idx, batch in enumerate(batches, 1):
            configured_batches.append({
                'number': idx,
                'name': batch.get('name', f'Batch {idx}'),
                'start': batch['start'],
                'end': batch['end'],
                'frames': batch['end'] - batch['start'] + 1,
                'priority': batch.get('priority', '0'),
                'completed': False,
                'rendering': False
            })

        # Save config
        config = get_config()
        config.add_recent_blend_file(blend_file)
        config.update_render_settings(project_name, len(batches))

        # Save batch profile as "last" for easy reload
        config.save_batch_profile('last', batches)

        # Save to current_render in config.json (static data - faster than memory)
        config.update_current_render({
            'project_name': project_name,
            'blend_file': blend_file,
            'log_file': str(log_file),
            'output_dir': str(output_dir),
            'timestamp': timestamp,
            'configured_batches': configured_batches,
            'total_frames': total_frames,
            'status': 'rendering'
        })

        # Also save to monitoring.active_render for backwards compatibility
        config.save_active_render({
            'project_name': project_name,
            'blend_file': blend_file,
            'log_file': str(log_file),
            'output_dir': str(output_dir),
            'timestamp': timestamp,
            'configured_batches': configured_batches,
            'total_frames': total_frames,
            'status': 'rendering'
        })

        # Start monitoring the log file
        global monitor, current_log_file
        current_log_file = str(log_file)

        # Give the script time to create the log file (5 seconds)
        # This matches the frontend delay before switching to monitor page
        print("⏳ Waiting 5 seconds for log file generation...")
        await asyncio.sleep(5)

        if monitor:
            monitor.stop()

        print(f"📊 Starting log monitor for: {log_file}")
        monitor = LogMonitor(str(log_file), update_render_state)
        monitor.start()

        # Reset stale state from any previous render before applying new values
        render_state["frames_completed"] = 0
        render_state["overall_progress"] = 0
        render_state["batch_progress"] = 0
        render_state["current_batch"] = 0
        render_state["current_frame"] = 0
        render_state["batch_start_frame"] = 0
        render_state["batch_end_frame"] = 0
        render_state["start_time"] = None
        render_state["end_time"] = None
        render_state["high_priority_list"] = []
        render_state["low_priority_list"] = []
        render_state["completed_list"] = []
        render_state["high_priority_batches"] = 0
        render_state["low_priority_batches"] = 0
        render_state["completed_batches"] = 0
        render_state["batch_eta"] = '00:00:00'
        render_state["overall_eta"] = '00:00:00'
        render_state["frame_time"] = 0
        render_state["avg_frame_time"] = 0

        # Update render state
        render_state["log_file"] = str(log_file)
        render_state["project_name"] = project_name
        render_state["status"] = "rendering"
        render_state["configured_batches"] = configured_batches
        render_state["total_batches"] = len(batches)
        render_state["total_frames"] = total_frames
        render_state["batches"] = []  # Will be populated by monitor as batches start

        print(f"✅ Saved render configuration to config.json")
        print(f"   - Project: {project_name}")
        print(f"   - Batches: {len(configured_batches)}")
        print(f"   - Total Frames: {total_frames}")

        return {
            "status": "ok",
            "message": "Render job started in Terminal",
            "log_file": str(log_file),
            "output_dir": str(output_dir),
            "temp_config": temp_config_path
        }

    except Exception as e:
        print(f"Error starting render: {e}")
        import traceback
        traceback.print_exc()
        return {"status": "error", "message": str(e)}


@app.post("/api/render/cancel")
async def cancel_render():
    """Cancel the current render job"""
    try:
        import subprocess
        import signal

        # Find all running Blender processes
        result = subprocess.run(
            ['pgrep', '-f', 'Blender'],
            capture_output=True,
            text=True
        )

        if result.returncode == 0 and result.stdout.strip():
            pids = result.stdout.strip().split('\n')
            killed_count = 0

            for pid in pids:
                try:
                    pid_int = int(pid)
                    # Send SIGTERM for graceful shutdown
                    subprocess.run(['kill', '-TERM', str(pid_int)])
                    killed_count += 1
                    print(f"✓ Sent SIGTERM to Blender process {pid_int}")
                except ValueError:
                    continue

            # Stop monitoring
            global monitor, current_log_file
            if monitor:
                monitor.stop()
                monitor = None

            # Remove the log file if it exists
            log_removed = False
            if current_log_file and Path(current_log_file).exists():
                try:
                    Path(current_log_file).unlink()
                    print(f"✓ Removed log file: {current_log_file}")
                    log_removed = True
                except Exception as e:
                    print(f"⚠️  Failed to remove log file: {e}")

            # Update render state
            global render_state
            render_state["status"] = "cancelled"
            render_state["log_file"] = ""
            render_state["configured_batches"] = []
            render_state["batches"] = []

            # Clear render config from config.json
            config = get_config()
            config.clear_current_render()
            config.clear_active_render()
            print("✅ Cleared render configuration from config.json")

            # Broadcast update to all clients
            await manager.broadcast({
                "type": "status_update",
                "data": render_state
            })

            message = f"Cancelled {killed_count} Blender process(es)"
            if log_removed:
                message += " and removed log file"

            return {
                "status": "ok",
                "message": message
            }
        else:
            return {
                "status": "ok",
                "message": "No running Blender processes found"
            }

    except Exception as e:
        print(f"Error cancelling render: {e}")
        import traceback
        traceback.print_exc()
        return {"status": "error", "message": str(e)}


@app.get("/api/browse-log-files")
async def browse_log_files():
    """Get list of available log files from renders directory"""
    import glob
    import re
    from datetime import datetime

    try:
        # Look for log files in renders directory (relative to server dir)
        renders_dir = Path(__file__).parent.parent / "renders"
        print(f"🔍 Looking for renders in: {renders_dir.absolute()}")
        print(f"🔍 Renders dir exists: {renders_dir.exists()}")

        if not renders_dir.exists():
            return {"status": "ok", "log_files": []}

        log_files = []

        # Find all render_log.txt files
        for log_file in renders_dir.rglob("*_render_log.txt"):
            print(f"📄 Found log file: {log_file}")
            # Extract project name and timestamp from filename
            filename = log_file.name
            timestamp_match = re.search(r'(\d{4})-(\d{2})-(\d{2})_(\d{2})-(\d{2})-(\d{2})', filename)

            if timestamp_match:
                year, month, day, hour, minute, second = map(int, timestamp_match.groups())
                dt = datetime(year, month, day, hour, minute, second)
                date_str = dt.strftime('%Y-%m-%d %H:%M:%S')

                # Extract project name (everything before the timestamp)
                project_match = re.match(r'^(.+?)_\d{4}-\d{2}-\d{2}', filename)
                project_name = project_match.group(1) if project_match else "Unknown Project"

                log_files.append({
                    "path": str(log_file.absolute()),
                    "project_name": project_name,
                    "date": date_str,
                    "timestamp": dt.timestamp()
                })

        # Sort by timestamp (newest first)
        log_files.sort(key=lambda x: x['timestamp'], reverse=True)

        return {
            "status": "ok",
            "log_files": log_files
        }

    except Exception as e:
        print(f"Error browsing log files: {e}")
        import traceback
        traceback.print_exc()
        return {"status": "error", "message": str(e)}


@app.post("/api/open-in-finder")
async def open_in_finder(data: Dict[str, str]):
    """Open a file or directory in Finder/Explorer"""
    import subprocess
    import platform

    filepath = data.get('filepath', '')

    if not filepath:
        return {"status": "error", "message": "No filepath provided"}

    # Get directory path
    if os.path.isfile(filepath):
        directory = os.path.dirname(filepath)
    else:
        directory = filepath

    if not os.path.exists(directory):
        return {"status": "error", "message": f"Path not found: {directory}"}

    try:
        system = platform.system()

        if system == "Darwin":  # macOS
            # Open Finder and select the file
            subprocess.run(["open", "-R", filepath])
        elif system == "Windows":
            # Open Explorer and select the file
            subprocess.run(["explorer", "/select,", filepath])
        else:  # Linux
            # Open file manager at directory
            subprocess.run(["xdg-open", directory])

        return {
            "status": "ok",
            "message": f"Opened in file manager: {directory}"
        }

    except Exception as e:
        print(f"Error opening in file manager: {e}")
        import traceback
        traceback.print_exc()
        return {"status": "error", "message": str(e)}


@app.post("/api/monitor/override")
async def override_log_file(data: Dict[str, str]):
    """Override the current log file being monitored"""
    global monitor, current_log_file, render_state

    logfile = data.get('logfile', '')

    if not logfile:
        return {"status": "error", "message": "No logfile provided"}

    # Check if file exists
    if not os.path.exists(logfile):
        return {"status": "error", "message": f"Log file not found: {logfile}"}

    try:
        # Stop current monitor if running
        if monitor:
            monitor.stop()

        # Extract project name from log filename
        import re
        filename = Path(logfile).name
        project_match = re.match(r'^(.+?)_\d{4}-\d{2}-\d{2}', filename)
        project_name = project_match.group(1) if project_match else "Unknown Project"

        # Start new monitor with new log file
        print(f"📊 Switching to monitor log file: {logfile}")
        print(f"📊 Project name: {project_name}")
        monitor = LogMonitor(logfile, update_render_state)
        monitor.start()

        # Update global state
        current_log_file = logfile
        render_state["log_file"] = logfile
        render_state["project_name"] = project_name

        # Restore total_frames from config if available, otherwise derive from
        # batches detected in the log file (handles the case where the .app config
        # doesn't know about the render because it was started via the dev server)
        config = get_config()
        current_render = config.get_current_render()
        if current_render and current_render.get('total_frames'):
            render_state["total_frames"] = current_render.get('total_frames', 0)
            render_state["configured_batches"] = current_render.get('configured_batches', [])
            render_state["total_batches"] = len(render_state["configured_batches"])
        elif monitor.state.get('batches'):
            # Fall back to summing frames across all batches found in the log
            total = sum(b.get('frames', 0) for b in monitor.state['batches'])
            render_state["total_frames"] = total
            render_state["total_batches"] = len(monitor.state['batches'])
            print(f"✓ Derived total_frames from log: {total} across {render_state['total_batches']} batches")

        # Recalculate overall_progress now that total_frames is set —
        # the callback fired during monitor.start() when total_frames was still 0
        if render_state["total_frames"] > 0 and render_state["frames_completed"] > 0:
            render_state["overall_progress"] = int(
                (render_state["frames_completed"] / render_state["total_frames"]) * 100
            )

        config.set('monitoring', 'current_log_file', value=logfile)

        return {
            "status": "ok",
            "message": "Successfully switched to new log file",
            "logfile": logfile
        }

    except Exception as e:
        print(f"Error overriding log file: {e}")
        import traceback
        traceback.print_exc()
        return {"status": "error", "message": str(e)}


# Server lifecycle events

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    global monitor, current_log_file, render_state

    print("="*60)
    print("🚀 Blender Render Monitor Starting...")
    print("="*60)

    # Get server info
    hostname = socket.gethostname()
    local_ip = get_local_ip()

    print(f"Hostname: {hostname}")
    print(f"Local IP: {local_ip}")
    print(f"Server: http://localhost:{_server_port}")
    print(f"Network: http://{local_ip}:{_server_port}")
    print("="*60)

    # Skip if monitor already started by main() before uvicorn launched
    if monitor and monitor.running:
        print("✓ Monitor already running (started in main)")
        print("="*60)
        return

    # Load current render configuration from config.json
    config = get_config()
    current_render = config.get_current_render()

    if current_render and current_render.get('configured_batches'):
        print(f"\n📋 Restoring render from config.json: {current_render.get('project_name', 'Unknown')}")
        render_state["project_name"] = current_render.get('project_name', '')
        render_state["configured_batches"] = current_render.get('configured_batches', [])
        render_state["total_batches"] = len(render_state["configured_batches"])
        render_state["total_frames"] = current_render.get('total_frames', 0)
        render_state["status"] = current_render.get('status', 'idle')
        log_file = current_render.get('log_file')
        print(f"   - Batches: {len(render_state['configured_batches'])}")
        print(f"   - Total Frames: {render_state['total_frames']}")
        print(f"   - Status: {render_state['status']}")

        # Start monitoring if we have a log file and status is rendering
        if log_file and render_state["status"] == "rendering":
            import os
            if os.path.exists(log_file):
                print(f"📊 Starting log monitor: {log_file}")
                monitor = LogMonitor(log_file, update_render_state)
                monitor.start()
                current_log_file = log_file
                render_state["log_file"] = log_file
            else:
                print(f"⚠️  Log file not found: {log_file}")
                render_state["status"] = "idle"

    print("="*60)


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    print("\n" + "="*60)
    print("🛑 Blender Render Monitor Shutting Down...")

    if monitor:
        monitor.stop()

    print("="*60)


# Utility functions

def get_local_ip() -> str:
    """Get local network IP address"""
    try:
        # Create a socket to determine local IP
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        return local_ip
    except Exception:
        return "127.0.0.1"


def _merge_batch_states():
    """
    Merge configured_batches with log-detected batches to show complete queue.
    Updates render_state['batches'], 'high_priority_list', 'low_priority_list', and 'completed_list'.
    """
    global render_state

    configured = render_state.get("configured_batches", [])

    if not configured:
        # No configured batches, just use log batches from monitor
        return

    # Collect all log batches from monitor's priority lists
    log_batches = []
    log_batches.extend(render_state.get("high_priority_list", []))
    log_batches.extend(render_state.get("low_priority_list", []))
    log_batches.extend(render_state.get("completed_list", []))

    # Create a map of log batches by frame range for quick lookup
    log_batch_map = {}
    for log_batch in log_batches:
        key = (log_batch['start'], log_batch['end'])
        log_batch_map[key] = log_batch

    # Merge: start with configured batches, update status from log batches
    merged = []
    high_priority_list = []
    low_priority_list = []
    completed_list = []

    for config_batch in configured:
        key = (config_batch['start'], config_batch['end'])

        if key in log_batch_map:
            # This batch has been seen in the log - use log data but keep config name/priority
            log_batch = log_batch_map[key]
            merged_batch = {
                **config_batch,  # Keep configured name, priority
                'completed': log_batch.get('completed', False),
                'rendering': not log_batch.get('completed', False)  # If not completed, it's rendering or waiting
            }
        else:
            # This batch hasn't started yet - keep as configured (pending)
            merged_batch = {
                **config_batch,
                'completed': False,
                'rendering': False  # Hasn't started yet
            }

        merged.append(merged_batch)

        # Categorize into priority lists
        if merged_batch['completed']:
            completed_list.append(merged_batch)
        elif merged_batch.get('priority') == '1':
            high_priority_list.append(merged_batch)
        else:
            # priority is 'null', '0', or anything else = low priority
            low_priority_list.append(merged_batch)

    # Update render_state with merged batches and priority lists
    render_state["batches"] = merged
    render_state["high_priority_list"] = high_priority_list
    render_state["low_priority_list"] = low_priority_list
    render_state["completed_list"] = completed_list

    # Update counts
    render_state["high_priority_batches"] = len(high_priority_list)
    render_state["low_priority_batches"] = len(low_priority_list)
    render_state["completed_batches"] = len(completed_list)

    # Check if ALL configured batches are complete
    all_batches_complete = all(batch.get('completed', False) for batch in merged)
    if all_batches_complete and len(merged) > 0:
        import time
        if not render_state.get('end_time'):
            render_state['end_time'] = time.time()
        render_state['status'] = 'completed'
        print("✅ All configured batches completed!")
    elif render_state.get('status') == 'completed' and not all_batches_complete:
        # If status was 'completed' but we still have incomplete batches, set back to rendering
        render_state['status'] = 'rendering'


def update_render_state(updates: Dict[str, Any]):
    """Update global render state and broadcast to clients"""
    global render_state
    render_state.update(updates)

    try:
        # Calculate derived values
        if render_state["batch_start_frame"] and render_state["batch_end_frame"] and render_state["current_frame"]:
            # Batch progress
            batch_frames = render_state["batch_end_frame"] - render_state["batch_start_frame"] + 1
            if batch_frames > 0:
                frames_done = render_state["current_frame"] - render_state["batch_start_frame"] + 1
                render_state["batch_progress"] = int((frames_done / batch_frames) * 100)

        # Overall progress
        if render_state["total_frames"] > 0 and render_state["frames_completed"] > 0:
            render_state["overall_progress"] = int((render_state["frames_completed"] / render_state["total_frames"]) * 100)

        # Calculate ETAs if we have average frame time
        if render_state.get("avg_frame_time", 0) > 0:
            avg = render_state["avg_frame_time"]

            # Batch ETA
            if render_state["batch_end_frame"] and render_state["current_frame"]:
                frames_left = max(0, render_state["batch_end_frame"] - render_state["current_frame"])
                batch_eta_seconds = int(frames_left * avg)
                render_state["batch_eta"] = seconds_to_time_str(batch_eta_seconds)

            # Overall ETA
            if render_state["total_frames"] > 0:
                frames_left = max(0, render_state["total_frames"] - render_state["frames_completed"])
                overall_eta_seconds = int(frames_left * avg)
                render_state["overall_eta"] = seconds_to_time_str(overall_eta_seconds)

        # Calculate elapsed time
        if render_state.get("start_time"):
            import time
            elapsed = int(time.time() - render_state["start_time"])
            render_state["elapsed_time"] = seconds_to_time_str(elapsed)

    except Exception as e:
        # Silently ignore calculation errors
        pass

    # Merge configured_batches with log batches for complete view
    try:
        _merge_batch_states()
    except Exception as e:
        print(f"Error merging batch states: {e}")

    # Broadcast to all connected WebSocket clients (non-blocking)
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            asyncio.create_task(manager.broadcast({
                "type": "progress",
                "data": render_state
            }))
    except RuntimeError:
        # No event loop running yet, skip broadcast
        pass


def seconds_to_time_str(seconds: int) -> str:
    """Convert seconds to HH:MM:SS format"""
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"


# Main entry point

def main():
    parser = argparse.ArgumentParser(description="Blender Render Monitor Server")
    parser.add_argument("--logfile", type=str, help="Path to render log file")
    parser.add_argument("--port", type=int, default=8081, help="Port to run server on")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--project", type=str, help="Project name")
    parser.add_argument("--batches", type=int, help="Total number of batches")
    parser.add_argument("--frames", type=int, help="Total number of frames")

    args = parser.parse_args()

    # Load current render configuration from config.json (static data)
    config = get_config()
    current_render = config.get_current_render()

    if current_render and current_render.get('configured_batches') and not args.logfile:
        print(f"📋 Restoring render from config.json: {current_render.get('project_name', 'Unknown')}")
        render_state["project_name"] = current_render.get('project_name', '')
        render_state["configured_batches"] = current_render.get('configured_batches', [])
        render_state["total_batches"] = len(render_state["configured_batches"])
        render_state["total_frames"] = current_render.get('total_frames', 0)
        render_state["status"] = current_render.get('status', 'idle')
        args.logfile = current_render.get('log_file')
        print(f"   - Batches: {len(render_state['configured_batches'])}")
        print(f"   - Total Frames: {render_state['total_frames']}")
        print(f"   - Status: {render_state['status']}")

    # Update initial state with provided info
    if args.project:
        render_state["project_name"] = args.project
    if args.batches:
        render_state["total_batches"] = args.batches
    if args.frames:
        render_state["total_frames"] = args.frames

    # Initialize log monitor if logfile provided
    global monitor, current_log_file
    if args.logfile:
        print(f"📊 Monitoring log file: {args.logfile}")
        monitor = LogMonitor(args.logfile, update_render_state)
        monitor.start()

        # Update global state
        current_log_file = args.logfile
        render_state["log_file"] = args.logfile

        # Save current log file to config
        config = get_config()
        config.set('monitoring', 'current_log_file', value=args.logfile)

    # Expose port globally so startup_event can print it
    global _server_port
    _server_port = args.port

    # Run server
    uvicorn.run(
        app,
        host=args.host,
        port=args.port,
        log_level="info",
        access_log=False  # Reduce noise
    )


# Serve pre-built React frontend - must be mounted AFTER all API routes
# so that API paths take precedence over the static file handler
_dist_dir = Path(__file__).parent / "frontend" / "dist"
if _dist_dir.exists():
    app.mount("/", StaticFiles(directory=str(_dist_dir), html=True), name="static")


if __name__ == "__main__":
    main()
