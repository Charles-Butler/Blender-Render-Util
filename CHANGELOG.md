# Changelog

All notable changes to Blender Batch Render Utilities will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [5.2.1] - 2026-04-17

### Fixed

- **Post-restart frame state restoration** in `monitor.py`: server restart no longer shows
  "Frame 0" and blank statistics. On startup, `_read_existing_content()` now greps `Fra:`
  lines to find the most recent frame within the active batch range, broadcasts
  `current_frame`, `frame_time`, and `avg_frame_time` via callback (up to 10 samples for
  the average), and prints a confirmation line to the server log.

---

## [5.2.0] - 2026-04-17

### Added

- **PyInstaller Bundle** (`app/RenderManager.spec`)
  - Bundles Python runtime, FastAPI, uvicorn, pywebview, watchdog, websockets
  - Bundles pre-built React frontend (`server/frontend/dist/`)
  - Bundles `batchedFrame_render.sh` and `config.template.json`
  - Produces native `RenderManager.app` for macOS
  - `CFBundleIdentifier`: `com.renderutil.rendermanager`
  - Supports dark mode (`NSRequiresAquaSystemAppearance: False`)
- **Build Script** (`app/build.sh`)
  - Single command builds entire app: `npm run build` → PyInstaller
  - Uses `python3 -m PyInstaller` for reliable PATH-agnostic execution
- **Persistent Config Storage for Bundle**
  - Bundled app stores `config.json` in `~/Library/Application Support/RenderManager/`
  - `config_manager.py` respects `RENDER_MANAGER_CONFIG_DIR` env var set by launcher

### Fixed

- Render script path in `app.py` now uses `sys._MEIPASS` when frozen instead of
  looking for a sibling `Blender-Utilities` repo - works correctly inside `.app` bundle

---

## [5.1.0] - 2026-04-18

### Added

- **Native Desktop App Launcher** (`app/launcher.py`)
  - Starts FastAPI backend in a daemon thread on `127.0.0.1:8081`
  - Polls `/health` until server is ready (15s timeout) before opening UI
  - Opens a native OS window via PyWebView - no browser, no terminal visible to user
  - Window config: 1280×820 default, 900×600 minimum, resizable
  - Accepts `--blend-file` CLI arg (passed from Blender add-on) to pre-select blend file in config
  - Cleanly shuts down uvicorn when window is closed
- **`pywebview` added to `server/requirements.txt`**

---

## [5.0.0] - 2026-04-18

### Changed (Breaking - Architecture)

- **Frontend now served by FastAPI directly**
  - React app must be pre-built (`npm run build`) - Vite dev server no longer required at runtime
  - `server/frontend/dist/` mounted as StaticFiles at `/` after all API routes
  - Root route handler updated to serve `frontend/dist/index.html`
  - Eliminates the two-terminal startup requirement for end users
- **All frontend API calls converted to relative URLs**
  - `http://localhost:8081/api/...` → `/api/...` across App.jsx, ConfigureRender.jsx, ProgressMonitor.jsx
  - WebSocket: `ws://${hostname}:8081/ws` → `ws://${window.location.host}/ws`
  - App now works on any port without frontend changes
- **Default port changed from `8080` to `8081`**
  - Matches the port the frontend already expected
  - Startup print statements now use the actual runtime port variable

---

## [4.3.0] - 2026-04-18

### Changed

- **Project Cleanup & Reorganization**

  - Deleted `server/static/index.html` - legacy v2.3.1 HTML dashboard superseded by React frontend
  - Deleted `server/test_full_stack.sh`, `test_server.py`, `test_launch.sh`, `test_render.log` - broken/obsolete test files
  - Deleted `server/frontend/public/vite.svg`, `src/assets/react.svg` - unused Vite/React template assets
  - Moved `watch_render_progress.sh` → `legacy/` (README already marked it legacy)
  - Moved `design/README.md` → `legacy/DESIGN_NOTES.md` (pre-v3 planning doc)
  - Moved `BLEND_FILE_SELECTION.md` → `docs/` (implementation docs out of root)
  - Removed hardcoded server restart commands paste-in from README.md EOF
  - Replaced all absolute `/Users/me/...` paths in QUICKSTART.md with relative paths
  - Fixed `Blender-Utilities` path typo in QUICKSTART.md → `Blender-Render-Util`

- **Config & Dependencies**
  - Added `server/config.json` to `.gitignore` - contains machine-specific paths and runtime render state
  - Created `server/config.template.json` - clean reference template for new installs
  - Added missing `websockets` to `server/requirements.txt`
  - Updated `batchedFrame_render.sh` header from v2.3 to v4.3.0

---

## [4.2.1] - 2026-04-18

### Fixed

- **"Frame X outside batch range" error on batch transition** - `batch_name` pattern matched the same `"Now Rendering X: N - M"` log line as `batch_start` and was checked first, causing an early return that silently skipped `batch_start` for every batch after the first; `batch_start_frame`/`batch_end_frame` were never updated, making frame progress calculations negative against the stale previous batch range. Removed the redundant `batch_name` block - name and priority are already extracted inside `batch_start`.

