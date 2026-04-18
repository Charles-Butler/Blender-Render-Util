# Quick Start Guide - Blender Render Web Interface

## Overview

This system allows you to configure and launch Blender batch renders through a web interface. The workflow is:

1. **Configure** → Select .blend file, add batches with frame ranges and priorities
2. **Launch** → Click "Start Job" to open Terminal and begin rendering
3. **Monitor** → Watch real-time progress in the web interface

---

## Setup (First Time Only)

### 1. Install Backend Dependencies

```bash
cd /path/to/Blender-Render-Util/server
pip3 install -r requirements.txt
```

### 2. Install Frontend Dependencies

```bash
cd /path/to/Blender-Render-Util/server/frontend
npm install
```

---

## Running the Application

### Terminal 1: Start Backend Server

```bash
cd server
python3 app.py --port 8081
```

You should see:
```
✓ Server started on http://0.0.0.0:8081
✓ Access from this machine: http://localhost:8081
```

### Terminal 2: Start Frontend Dev Server

```bash
cd server/frontend
npm run dev
```

You should see:
```
  VITE ready in XXX ms
  ➜  Local:   http://localhost:5173/
```

### Terminal 3: (Optional) Direct Script Testing

To test the bash script directly without the web interface:

```bash
cd /path/to/Blender-Render-Util
./batchedFrame_render.sh
```

---

## Using the Web Interface

### 1. Open Your Browser

Navigate to: **http://localhost:5173**

### 2. Configure Your Render

On the **Configure** page:

1. **Project Name**: Enter a name (e.g., "TOR_SpaceStation")
2. **Blend File**: Select from dropdown of recent files
3. **Add Batches**: Click `+` to add frame ranges
   - **Start Frame**: First frame to render
   - **End Frame**: Last frame to render
   - **Name**: Optional batch name
   - **Priority**:
     - `High` = Renders first (smaller batches)
     - `Low` = Renders after high priority

4. Review the **Render Order Preview** to see execution order
5. Click **Start Job**

### 3. Rendering Begins

- A new **Terminal window** will open automatically
- The bash script runs with your configuration
- Terminal shows real-time Blender output

### 4. Monitor Progress

- Switch to the **Monitor** page in the web interface
- See live progress bars for:
  - Current batch progress
  - Overall render progress
  - Time estimates
  - Frame completion stats
  - Batch queue status

---

## Example Configuration

**Project Name**: `TOR_SpaceStation`

**Batches**:
| # | Name | Start | End | Frames | Priority |
|---|------|-------|-----|--------|----------|
| 1 | Intro | 0 | 59 | 60 | High |
| 2 | Main | 60 | 200 | 141 | Low |
| 3 | Outro | 201 | 250 | 50 | High |

**Render Order** (priority sorted):
1. Intro (60 frames) - High
2. Outro (50 frames) - High
3. Main (141 frames) - Low

---

## Output Structure

Renders are saved to:

```
renders/
└── {PROJECT_NAME}_{TIMESTAMP}/
    ├── {PROJECT_NAME}_{TIMESTAMP}_render_log.txt
    └── [rendered frames...]
```

Example:
```
renders/TOR_SpaceStation_2026-03-19_16-30-00/
├── TOR_SpaceStation_2026-03-19_16-30-00_render_log.txt
└── 0001.png
└── 0002.png
...
```

---

## Troubleshooting

### Backend won't start

```bash
# Check if port 8081 is in use
lsof -i :8081

# Kill existing process if needed
kill -9 <PID>
```

### Frontend won't start

```bash
# Check if port 5173 is in use
lsof -i :5173

# Try a different port
npm run dev -- --port 5174
```

### Terminal doesn't open when clicking "Start Job"

1. Check that the bash script is executable:
   ```bash
   chmod +x batchedFrame_render.sh
   ```

2. Check Terminal permissions in System Preferences → Security & Privacy

3. Check backend logs for errors

### Blend file not found

1. Verify the path is correct
2. Add your .blend file via the API:
   ```bash
   curl -X POST http://localhost:8081/api/blend-files/add \
     -H "Content-Type: application/json" \
     -d '{"file_path": "/path/to/your/file.blend"}'
   ```

### Monitor not updating

1. Check WebSocket connection in browser console (F12)
2. Verify backend is running on port 8081
3. Check that log file is being created in renders directory

---

## Next Steps

- **Cancel Renders**: Click "Cancel Job" to stop active render
- **View Active Renders**: Navigate between Configure/Monitor pages any time
- **Re-run Renders**: Configure and start multiple jobs in sequence
- **Check Logs**: Open `renders/{PROJECT}_{TIMESTAMP}/` for detailed logs

---

## API Endpoints

For automation or debugging:

- `GET  /api/status` - Current render status
- `GET  /api/config` - Configuration settings
- `GET  /api/blend-files` - List recent blend files
- `POST /api/blend-files/add` - Add blend file to recent list
- `POST /api/render/start` - Start render job
- `POST /api/render/cancel` - Cancel active render
- `GET  /api/browse-log-files` - List available log files
- `WS   /ws` - WebSocket for live updates
