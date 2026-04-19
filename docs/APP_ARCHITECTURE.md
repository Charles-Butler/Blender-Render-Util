# Render Manager — Application Architecture

## Overview

The goal is to ship Render Manager as a **Blender Market add-on** that launches a native desktop application window (not a browser tab). The system is split into two components that are distributed separately.

---

## Two-Component System

```
┌─────────────────────────────────────────────────────┐
│  BLENDER                                            │
│  ┌─────────────────────────────────────────────┐   │
│  │  Render Manager Add-on  (N-Panel sidebar)   │   │
│  │  • Unsaved changes check                    │   │
│  │  • Save blend file                          │   │
│  │  • Launch RenderManager.app (detached)      │   │
│  │  • bpy.ops.wm.quit_blender()                │   │
│  └─────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────┘
                        │ subprocess.Popen
                        │ start_new_session=True (detached)
                        │ passes --blend-file arg
                        ▼
┌─────────────────────────────────────────────────────┐
│  RenderManager.app  (PyWebView + PyInstaller)       │
│  ┌──────────────┐    ┌──────────────────────────┐  │
│  │  launcher.py │───▶│  FastAPI (daemon thread)  │  │
│  │              │    │  serves frontend/dist/    │  │
│  │  PyWebView   │◀───│  + all API routes         │  │
│  │  native OS   │    │  + WebSocket              │  │
│  │  window      │    └──────────────────────────┘  │
│  └──────────────┘                                   │
└─────────────────────────────────────────────────────┘
```

---

## Project Structure (Target)

```
Blender-Render-Util/
├── app/
│   ├── launcher.py               # PyWebView entry point
│   ├── RenderManager.spec        # PyInstaller bundle spec
│   └── build.sh                  # One-command build script
├── addon/
│   ├── __init__.py               # Blender add-on (panel + operator)
│   └── launch.py                 # App process launcher helper
├── server/
│   ├── app.py                    # FastAPI backend
│   ├── monitor.py                # Log file monitor
│   ├── config_manager.py         # JSON config persistence
│   ├── config.template.json      # New-install reference config
│   ├── requirements.txt
│   └── frontend/
│       ├── dist/                 # Pre-built React (npm run build)
│       └── src/                  # React source
├── docs/
│   ├── APP_ARCHITECTURE.md       # This file
│   └── BLEND_FILE_SELECTION.md
├── legacy/
│   ├── watch_render_progress.sh
│   └── DESIGN_NOTES.md
└── batchedFrame_render.sh
```

---

## Implementation Phases

### Phase 1 — Pre-build Fixes ✅ _(Complete)_

Changes to existing files so the app is self-contained and port-agnostic before any new code is written.

**`server/app.py`**
- Fix default port: `8080` → `8081`
- Fix startup print statements to use the actual port variable
- Update root route handler to serve from `frontend/dist/index.html`
- Mount `frontend/dist/` as StaticFiles at end of file (after all API routes)

**`server/frontend/src/App.jsx`**
- WebSocket: `ws://${window.location.hostname}:8081/ws` → `ws://${window.location.host}/ws`
- All `http://localhost:8081/api/...` fetch calls → `/api/...` (relative)

**`server/frontend/src/pages/ConfigureRender.jsx`**
- All `http://localhost:8081/api/...` → `/api/...`

**`server/frontend/src/pages/ProgressMonitor.jsx`**
- All `http://localhost:8081/api/...` → `/api/...`

---

### Phase 2 — Standalone App Launcher ✅ _(Complete)_

**`app/launcher.py`** startup sequence:
1. Start FastAPI + uvicorn in a daemon thread on port 8081
2. Poll `GET /health` until 200 OK (max 10s timeout)
3. Parse `--blend-file` CLI arg, pre-populate config if provided
4. Open PyWebView window → `http://localhost:8081`
   - Title: "Render Manager"
   - Width: 1280, Height: 800
   - No browser chrome
5. `pywebview.start()` — blocks until window closed
6. Signal uvicorn thread to shut down

---

### Phase 3 — PyInstaller Bundle ✅ _(Complete)_

**`app/RenderManager.spec`** bundles:
- Python runtime
- `fastapi`, `uvicorn`, `pywebview`, `watchdog`, `websockets`
- `server/` (app.py, monitor.py, config_manager.py)
- `server/frontend/dist/` (pre-built React — no Node needed at runtime)
- `batchedFrame_render.sh`

**Build flow:**
```bash
cd server/frontend && npm run build
cd ../../app && pyinstaller RenderManager.spec
# Output: app/dist/RenderManager.app
```

---

### Phase 4 — Blender Add-on

**`addon/__init__.py`** structure:
```python
bl_info = {
    "name": "Render Manager",
    "version": (4, 3, 0),
    "blender": (3, 0, 0),
    "category": "Render",
}
```

**Panel** — N-Panel → "Render" tab → "Render Manager" section:
- Shows current blend file name
- "Launch Render Manager" button

**Operator** (`RENDER_OT_launch_manager`):
1. Check `bpy.data.is_dirty` → show confirm dialog if unsaved changes
2. `bpy.ops.wm.save_mainfile()` if confirmed
3. Resolve RenderManager.app path (preferences → `/Applications` → add-on dir)
4. `subprocess.Popen([app_path, '--blend-file', bpy.data.filepath], start_new_session=True)`
5. `bpy.ops.wm.quit_blender()`

**Add-on Preferences** — stores path to RenderManager.app for non-standard install locations.

**App Discovery Order:**
1. Path stored in add-on preferences
2. `/Applications/RenderManager.app`
3. Same directory as the add-on `.zip`

---

## Distribution (Blender Market)

```
Customer downloads two items:

  1. RenderManager_v4.3.0.dmg  →  drag RenderManager.app to /Applications
                                    (~50-80MB, Python + deps + built React)

  2. render_manager_addon.zip  →  install via Blender Preferences → Add-ons
                                    (~10KB, pure Python, no dependencies)
```

The add-on is listed on Blender Market. The app download link is included in the add-on's README and the Blender Market listing description.

---

## Key Design Decisions

| Decision | Choice | Reason |
|----------|--------|--------|
| App window | PyWebView | Native OS window, Python-native, ~20MB vs Electron ~150MB |
| Bundler | PyInstaller | Standard Python tool, produces proper macOS .app |
| Frontend serving | FastAPI static files from `dist/` | No Node/Vite at runtime, single process |
| API URLs | Relative (`/api/...`) | Works on any port, same-origin, no CORS needed |
| Blender integration | N-Panel operator | Non-destructive, standard add-on pattern |
| Process detachment | `start_new_session=True` | App survives after Blender quits |
| Distribution | Two separate downloads | Keeps add-on zip small for Blender Market |

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Desktop window | `pywebview` |
| Backend | `FastAPI` + `uvicorn` |
| Frontend | React 19 + Vite (pre-built) |
| Log monitoring | `watchdog` + polling fallback |
| Config persistence | JSON via `config_manager.py` |
| Bundling | `PyInstaller` |
| Blender integration | `bpy` (Python API) |