## [4.2.0] - 2026-04-18

### Fixed

- **Overall Progress resets to 0% on new render** - `start_render` now clears all stale state (frames completed, progress, priority lists, ETAs) from the previous render before applying new render values
- **Elapsed time showing negative values** - `end_time` from a completed render was not cleared when a new render started, causing `end_time - start_time` to go negative once the new `start_time` was set; both fields are now reset on render start
- **Frontend guard** - Added `Math.max(0, ...)` to elapsed time calculation as a safety net against any future stale timestamp edge cases

---

## [4.1.0] - 2026-03-01

### Added

- **Automatic State Restoration on Server Restart**

  - Server startup loads render configuration from `config.json`
  - Automatically starts log monitor if status is "rendering"
  - Seamless recovery from server restarts during active renders
  - No manual intervention required to resume monitoring

- **Real-Time Batch Status Badges**
  - High Priority and Low Priority lists show per-batch status
  - "Rendering" badge (orange gradient) with film icon for active batch
  - "Pending" badge (blue gradient) with clock icon for queued batches

### Fixed

- Monitor correctly identifies when pre-configured batches begin rendering
- `current_batch` number updates properly when switching between batches
- Existing batch detection now sets batch number from batch metadata
- All configured batches appear in priority lists immediately on page load (not just after detection)

---

## [4.0.0] - 2026-03-01

### Added

- **Complete Render Workflow from Web UI**

  - Start render jobs directly from Configure page via API
  - AppleScript integration launches Terminal with render command
  - Automatic log file creation and monitoring activation
  - Cancel running render jobs with single button click

- **Batch Profile System**

  - Save and load batch configurations; `last` profile auto-saved on render start
  - Load Last Profile button in Frame Selection
  - API endpoints: `/api/batch-profiles`, `/api/batch-profiles/{name}` (POST/DELETE)

- **Static Configuration Storage**

  - Frame selections persisted in `config.json`
  - `current_render` object stores active render state (project, batches, status, log path)
  - Server startup automatically restores render state from config
  - Blend file browser with recent files tracking

- **Monitor Tab Access Control**

  - Monitor tab disabled when status is `idle`
  - Auto-redirect from Monitor to Configure when render completes
  - Tooltip: "Start a render to access Monitor"

- **Configure Page Live Updates**
  - Batches update in real-time via WebSocket during rendering
  - Read-only mode with status badges when render is active

### Fixed

- Circular reference issue in batch state merging
- Current batch number properly tracks when pre-configured batches begin rendering
- Low priority correctly handles both `'null'` and `'0'` values

---

## [3.2.0] - 2026-03-01

### Added

- **FontAwesome Icon System**

  - Complete migration from emojis to FontAwesome solid icons (17 unique icons)
  - Cross-platform consistency and professional appearance
  - Improved icon sizing and alignment throughout UI
  - Custom icon components with proper semantic meaning

- **Custom Branding**

  - Official Blender logo PNG (80x80px) in sidebar navigation
  - Drop shadow effect for visual depth
  - Replaced generic film icon with brand-specific imagery

- **Animated Status Indicators**

  - Rotating sync arrow (fa-arrows-rotate) during active renders (2s rotation cycle)
  - Pulsing green dot indicator for "Rendering" state (1.5s fade cycle, opacity 1→0.3→1)
  - Position-absolute pulse dot at far right of status container

- **Enhanced Mobile Navigation**
  - FontAwesome caret icons (fa-caret-left/right) for drawer toggle
  - Sleek 50px × 100px touch-optimized tap target
  - 16px rounded corners for modern appearance
  - Enhanced hover effect with subtle slide-out animation (2px translateX)
  - Active state with scale-down feedback (0.95)
  - Deeper shadow (3px→12px blur) for better depth perception

### Changed

- **Icon Updates Across UI**

  - Play button (fa-play) for Start Job instead of rocket
  - Stop sign (fa-stop) for Cancel Job
  - Level-down arrow (fa-level-down) for Low Priority batches
  - List-alt (fa-list-alt) for Batch Queue
  - Folder-open (fa-folder-open) for Project Settings and file operations
  - Check-circle (fa-check-circle) for completed states
  - Film (fa-film) for rendering/frame operations
  - Clock (fa-clock) for time-related stats and pending status
  - Bolt (fa-bolt) for High Priority batches
  - File-lines (fa-file-lines) for log file monitoring

- **Removed Elements**
  - All emoji usage replaced with FontAwesome icons
  - Target emoji (🎯) removed from "Render Order" heading
  - Text-based `>` and `<` arrows replaced with proper caret icons

---

## [3.1.0] - 2026-03-01

### Added

- **Advanced Log File Management**

  - Log file browser modal showing all renders in repository directory
  - Switch between multiple concurrent renders without server restart
  - External log file support via manual path entry
  - Automatic project name extraction from log filename
  - Real-time display of currently monitored log file path

