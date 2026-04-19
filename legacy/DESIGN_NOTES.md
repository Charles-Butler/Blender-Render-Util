# Blender Render Util - Web Application Design

## Overview

Transform the shell-based monitoring into a web application for remote, cross-platform monitoring of Blender renders.

---

## Architecture

### Workflow

```
1. User runs: ./batchedFrame_render.sh
   ↓
2. Script does interactive batch setup (as current implementation)
   ↓
3. Script launches web server in background
   ↓
4. Displays: "📊 Monitor at: http://192.168.1.x:8080"
   ↓
5. Starts Blender rendering + streams to web UI
   ↓
6. Anyone on network can view real-time progress
```

### System Diagram

```
┌──────────────────────────────────────────────────────────────┐
│  batchedFrame_render.sh (Main Entry Point)                   │
│  - Interactive batch queue setup                             │
│  - Launches web server                                       │
│  - Displays monitoring URLs                                  │
│  - Executes Blender renders                                  │
└───────────────────┬──────────────────────────────────────────┘
                    │
        ┌───────────┴───────────┐
        │                       │
        ▼                       ▼
┌───────────────┐      ┌────────────────┐
│  Blender      │      │  Web Server    │
│  Rendering    │──────▶  (FastAPI)     │
│  Process      │      │  - Log parser  │
│  (background) │      │  - WebSocket   │
└───────────────┘      │  - REST API    │
                       └────────┬───────┘
                                │
                                │ WebSocket
                                │
                       ┌────────▼────────┐
                       │  Web Dashboard  │
                       │  (React/Vue)    │
                       │  - Progress UI  │
                       │  - Queue view   │
                       │  - Stats/Charts │
                       └─────────────────┘
```

---

## Project Structure

```
Blender-Render-Util/
├── batchedFrame_render.sh          # Main entry point (updated)
├── watch_render_progress.sh        # Legacy CLI monitor (deprecated)
│
├── server/                          # Python backend
│   ├── app.py                       # FastAPI application
│   ├── requirements.txt             # Python dependencies
│   ├── monitor.py                   # Log monitoring service
│   ├── websocket.py                 # WebSocket handler
│   └── static/                      # Compiled frontend assets
│       ├── index.html
│       ├── assets/
│       └── ...
│
├── web/                             # Frontend application
│   ├── src/
│   │   ├── App.jsx                  # Main dashboard component
│   │   ├── main.jsx                 # Entry point
│   │   ├── components/
│   │   │   ├── ProgressBar.jsx      # Batch & overall progress bars
│   │   │   ├── BatchQueue.jsx       # Queue visualization
│   │   │   ├── Stats.jsx            # Time estimates, frame counts
│   │   │   ├── ErrorDisplay.jsx     # Error messages
│   │   │   └── StatusHeader.jsx     # Project info header
│   │   ├── hooks/
│   │   │   └── useWebSocket.js      # WebSocket connection hook
│   │   └── styles/
│   │       └── main.css
│   ├── package.json
│   ├── vite.config.js
│   └── index.html
│
├── design/                          # Design documentation
│   ├── README.md                    # This file
│   ├── wireframes/                  # UI mockups
│   └── api-spec.md                  # API documentation
│
└── README.md                        # Main project README
```

---

## Technology Stack

### Backend
- **Language**: Python 3.9+
- **Framework**: FastAPI
  - Fast, modern, async support
  - WebSocket built-in
  - Auto-generated API docs
- **Dependencies**:
  - `fastapi` - Web framework
  - `uvicorn` - ASGI server
  - `websockets` - WebSocket support
  - `watchdog` - File monitoring

### Frontend
- **Framework**: React (with Vite)
  - Fast dev server
  - Modern tooling
  - Component-based
- **UI Library**: TailwindCSS or Material-UI
- **State Management**: React hooks + Context
- **Real-time**: WebSocket API

### Alternative Frontend Options
- **Vue.js** - Simpler learning curve
- **Svelte** - Lightweight, fast
- **Vanilla JS** - No framework overhead

---

## Core Features

