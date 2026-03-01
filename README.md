# Blender Batch Render Utilities

A comprehensive batch rendering system for Blender with real-time web-based monitoring, priority queue management, and accurate progress tracking.

## Overview

These utilities streamline the Blender rendering workflow by providing:

- **Automated batch rendering** with priority-based queue management
- **Real-time web dashboard** with live WebSocket updates
- **Accurate time estimates** for batch and overall completion
- **Multi-device monitoring** - view progress from any device on your network
- **Error detection** and comprehensive logging

---

## Quick Start

### 1. Start a Render Job

```bash
./batchedFrame_render.sh
```

### 2. Start the Web Monitoring Server

```bash
cd server
python3 app.py --port 8081 --logfile /path/to/render_log.txt --project "ProjectName" --batches 8 --frames 527
```

### 3. Start the Frontend Dashboard

```bash
cd server/frontend
npm install
npm run dev -- --host 0.0.0.0
```

### 4. Access the Dashboard

- **Local:** http://localhost:5173/
- **Network:** http://YOUR_IP:5173/ (accessible from other devices)

---

## Scripts

### 1. `batchedFrame_render.sh` - Batch Render Orchestrator

Executes multiple Blender rendering batches with automatic logging and organization.

**Features:**

- Interactive project name prompt
- **Dynamic batch queue creation**
  - User inputs start/end frames for each batch
  - Optional batch naming
  - Priority assignment (High/Low)
- **Intelligent batch sorting**
  - High priority batches render first
  - Within priority groups: smallest batches first
- Timestamp-based output directories
- Automatic log file creation
- Path validation (Blender executable and .blend file)
- Audio notification on completion

**Usage:**

```bash
./batchedFrame_render.sh
```

**Interactive Workflow:**

1. Enter project name
2. For each batch, provide:
   - Start frame
   - End frame (inclusive)
   - Batch name (optional)
   - Priority: 1 (High), 0 (Low), or skip for no priority
3. Type `done` when finished adding batches
4. Review sorted queue summary
5. Confirm to start rendering

**Example:**

```
Enter Project Name: MyAnimation

Batch #1
  Start Frame: 100
  End Frame: 200
  Batch Name: Intro
  Priority (H=High, L=Low) [H]: H
  ✅ Added: Intro [Priority: H] (Frames 100-200, 101 frames)

Batch #2
  Start Frame: 500
  End Frame: 800
  Batch Name: Main Scene
  Priority (H=High, L=Low) [H]: L
  ✅ Added: Main Scene [Priority: L] (Frames 500-800, 301 frames)

Start Frame: done

[Queue Summary Table]
Start rendering? (Y/n): Y
```

**Output Structure:**

```
./renders/
└── {PROJECT_NAME}_{TIMESTAMP}/
    └── {PROJECT_NAME}_{TIMESTAMP}_render_log.txt
```

---

### 2. `server/app.py` - FastAPI Web Monitoring Server

Real-time web server that provides REST API and WebSocket endpoints for monitoring render progress.

**Features:**

- RESTful API endpoints: `/api/status`, `/api/queue`, `/api/stats`
- WebSocket endpoint: `/ws` for real-time updates
- Automatic log file monitoring with efficient grep-based parsing
- CORS enabled for frontend development
- Health check endpoint: `/health`

**Usage:**

```bash
python3 app.py --port 8081 \
  --logfile /path/to/render_log.txt \
  --project "ProjectName" \
  --batches 8 \
  --frames 527
```

**Arguments:**

- `--logfile`: Path to the render log file
- `--port`: Server port (default: 8080)
- `--host`: Host to bind to (default: 0.0.0.0)
- `--project`: Project name
- `--batches`: Total number of batches
- `--frames`: Total number of frames

---

### 3. `server/frontend/` - React Web Dashboard

Modern web-based dashboard for monitoring render progress in real-time.

**Features:**

- Real-time WebSocket updates every 2 seconds
- Responsive design (desktop and mobile)
- Progress bars for overall and current batch
- Statistics panel with ETA calculations
- Priority-based batch lists (high/low/completed)
- Connection status indicator

**Development:**

```bash
cd server/frontend
npm install
npm run dev -- --host 0.0.0.0
```

**Production Build:**

```bash
npm run build
```

---

### 4. `watch_render_progress.sh` - Terminal Progress Monitor (Legacy)

Terminal-based monitoring script that tracks rendering progress with visual feedback.

**Usage Options:**

**Option 1: Pipe from active render**

```bash
./batchedFrame_render.sh | tee >(./watch_render_progress.sh)
```

**Option 2: Monitor existing log**

```bash
tail -f ./renders/PROJECT_NAME/log_file.txt | ./watch_render_progress.sh
```

**Option 3: Provide log file as argument**

```bash
./watch_render_progress.sh /path/to/render_log.txt
```

**Option 4: Auto-detect active renders**

```bash
./watch_render_progress.sh
```

The script will automatically detect running Blender processes and offer to monitor the most recent log.

---

