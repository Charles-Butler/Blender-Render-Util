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
- Interactive case/game name prompt
- Timestamp-based output directories
- Automatic log file creation
- Sequential batch rendering
- Audio notification on completion

**Usage:**
```bash
./batchedFrame_render.sh
```

You'll be prompted to enter a case/game name, and rendering will begin automatically.

**Output Structure:**
```
./renders/
└── {CASE_NAME}_{TIMESTAMP}/
    └── {CASE_NAME}_{TIMESTAMP}_render_log.txt
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
tail -f ./renders/CASE_NAME/log_file.txt | ./watch_render_progress.sh
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

### v2.2 - Dual Progress Tracking *(Current)*
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

### Batch Configuration

Current render batches (527 total frames):

| Batch | Frame Range | Frames | Order |
|-------|-------------|--------|-------|
| 5     | 973-999     | 27     | 1st   |
| 8     | 0-59        | 60     | 2nd   |
| 6     | 1059-1130   | 72     | 3rd   |
| 4     | 795-869     | 75     | 4th   |
| 7     | 1130-1230   | 101    | 5th   |
| 2     | 642-672     | 31     | 6th   |
| 3     | 702-755     | 54     | 7th   |
| 1     | 494-600     | 107    | 8th   |

---

## Requirements

- **macOS** (Bash 3+ compatible)
- **Blender** installed at `/Applications/Blender.app/`
- **bc** (basic calculator - pre-installed on macOS)
- **Terminal** with support for ANSI escape sequences

---

## Configuration

### Modifying Batch Ranges

Edit `batchedFrame_render.sh` and update the Blender command flags:

```bash
$BLENDER_PATH -b "$BLEND_FILE" -s START_FRAME -e END_FRAME -a
```

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

## Future Enhancements

- [ ] Configuration file for batch ranges
- [ ] Support for multiple .blend files
- [ ] Email/notification on completion
- [ ] Web dashboard for remote monitoring
- [ ] Automatic retry on failed frames
- [ ] GPU vs CPU render detection
- [ ] Render farm distribution support