### Phase 1: MVP (Minimum Viable Product)

1. **Web Server Integration**
   - Launch FastAPI server from bash script
   - Detect local IP address
   - Display monitoring URLs

2. **Real-time Progress Monitoring**
   - Live batch progress bar
   - Overall render progress
   - Current frame info
   - Time estimates (batch ETA, overall ETA)

3. **Queue Visualization**
   - Display all batches in queue
   - Show current batch
   - Priority indicators
   - Frame counts

4. **Basic Stats**
   - Frames completed
   - Average time per frame
   - Elapsed time
   - Estimated completion

### Phase 2: Enhanced Features

5. **Error Detection & Display**
   - Parse Blender errors
   - Texture size warnings
   - Memory errors
   - Visual error indicators

6. **Historical Data**
   - Previous render sessions
   - Performance metrics
   - Frame time graphs

7. **Mobile Responsive**
   - Optimize for phone/tablet
   - Touch-friendly controls

### Phase 3: Advanced Features

8. **Multi-User Support**
   - Multiple simultaneous viewers
   - No authentication needed (local network)

9. **Notifications**
   - Browser notifications on completion
   - Error alerts
   - Batch completion notices

10. **Control Panel**
    - Pause/resume rendering
    - Cancel batches
    - Adjust priorities

---

## API Design

### REST Endpoints

```
GET  /api/status          # Current render status
GET  /api/queue           # Batch queue information
GET  /api/stats           # Statistics and metrics
GET  /api/logs            # Recent log entries
POST /api/control/pause   # Pause rendering
POST /api/control/resume  # Resume rendering
POST /api/control/cancel  # Cancel current batch
```

### WebSocket Events

**Server → Client:**
```javascript
{
  "type": "progress",
  "data": {
    "currentFrame": 150,
    "batchProgress": 45,
    "overallProgress": 23,
    "eta": "01:23:45",
    "avgFrameTime": "00:01:02"
  }
}

{
  "type": "batch_complete",
  "data": {
    "batchNumber": 2,
    "batchName": "Hero Shot",
    "totalTime": "00:45:30"
  }
}

{
  "type": "error",
  "data": {
    "message": "Texture size exceeds maximum",
    "severity": "warning"
  }
}
```

---

## Modified batchedFrame_render.sh Integration

### New Flow

```bash
#!/bin/bash

# ... existing batch setup code ...

# After batch queue is finalized and confirmed:

echo "🚀 Starting web monitoring server..."

# Detect local IP address
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    LOCAL_IP=$(ipconfig getifaddr en0 2>/dev/null || ipconfig getifaddr en1 2>/dev/null)
else
    # Linux/Windows WSL
    LOCAL_IP=$(hostname -I | awk '{print $1}')
fi

# Fallback to localhost
if [ -z "$LOCAL_IP" ]; then
    LOCAL_IP="127.0.0.1"
fi

# Export data for Python server
export PROJECT_NAME="$PROJECT_NAME"
export LOGFILE="$LOGFILE"
export BATCH_COUNT="$BATCH_COUNT"
export TOTAL_FRAMES="$TOTAL_FRAMES"

# Start Python web server in background
python3 server/app.py --logfile "$LOGFILE" --port 8080 &
SERVER_PID=$!

# Wait for server to start
sleep 2

echo "================================================================"
echo "📊 MONITOR RENDER PROGRESS:"
echo ""
echo "   Local:   http://localhost:8080"
echo "   Network: http://$LOCAL_IP:8080"
echo ""
echo "   Share the network URL with others to monitor remotely!"
echo "================================================================"
echo ""

# Existing rendering code continues...
# ... Blender batch processing ...

# On completion, cleanup
kill $SERVER_PID 2>/dev/null
```

---

## UI Design Concepts

### Dashboard Layout

