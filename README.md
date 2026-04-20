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

### Option A: Web-Based Workflow (Recommended)

**1. Start the Backend Server**

```bash
cd server
python3 app.py --port 8081
```

**2. Start the Frontend Dashboard**

```bash
cd server/frontend
npm install
npm run dev -- --host 0.0.0.0
```

**3. Access the Dashboard**

- **Local:** http://localhost:5173/
- **Network:** http://YOUR_IP:5173/ (accessible from other devices)

**4. Configure and Start Render**

1. Navigate to the **Configure** page
2. Enter project name and select blend file
3. Add batches using the **+** button (set frame ranges and priority)
4. Review the render order preview
5. Click **🚀 Start Job** to begin rendering
6. Switch to **Monitor** page to watch real-time progress

### Option B: CLI-Only Workflow (Legacy)

**1. Start a Render Job**

```bash
./batchedFrame_render.sh
```

**2. Monitor Progress (Optional)**

Terminal-based:

```bash
./watch_render_progress.sh /path/to/render_log.txt
```

Or start web monitoring:

```bash
cd server
python3 app.py --port 8081 --logfile /path/to/render_log.txt --project "ProjectName" --batches 8 --frames 527
```

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

### v3.0 - Web-Based Configuration & Real-Time Monitoring System

- **Two-Page React Application**:
  - **Configure Page**: Full batch render job setup interface
    - Interactive project settings (name, blend file selection)
    - Frame selection with +/- controls for adding/removing batches
    - Live render order preview showing sorted batch execution
    - Full batch queue table with status tracking
    - Dual action buttons: Start Job / Cancel Job
    - Read-only mode when monitoring active renders
  - **Monitor Page**: Real-time progress dashboard
    - Live WebSocket updates every 2 seconds
    - Overall and batch progress bars
    - Statistics panel with ETAs and timing metrics
    - Priority-based batch lists (high/low/completed)
- **Modern UI/UX**:
  - Sidebar navigation (desktop) with hamburger drawer (tablet/mobile ≤1024px)
  - Responsive 2-column layout (1fr × 1.5fr grid)
  - Centered content with 1200px max-width
  - Version footer in navigation menu
  - Gradient color-coded priority badges (yellow=high, blue=low)
- **Configuration Management**:
  - JSON-based persistent settings (`config.json`)
  - Recent blend files tracking (max 10)
  - Last used project settings
  - Python ConfigManager with dot-notation access
- **Simplified Priority System**:
  - Binary priority: High (1) or Low (null/default)
  - High priority batches render first, then sorted by frame count
  - Color-coded badges for instant recognition
- **FastAPI Backend**:
  - RESTful API: `/api/config`, `/api/blend-files`, `/api/render/start`, `/api/render/cancel`
  - WebSocket endpoint for real-time updates
  - Efficient log parsing with grep for large files (850K+ lines)
  - Auto-detection of render start time from log filename
- **Multi-Device Support**:
  - Access from any device on local network
  - Responsive design for desktop, tablet, and mobile
  - Network-accessible Vite dev server with `--host 0.0.0.0`
- **Intelligent Monitoring**:
  - Automatic timestamp parsing from log filename (YYYY-MM-DD_HH-MM-SS)
  - Frame counting from "Append frame" lines (Blender 4.x)
  - Batch detection from "Now Rendering Scenes" and "Finished Scenes" markers
  - Priority tag parsing: `[Priority: 1]` or `[Priority: null]`
  - Status tracking per batch: Pending → Rendering → Completed

### v3.1 - Enhanced Monitoring & Mobile UX

- **Advanced Log File Management**:
  - Log file browser modal showing all renders in repo directory
  - Switch between multiple concurrent renders without restarting server
  - External log file support via manual path entry
  - Automatic project name extraction from log filename
  - Real-time display of currently monitored log file path
- **Improved Time Tracking**:
  - Elapsed time counter with automatic freeze on render completion
  - End time detection when all batches complete
  - Accurate final render duration display
- **Mobile Navigation Upgrade**:
  - Replaced hamburger menu with side tab toggle (saves screen space)
  - Tab shows `>` when closed, `<` when open
  - Positioned at screen midpoint (50% height)
  - Smooth slide-in/out drawer animation
  - Touch-optimized 40px × 80px tap target
- **API Enhancements**:
  - `/api/browse-log-files` - Scans renders directory recursively
  - `/api/monitor/override` - Updates project name when switching logs
  - Returns sorted list by timestamp (newest first)
  - Extracts project name and datetime from filenames

