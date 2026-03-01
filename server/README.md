# Blender Render Monitor - Server

FastAPI-based web server for monitoring Blender renders in real-time.

## Quick Start

### 1. Install Dependencies

**Option A: Full installation (recommended)**
```bash
# Accept Xcode license (required on macOS)
sudo xcodebuild -license

# Install dependencies
pip3 install -r requirements.txt
```

**Option B: Minimal installation (if Xcode not available)**
```bash
# Install only core dependencies (watchdog will use polling mode)
pip3 install fastapi uvicorn
```

### 2. Run Server

```bash
# Basic usage
python3 app.py --port 8080

# With log file monitoring
python3 app.py --logfile /path/to/render_log.txt --port 8080

# With project info
python3 app.py --project "MyProject" --batches 5 --port 8080
```

### 3. Access Dashboard

- **Local**: http://localhost:8080
- **Network**: http://YOUR_LOCAL_IP:8080

## Features

- ✅ Real-time progress monitoring via WebSocket
- ✅ REST API for status/stats
- ✅ Automatic log file parsing
- ✅ Error detection
- ✅ Mobile-responsive web dashboard
- ✅ Network-accessible (LAN)

## API Endpoints

- `GET /` - Web dashboard
- `GET /api/status` - Current render status
- `GET /api/queue` - Batch queue info
- `GET /api/stats` - Rendering statistics
- `GET /health` - Health check
- `WS /ws` - WebSocket for real-time updates

## Troubleshooting

**Dependencies won't install?**
- Accept Xcode license: `sudo xcodebuild -license`
- Or use minimal install (see above)

**Server won't start?**
- Check if port 8080 is available: `lsof -i :8080`
- Try different port: `python3 app.py --port 8081`

**Can't access from other devices?**
- Check firewall settings
- Ensure devices are on same network
- Use network IP, not localhost

## Development

**Test server files:**
```bash
python3 test_server.py
```

**Run with auto-reload:**
```bash
uvicorn app:app --reload --host 0.0.0.0 --port 8080
```
