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
    "batch_eta": "00:00:00",
    "overall_eta": "00:00:00",
    "elapsed_time": "00:00:00",
    "errors": []
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
        return FileResponse(index_path)
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
        await websocket.send_json({
            "type": "init",
            "data": render_state
        })

        # Keep connection alive with periodic heartbeat
        while True:
            # Send periodic updates every 2 seconds
            await asyncio.sleep(2)
            await websocket.send_json({
                "type": "heartbeat",
                "data": render_state
            })

    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        print(f"WebSocket error: {e}")
        manager.disconnect(websocket)


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "version": "2.3.0"}


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

    # Broadcast to all connected WebSocket clients
    asyncio.create_task(manager.broadcast({
        "type": "progress",
        "data": render_state
    }))


# Main entry point

def main():
    parser = argparse.ArgumentParser(description="Blender Render Monitor Server")
    parser.add_argument("--logfile", type=str, help="Path to render log file")
    parser.add_argument("--port", type=int, default=8080, help="Port to run server on")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--project", type=str, help="Project name")
    parser.add_argument("--batches", type=int, help="Total number of batches")

    args = parser.parse_args()

    # Update initial state with provided info
    if args.project:
        render_state["project_name"] = args.project
    if args.batches:
        render_state["total_batches"] = args.batches

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