## Version History

### v1.0 - Initial Batch Renderer

- Basic batch rendering script
- Manual frame range configuration
- Simple logging to stdout

### v1.1 - Monitoring Script

- Standalone monitoring script introduced
- Basic frame tracking
- Time per frame calculation
- Manual log file input required

### v2.1 - Visual Progress Bar

- Added visual progress bar for batch rendering
- Real-time display updates
- Frame completion percentage
- ETA calculations based on average frame time

### v2.2 - Dual Progress Tracking

- **Batch Progress Bar**: Tracks current batch completion
- **Overall Progress Bar**: Tracks total render progress across all batches
- Pre-scanning of existing logs for accurate resume tracking
- Auto-detection of active renders
- Interactive log selection
- Enhanced error detection:
  - Critical Blender errors
  - Texture size errors
  - Out of memory errors
- Batch configuration parsing from render script
- Bash 3 compatibility for macOS

### v2.3 - Interactive Batch Queue System

- **Interactive Batch Input**: User defines frame ranges dynamically
  - Start/end frame validation
  - Optional batch naming
  - Input validation with error handling
- **Priority-Based Queue Management**:
  - High (H) or Low (L) priority assignment per batch
  - Automatic sorting: High priority first, then by frame count (smallest first)
  - Optimizes for quick wins on important batches
- **Enhanced Queue Summary**:
  - Visual table showing all batches with priorities
  - Total batch and frame count
  - Confirmation before rendering starts
- **Path Validation**: Checks for Blender executable and .blend file before starting
- **Error Resilience**: Captures exit codes and continues on batch failures

### v3.0 - Web-Based Real-Time Monitoring System _(Current)_

- **React-Based Web Dashboard**:
  - Modern single-page application (SPA) with Vite + React
  - Real-time updates via WebSocket
  - Responsive design for desktop and mobile
  - Centered layout with max-width 1000px container
- **FastAPI Backend Server**:
  - RESTful API endpoints for status, queue, and statistics
  - WebSocket support for live progress updates
  - Efficient log parsing with grep for large files (850K+ lines)
  - Auto-detection of render start time from log filename
- **Priority System Upgrade**:
  - Numeric priority system: 1 (High), 0 (Low), null (No priority)
  - Smart default behavior: batches without priority tagged as low priority
  - Visual distinction in dashboard for high/low/completed batches
- **Advanced Progress Tracking**:
  - Overall progress (full-width display)
  - Current batch progress with frame range detection
  - Statistics panel: frame time, average time, batch ETA, overall ETA, elapsed time
  - Real-time elapsed time calculation from render start timestamp
- **Multi-Device Support**:
  - Access dashboard from any device on local network
  - Dynamic WebSocket connection based on hostname
  - Network-accessible Vite dev server with `--host 0.0.0.0`
- **Intelligent Log Monitoring**:
  - Automatic timestamp parsing from log filename (YYYY-MM-DD_HH-MM-SS)
  - Frame counting from "Append frame" lines (Blender 4.x)
  - Batch detection from "Now Rendering Scenes" and "Finished Scenes" markers
  - Priority tag parsing: `[Priority: 1]`, `[Priority: 0]`, or `[Priority: null]`
- **Enhanced UI/UX**:
  - Connection status indicator
  - Gradient color-coded priority cards (yellow=high, blue=low, green=completed)
  - Mobile-responsive with vertical stacking
  - No scrollbars on batch lists for cleaner appearance

---

## Features Breakdown

### Real-Time Progress Display

```
┌────────────────────────────────────────────────────────────────┐
│ 🎬 BATCH #1: Frame 650/672
│ [████████████████████████████████░░░░░░░░] 85%
│
│ 🌍 OVERALL: 450 / 527 frames
│ [██████████████████████████████░░░░░░░░░░] 85%
├────────────────────────────────────────────────────────────────┤
│ ⏱️  Frame Time:     00:00:58
│ 📈 Avg/Frame:      00:01:02 (62.5s)
│ ⏳ Batch ETA:      00:22:44
│ 🌍 Overall ETA:    01:19:50
│ 🕐 Batch Time:     00:53:30
│ 🌐 Total Time:     07:45:00
│ 🎯 Blender Est:    00:08:07 (per frame)
└────────────────────────────────────────────────────────────────┘
```

### Error Detection

The monitoring script automatically detects and highlights:

- **Critical Blender errors** (render failures, quit events)
- **Texture size errors** (exceeds 16384x16384)
- **Out of memory errors** (insufficient RAM)

### Batch Queue System

**Priority-Based Sorting:**

Batches are automatically sorted by:

1. **Priority**: High (H) batches render before Low (L) batches
2. **Frame Count**: Within same priority, smaller batches render first

This optimization ensures:

- Quick completion of high-priority content
- Early feedback on important scenes
- Efficient use of rendering time

**Example Queue:**