- **Improved Time Tracking**

  - Elapsed time counter with automatic freeze on render completion
  - End time detection when all batches complete
  - Accurate final render duration display
  - Timestamp preservation for completed renders

- **Mobile Navigation Upgrade**

  - Replaced hamburger menu with side tab toggle (space-saving design)
  - Positioned at screen midpoint (50% vertical height)
  - Smooth slide-in/out drawer animation
  - Touch-optimized 40px × 80px tap target

- **API Enhancements**
  - `/api/browse-log-files` - Recursively scans renders directory
  - `/api/monitor/override` - Updates project name when switching logs
  - Sorted log file list by timestamp (newest first)
  - Extracts project name and datetime from filenames

---

## [3.0.0] - 2026-03-01

### Added

- **Web-Based Monitoring Dashboard**

  - React SPA with Vite for modern development experience
  - Real-time WebSocket updates every 2 seconds
  - Responsive design supporting desktop and mobile devices
  - Centered layout with max-width 1000px container
  - Connection status indicator (connected/disconnected)

- **FastAPI Backend Server** (`server/app.py`)

  - RESTful API endpoints: `/api/status`, `/api/queue`, `/api/stats`, `/health`
  - WebSocket endpoint `/ws` for real-time progress streaming
  - CORS middleware for frontend development
  - Efficient log parsing using grep for large files (850K+ lines)
  - Automatic render start time detection from log filename

- **Intelligent Log Monitoring** (`server/monitor.py`)

  - Timestamp parsing from log filename format `YYYY-MM-DD_HH-MM-SS`
  - Frame counting from "Append frame" lines (Blender 4.x compatibility)
  - Batch detection from "Now Rendering Scenes" and "Finished Scenes" markers
  - Priority tag parsing: `[Priority: 1]`, `[Priority: 0]`, `[Priority: null]`
  - Current batch detection based on frame range matching

- **Real-Time Progress Tracking**

  - Overall progress display (full-width)
  - Current batch progress with frame range detection
  - Statistics panel: frame time, average time, batch ETA, overall ETA, elapsed time
  - Frontend-calculated elapsed time from Unix timestamp
  - Automatic frame counting with race condition prevention

- **Multi-Device Support**
  - Network-accessible via `--host 0.0.0.0` flag
  - Dynamic WebSocket connection based on hostname
  - Access from any device on local network

### Changed

- **Priority System Upgrade**

  - Changed from `H`/`L` to numeric system: `1` (High), `0` (Low), `null` (No priority)
  - Updated `batchedFrame_render.sh` to accept `1`, `0`, or skip for priority input
  - Modified batch sorting to handle: 1 > 0 > null priority levels
  - Default priority changed from high to low for batches without explicit priority

- **UI/UX Improvements**
  - Gradient color-coded priority cards (yellow=high, blue=low, green=completed)
  - Removed scrollbars from batch lists for cleaner appearance
  - Mobile-responsive with vertical stacking of status elements
  - Full-width progress containers on desktop

### Fixed

- Race condition in frame counting during initial log scan
  - Moved polling start to after initial content read completes
  - Prevents double-counting of frames
- Status now correctly shows "rendering" when incomplete batches exist
- Elapsed time now calculates from actual render start time (from filename)
- Current batch detection now finds correct batch containing current frame
- WebSocket connection properly reconnects without page reload

### Technical

- Frontend built with React 18.3.1 + Vite 7.3.1
- Backend using FastAPI + Uvicorn with WebSocket support
- Log file monitoring with watchdog or polling fallback
- Grep-based log parsing for performance with large files

---

## [2.3.0] - 2026-02-27

### Added

- Interactive batch queue system
- Dynamic frame range input with validation
- Optional batch naming
- Priority-based queue management (H/L)
- Automatic batch sorting by priority and frame count
- Visual table summary of batches before rendering
- Path validation for Blender executable and .blend file
- Error resilience with exit code capture

### Changed

- Removed hardcoded frame ranges
- Made batch queue fully dynamic

---

## [2.2.0] - 2026-02-20

### Added

- Dual progress tracking (batch + overall)
- Pre-scanning of existing logs
- Auto-detection of active renders
- Interactive log selection
- Enhanced error detection:
  - Critical Blender errors
  - Texture size errors
  - Out of memory errors
- Batch configuration parsing
- Bash 3 compatibility for macOS

---

## [2.1.0] - 2026-02-15

### Added

- Visual progress bar for batch rendering
- Real-time display updates
- Frame completion percentage
- ETA calculations based on average frame time

---

## [1.1.0] - 2026-02-10

### Added

- Standalone monitoring script
- Basic frame tracking
- Time per frame calculation
- Manual log file input

---

## [1.0.0] - 2026-02-05

### Added

- Initial batch rendering script
- Manual frame range configuration
- Basic logging to stdout
- Timestamp-based output directories
- Audio notification on completion

---

## Types of Changes

- `Added` for new features
- `Changed` for changes in existing functionality
- `Deprecated` for soon-to-be removed features
- `Removed` for now removed features
- `Fixed` for any bug fixes
- `Security` in case of vulnerabilities
