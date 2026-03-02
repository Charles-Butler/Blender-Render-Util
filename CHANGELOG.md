# Changelog

All notable changes to Blender Batch Render Utilities will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