| Order | Batch Name    | Priority | Frame Range | Frames | Rationale               |
| ----- | ------------- | -------- | ----------- | ------ | ----------------------- |
| 1     | Quick Test    | H        | 100-110     | 11     | High priority, smallest |
| 2     | Hero Shot     | H        | 500-650     | 151    | High priority, larger   |
| 3     | BG Elements   | L        | 50-100      | 51     | Low priority, smallest  |
| 4     | Full Sequence | L        | 1000-1500   | 501    | Low priority, largest   |

**Interactive Input:**

- No hardcoded frame ranges
- Fully dynamic queue creation
- Add as many batches as needed
- Cancel or finish at any time

---

## Requirements

### Batch Rendering

- **macOS** (Bash 3+ compatible)
- **Blender** installed at `/Applications/Blender.app/`
- **bc** (basic calculator - pre-installed on macOS)

### Web Monitoring Server

- **Python 3.9+**
- **FastAPI** - `pip install fastapi`
- **Uvicorn** - `pip install uvicorn`
- **WebSockets** - `pip install websockets`

### Frontend Dashboard

- **Node.js 16+**
- **npm** (comes with Node.js)
- **Vite** and **React** (installed via `npm install`)

---

## Configuration

### Changing Blender File Path

Update line 30 in `batchedFrame_render.sh`:

```bash
BLEND_FILE="/path/to/your/file.blend"
```

### Changing Blender Executable Path

Update line 31 in `batchedFrame_render.sh`:

```bash
BLENDER_PATH="/Applications/Blender.app/Contents/MacOS/Blender"
```

---

## Tips & Best Practices

1. **Run in parallel for best experience:**

   ```bash
   ./batchedFrame_render.sh | tee >(./watch_render_progress.sh)
   ```

2. **Monitor long-running renders:** The script can be attached to existing renders mid-process

3. **Pre-scan existing logs:** When resuming monitoring, the script automatically counts completed frames

4. **Check for active renders:** Run `./watch_render_progress.sh` without arguments to auto-detect

---

## Troubleshooting

**No render logs found:**

- Ensure renders are outputting to `./renders/` directory
- Check that log files follow the naming pattern `*_render_log.txt`

**Progress not updating:**

- Verify Blender output contains `Fra:` lines with timing info
- Check log file is being written in real-time

**Incorrect overall progress:**

- Ensure batch ranges in `batchedFrame_render.sh` match actual render jobs
- Re-run with fresh log (pre-scan may count duplicate frames)

---

## License

MIT

---

## Git Workflow

This repository follows a structured branching model for development and releases:

```
feature/* → develop → release/* → main → (back-merge to) develop
```

### Branch Structure

- **`main`** - Production/stable releases only (protected)
- **`develop`** - Default branch for ongoing development
- **`feature/*`** - Individual feature development branches
- **`release/*`** - Release preparation branches

### Workflow

**1. Feature Development:**

```bash
git checkout develop
git checkout -b feature/feature-name
# ... make changes ...
git add .
git commit -m "Add feature description"
```

**2. Merge Features into Develop:**

```bash
git checkout develop
git merge feature/feature-name
git push origin develop
```

**3. Create Release Branch:**

```bash
git checkout develop
git checkout -b release/v2.3
# ... final testing and version updates ...
git commit -m "Prepare release v2.3"
```

**4. Merge to Production (main):**

```bash
git checkout main
git merge release/v2.3
git tag v2.3
git push origin main --tags
```

**5. Back-merge to Develop:**

```bash
git checkout develop
git merge main
git push origin develop
```

---

## Future Enhancements

- [ ] Configuration file for paths and defaults
- [ ] Support for multiple .blend files in one session
- [ ] Save/load batch queue presets
- [ ] Email/SMS notifications on completion
- [x] ~~Web dashboard for remote monitoring~~ ✅ Completed in v3.0
- [ ] GPU vs CPU render detection
- [ ] Render farm distribution support
- [ ] Resume failed batches from queue
- [ ] Export queue summary as CSV/JSON
- [ ] Parallel batch rendering support
- [ ] Production build deployment for frontend
- [ ] Authentication/password protection for web dashboard
- [ ] Frame preview thumbnails in dashboard
- [ ] Pause/resume batch rendering
- [ ] Historical render statistics and analytics

⏺ Here are the commands to restart both servers:

Backend Server (port 8081):
cd /Users/me/Podcast/3D-Animation/Repos/Blender-Render-Util/server && python3 app.py --port 8081 --logfile
/Users/me/Podcast/3D-Animation/Repos/renders/005_TOR_RER_2026-02-27_18-07-23/005_TOR_RER_2026-02-27_18-07-23_render_log.txt --project
"005_TOR_RER" --batches 8 --frames 527 > /tmp/server.log 2>&1 &

Frontend Server (port 5173):
cd /Users/me/Podcast/3D-Animation/Repos/Blender-Render-Util/server/frontend && npm run dev -- --host 0.0.0.0 > /tmp/vite.log 2>&1 &

Then access the dashboard at:

- Local: http://localhost:5173/
- Network: http://192.168.0.147:5173/
