#!/bin/bash
# Build RenderManager.app
# Usage: cd app && ./build.sh

set -e

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
APP_DIR="$ROOT/app"
FRONTEND_DIR="$ROOT/server/frontend"

echo "================================================"
echo "  Render Manager - Build Script"
echo "================================================"

# 1. Build React frontend
echo ""
echo "[ 1/3 ] Building React frontend..."
cd "$FRONTEND_DIR"
npm run build
echo "✓ Frontend built → server/frontend/dist/"

# 2. Install Python dependencies
echo ""
echo "[ 2/3 ] Checking Python dependencies..."
pip3 install pyinstaller pywebview fastapi uvicorn watchdog websockets --quiet
echo "✓ Dependencies ready"

# 3. Run PyInstaller (use python3 -m to avoid PATH issues)
echo ""
echo "[ 3/3 ] Bundling with PyInstaller..."
cd "$APP_DIR"
python3 -m PyInstaller RenderManager.spec --clean --noconfirm

echo ""
echo "================================================"
echo "  ✅ Build complete!"
echo "  Output: app/dist/RenderManager.app"
echo "================================================"
