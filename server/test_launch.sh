#!/bin/bash

echo "Testing Server Launch..."
echo "========================================"

# Check if Python 3 is available
echo "1. Checking Python version..."
python3 --version

# Check if dependencies are installed
echo ""
echo "2. Checking dependencies..."
python3 -c "
try:
    import fastapi
    print('   ✓ fastapi installed')
except ImportError:
    print('   ✗ fastapi NOT installed')

try:
    import uvicorn
    print('   ✓ uvicorn installed')
except ImportError:
    print('   ✗ uvicorn NOT installed')

try:
    import websockets
    print('   ✓ websockets installed')
except ImportError:
    print('   ✗ websockets NOT installed')

try:
    import watchdog
    print('   ✓ watchdog installed')
except ImportError:
    print('   ✗ watchdog NOT installed')
"

# Try to import the app
echo ""
echo "3. Testing app.py import..."
python3 -c "
try:
    # Test if monitor.py can be imported
    import sys
    sys.path.insert(0, '.')
    from monitor import LogMonitor
    print('   ✓ monitor.py imports successfully')
except Exception as e:
    print(f'   ✗ Error importing monitor.py: {e}')
"

echo ""
echo "========================================"
echo "To install dependencies, run:"
echo "  pip3 install -r requirements.txt"
echo ""
echo "To launch server, run:"
echo "  python3 app.py --port 8080"