### v3.2 - Professional Icon System & UI Polish

- **FontAwesome Integration**:
  - Complete migration from emojis to FontAwesome solid icons
  - Cross-platform consistency and professional appearance
  - 17 unique icons replaced across all components
  - Improved icon sizing and alignment throughout UI
- **Custom Branding**:
  - Blender official logo PNG (80x80px) in sidebar navigation
  - Drop shadow effect for logo depth
  - Removed generic film icon
- **Animated Status Indicators**:
  - Rotating sync arrow (fa-arrows-rotate) during active renders (2s rotation)
  - Pulsing green dot indicator for "Rendering" state (1.5s fade cycle)
  - Position-absolute dot at far right of status container for visual separation
- **Enhanced Mobile Tab**:
  - FontAwesome caret icons (fa-caret-left/right) for open/close states
  - Sleek 50px × 100px touch target with 16px rounded corners
  - Enhanced hover effect with subtle slide-out animation (2px translateX)
  - Active state with scale-down feedback (0.95)
  - Deeper shadow for better depth perception
- **Icon Updates**:
  - Play button (fa-play) for Start Job instead of rocket
  - Stop sign (fa-stop) for Cancel Job
  - Level-down arrow (fa-level-down) for Low Priority batches
  - List-alt (fa-list-alt) for Batch Queue
  - Folder-open (fa-folder-open) for Project Settings and file operations
  - Check-circle (fa-check-circle) for completed states
  - Film (fa-film) for rendering/frame operations
  - Clock (fa-clock) for time-related stats and pending status
  - Removed target emoji from Render Order heading

### v4.0 - Full Web-Based Render Configuration & Execution

- **Complete Render Workflow from Web UI**:
  - Web-based batch configuration replaces manual script editing
  - Start render jobs directly from Configure page via API
  - AppleScript integration launches Terminal with render command
  - Automatic log file creation and monitoring activation
  - Cancel running render jobs with single button click
- **Batch Profile System**:
  - Save and load batch configurations with `last` profile auto-saved on render start
  - Load Last Profile button with history icon in Frame Selection
  - API endpoints: `/api/batch-profiles`, `/api/batch-profiles/{name}`, POST/DELETE support
  - Stores batch count, total frames, and timestamp metadata
- **Static Configuration Storage**:
  - All frame selections persisted in `config.json` for instant access
  - `current_render` object stores active render state (project, batches, status, log path)
  - Server startup automatically restores render state from config
  - 5-second delay before switching to Monitor page (ensures log file exists)
  - Blend file browser with recent files tracking
- **Enhanced Batch State Merging**:
  - `_merge_batch_states()` function combines configured batches with monitor-detected batches
  - Populates high_priority_list, low_priority_list, and completed_list from configured batches
  - Low priority includes both `'null'` and `'0'` values
  - Real-time WebSocket updates reflect all queued batches even before they start rendering
- **Improved Batch Transition Detection**:
  - Monitor correctly updates `current_batch` number when existing batches start rendering
  - Batch completion moves batches to completed list and triggers next batch detection
  - Fixed circular reference issue in batch state merging
  - Current batch number properly tracks when pre-configured batches begin
- **Monitor Tab Access Control**:
  - Monitor tab disabled when status is `idle`
  - Auto-redirect from Monitor to Configure when render completes
  - Tooltip guidance: "Start a render to access Monitor"
- **Configure Page Live Updates**:
  - Batches update in real-time via WebSocket during rendering
  - Shows batch status (completed, rendering, pending) on Configure page
  - Read-only mode displays active render configuration with status badges
  - Dual-mode interface: editable when idle, read-only when rendering

### v4.1 - Enhanced Monitoring & Status Visibility

- **Automatic State Restoration on Server Restart**:
  - Server startup event loads render configuration from `config.json`
  - Automatically starts log monitor if status is "rendering"
  - Seamless recovery from server restarts during active renders
  - No manual intervention required to resume monitoring
- **Real-Time Batch Status Badges**:
  - High Priority and Low Priority lists show status for each batch
  - "Rendering" badge (orange gradient) with film icon for active batch
  - "Pending" badge (blue gradient) with clock icon for queued batches
  - Instant visual feedback of which batch is currently rendering
- **Fixed Batch Transition Tracking**:
  - Monitor correctly identifies when pre-configured batches begin rendering
  - `current_batch` number updates properly when switching between batches
  - Existing batch detection now sets batch number from batch metadata
  - Eliminates incorrect batch number display during transitions
