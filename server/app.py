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
    version="2.3.0"
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
monitor: Optional[LogMonitor] = None
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
    "start_time": None
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
    static_dir = Path(__file__).parent / "static"
    index_path = static_dir / "index.html"

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
        # Return simple status page if no HTML exists yet
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
    return {"status": "healthy", "version": "2.3.0"}


@app.get("/api/config")
async def get_configuration():
    """Get current configuration"""
    config = get_config()
    return {
        "status": "ok",
        "config": config.get_all()
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
        from datetime import datetime

        # Extract config
        project_name = render_config.get('projectName', '')
        blend_file = render_config.get('blendFile', '')
        batches = render_config.get('batches', [])

        if not project_name or not blend_file or not batches:
            return {"status": "error", "message": "Missing required fields"}

        # Generate timestamp
        timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')

        # Create output directory
        output_dir = f"./renders/{project_name}_{timestamp}"
        import os
        os.makedirs(output_dir, exist_ok=True)

        # Create log file path
        log_file = f"{output_dir}/{project_name}_{timestamp}_render_log.txt"

        # TODO: Start the actual batch render script in background
        # For now, we'll just create a placeholder log file
        with open(log_file, 'w') as f:
            f.write(f"Render started at {timestamp}\n")
            f.write(f"Project: {project_name}\n")
            f.write(f"Blend file: {blend_file}\n")
            f.write(f"Total batches: {len(batches)}\n")

        # Save config
        config = get_config()
        config.add_recent_blend_file(blend_file)
        config.update_render_settings(project_name, len(batches))

        return {
            "status": "ok",
            "message": "Render job started",
            "log_file": log_file,
            "output_dir": output_dir
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
        # TODO: Implement actual render cancellation
        # This would need to:
        # 1. Find the running Blender process
        # 2. Send SIGTERM to gracefully stop it
        # 3. Update render state

        return {
            "status": "ok",
            "message": "Render job cancelled"
        }

    except Exception as e:
        print(f"Error cancelling render: {e}")
        return {"status": "error", "message": str(e)}


# Server lifecycle events

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    print("="*60)
    print("🚀 Blender Render Monitor Starting...")
    print("="*60)

    # Get server info
    hostname = socket.gethostname()
    local_ip = get_local_ip()

    print(f"Hostname: {hostname}")
    print(f"Local IP: {local_ip}")
    print(f"Server: http://localhost:8080")
    print(f"Network: http://{local_ip}:8080")
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
    parser.add_argument("--port", type=int, default=8080, help="Port to run server on")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--project", type=str, help="Project name")
    parser.add_argument("--batches", type=int, help="Total number of batches")
    parser.add_argument("--frames", type=int, help="Total number of frames")

    args = parser.parse_args()

    # Update initial state with provided info
    if args.project:
        render_state["project_name"] = args.project
    if args.batches:
        render_state["total_batches"] = args.batches
    if args.frames:
        render_state["total_frames"] = args.frames

    # Initialize log monitor if logfile provided
    global monitor
    if args.logfile:
        print(f"📊 Monitoring log file: {args.logfile}")
        monitor = LogMonitor(args.logfile, update_render_state)
        monitor.start()

    # Run server
    uvicorn.run(
        app,
        host=args.host,
        port=args.port,
        log_level="info",
        access_log=False  # Reduce noise
    )


if __name__ == "__main__":
    main()