```
┌─────────────────────────────────────────────────────────────┐
│  🎬 Blender Render Monitor - Project: MyAnimation          │
│  ════════════════════════════════════════════════════════   │
│                                                             │
│  Current Batch: Intro (Batch 1/3) [Priority: H]            │
│  ┌────────────────────────────────────────────────────┐    │
│  │  Frame 145 / 200                                   │    │
│  │  [████████████████░░░░░░░░░░░░] 72%              │    │
│  └────────────────────────────────────────────────────┘    │
│                                                             │
│  Overall Progress                                           │
│  ┌────────────────────────────────────────────────────┐    │
│  │  145 / 450 frames                                  │    │
│  │  [████████░░░░░░░░░░░░░░░░░░░░] 32%              │    │
│  └────────────────────────────────────────────────────┘    │
│                                                             │
│  ┌─────────────────┬──────────────────┬─────────────────┐  │
│  │ ⏱️ Frame Time   │ 📈 Avg/Frame     │ ⏳ ETA         │  │
│  │ 00:00:58        │ 00:01:02         │ 01:23:45       │  │
│  └─────────────────┴──────────────────┴─────────────────┘  │
│                                                             │
│  Batch Queue                                                │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ ✓ Batch 1: Quick Test [H]   (11 frames)  COMPLETE  │   │
│  │ → Batch 2: Intro [H]         (200 frames) ACTIVE   │   │
│  │   Batch 3: Main Scene [L]    (239 frames) PENDING  │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

### Mobile Layout

```
┌───────────────────────┐
│ 🎬 MyAnimation        │
│ ═══════════════════   │
│                       │
│ Batch 1/3 [H]         │
│ Frame 145/200         │
│ [████████░░] 72%      │
│                       │
│ Overall               │
│ [███░░░░░░░] 32%      │
│                       │
│ ETA: 01:23:45         │
│ Avg: 00:01:02         │
│                       │
│ Queue:                │
│ ✓ Quick Test          │
│ → Intro (Active)      │
│ • Main Scene          │
└───────────────────────┘
```

---

## Development Phases

### Phase 1: Foundation (Week 1)
- [ ] Create server directory structure
- [ ] Set up FastAPI basic server
- [ ] Implement log file monitoring
- [ ] Create simple HTML dashboard (no framework)
- [ ] Test WebSocket connection
- [ ] Integrate server launch into bash script

### Phase 2: Core Features (Week 2)
- [ ] Build React/Vue frontend
- [ ] Implement progress bars
- [ ] Add batch queue visualization
- [ ] Real-time updates via WebSocket
- [ ] Stats display
- [ ] Mobile responsive design

### Phase 3: Polish (Week 3)
- [ ] Error detection and display
- [ ] Browser notifications
- [ ] Performance optimization
- [ ] Cross-browser testing
- [ ] Documentation

---

## Deployment Considerations

### Local Network Access
- Server binds to `0.0.0.0:8080` (all interfaces)
- Accessible from any device on same network
- No firewall configuration needed (local only)

### Future: Remote Access
- Port forwarding
- ngrok/tunneling services
- Cloud deployment (AWS, Heroku)
- Authentication layer

---

## Success Metrics

1. **Ease of Use**
   - One-command launch
   - Auto-discovery of monitoring URL
   - No manual configuration

2. **Real-time Performance**
   - Updates within 1 second
   - No lag on progress bars
   - Smooth animations

3. **Accessibility**
   - Works on all devices (desktop, tablet, phone)
   - Cross-browser compatible
   - Intuitive UI requiring no documentation

4. **Reliability**
   - Handles server crashes gracefully
   - Reconnects WebSocket automatically
   - Persists data through page refreshes

---

## Next Steps

1. **Prototype FastAPI Server**
   - Basic endpoints
   - Log file monitoring
   - WebSocket connection

2. **Simple HTML Dashboard**
   - Prove concept with vanilla JS
   - Test real-time updates

3. **Choose Frontend Framework**
   - React vs Vue vs Svelte
   - Based on complexity needs

4. **Integration Testing**
   - End-to-end workflow
   - Network accessibility
   - Error handling

---

## Questions to Resolve

- [ ] Should we include authentication for remote access?
- [ ] Persist render history to database or JSON files?
- [ ] Support multiple concurrent renders?
- [ ] Include video preview of rendered frames?
- [ ] Add render farm support from the start?