- **Improved Priority List Population**:
  - All configured batches appear in priority lists immediately on page load
  - Batches visible before they start rendering (not just after detection)
  - Merge function rebuilds priority lists from configured batches
  - Complete queue visibility from the start of the render job

### v4.2 - Bug Fixes

- **Overall Progress & Elapsed Time Reset on New Render**:
  - `start_render` now clears all stale state from the previous render (frames completed, overall progress, priority lists, ETAs, start/end time) before applying new render values
  - Fixes overall progress showing 100% when configuring a new render after a completed one
  - Fixes elapsed time displaying negative values (e.g. `-630:-53:-17`) caused by stale `end_time` surviving into the new render session
  - Frontend guard added (`Math.max(0, ...)`) as a safety net against future stale timestamp edge cases
- **"Frame X outside batch range" error on batch transition**:
  - `batch_name` regex matched the same log line as `batch_start` and was evaluated first, silently skipping `batch_start` for every batch after the first
  - `batch_start_frame`/`batch_end_frame` were never updated on batch transitions, causing negative batch progress and the spurious "outside batch range" warning
  - Removed the redundant `batch_name` early-return block - name and priority extraction already handled inside `batch_start`

### v4.3 - Project Cleanup & Reorganization

- **Removed Legacy & Redundant Files**:
  - `server/static/index.html` (v2.3.1 HTML dashboard - replaced by React frontend)
  - Broken test files: `test_full_stack.sh`, `test_server.py`, `test_launch.sh`, `test_render.log`
  - Unused template assets: `vite.svg`, `react.svg`
- **Reorganized Project Structure**:
  - `watch_render_progress.sh` → `legacy/` (terminal monitor superseded by web dashboard)
  - `design/README.md` → `legacy/DESIGN_NOTES.md`
  - `BLEND_FILE_SELECTION.md` → `docs/`
- **Config & Portability**:
  - `server/config.json` added to `.gitignore` (contains machine-specific runtime state)
  - `server/config.template.json` added for new installs
  - `websockets` added to `requirements.txt`
  - All hardcoded paths removed from `QUICKSTART.md`

### v5.0 - Self-Contained Server Architecture

- **Frontend served by FastAPI directly**:
  - React app pre-built via `npm run build` - no Vite dev server at runtime
  - `frontend/dist/` mounted as static files, eliminating the two-terminal startup
  - Single command to run the full app: `python3 app.py`
- **Relative API URLs throughout frontend**:
  - All `http://localhost:8081/api/...` replaced with `/api/...`
  - WebSocket uses `window.location.host` - works on any port or hostname
  - Foundation for PyWebView packaging (Phase 2)
- **Default port unified to `8081`**

### v5.1 - Native Desktop App Launcher

- **`app/launcher.py`** - Native desktop window via PyWebView:
  - Starts FastAPI backend in a daemon thread, no terminal visible to user
  - Polls `/health` before opening UI (15s timeout)
  - Native OS window at 1280×820, resizable, no browser chrome
  - Accepts `--blend-file` arg from Blender add-on to pre-select blend file
  - Clean shutdown when window is closed
- **`pywebview` added to requirements**

### v5.3.0 - Help Page, App Icon & Reconnect Flow _(Current)_

- Help & Support page in the nav sidebar — troubleshooting, changelog, GitHub issues link
- Custom app icon in macOS dock and app switcher
- Monitor tab always accessible — idle state shows a log picker to reconnect to a running render
- Fixed watchdog crash on startup (double monitor registration)
- Fixed overall progress showing wrong denominator when manually selecting a log

### v5.2.1 - Post-Restart State Restoration

- Fixed "Frame 0 / blank statistics" bug after server restart
- `monitor.py` now greps `Fra:` lines on startup to restore `current_frame`,
  `frame_time`, and `avg_frame_time` for the active batch

### v5.2 - PyInstaller macOS Bundle

- **`app/RenderManager.spec`** - PyInstaller bundle definition:
  - Packages Python runtime, all dependencies, and pre-built React frontend
  - Produces a standalone `RenderManager.app` - no Python, Node, or terminal required
  - Persistent config stored in `~/Library/Application Support/RenderManager/`
  - Dark mode support, proper macOS bundle metadata
- **`app/build.sh`** - single command builds the full app
- Render script path fixed for bundle mode (`sys._MEIPASS` when frozen)

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
