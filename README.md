# Blender Batch Render Utilities

A set of Bash scripts for orchestrating and monitoring Blender batch rendering jobs with real-time progress tracking and ETA estimates.

## Overview

These utilities streamline the Blender rendering workflow by providing:
- **Automated batch rendering** with organized output
- **Real-time progress monitoring** with visual progress bars
- **Accurate time estimates** for batch and overall completion
- **Error detection** and logging

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
   - Priority: H (High) or L (Low) - defaults to High
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

### 2. `watch_render_progress.sh` - Render Progress Monitor

Real-time monitoring script that tracks rendering progress with visual feedback and time estimates.

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

### v2.3 - Interactive Batch Queue System *(Current)*
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

| Order | Batch Name    | Priority | Frame Range | Frames | Rationale                      |
|-------|---------------|----------|-------------|--------|--------------------------------|
| 1     | Quick Test    | H        | 100-110     | 11     | High priority, smallest        |
| 2     | Hero Shot     | H        | 500-650     | 151    | High priority, larger          |
| 3     | BG Elements   | L        | 50-100      | 51     | Low priority, smallest         |
| 4     | Full Sequence | L        | 1000-1500   | 501    | Low priority, largest          |

**Interactive Input:**
- No hardcoded frame ranges
- Fully dynamic queue creation
- Add as many batches as needed
- Cancel or finish at any time

---

## Requirements

- **macOS** (Bash 3+ compatible)
- **Blender** installed at `/Applications/Blender.app/`
- **bc** (basic calculator - pre-installed on macOS)
- **Terminal** with support for ANSI escape sequences

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
- [ ] Web dashboard for remote monitoring
- [ ] GPU vs CPU render detection
- [ ] Render farm distribution support
- [ ] Resume failed batches from queue
- [ ] Export queue summary as CSV/JSON
- [ ] Parallel batch rendering support
