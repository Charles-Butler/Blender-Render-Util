#!/bin/bash

echo "================================================================"
echo "    Blender Render Monitor - Full Stack Test"
echo "================================================================"
echo ""

# Set log file path
TEST_LOG="./test_render.log"

# Clean up old test log
rm -f "$TEST_LOG"

echo "1. Starting web server..."
echo "   Access dashboard at: http://localhost:8080"
echo ""

# Start server in background
python3 app.py --port 8080 --project "TestProject" --batches 2 --logfile "$TEST_LOG" &
SERVER_PID=$!

# Wait for server to start
sleep 3

echo "2. Server started (PID: $SERVER_PID)"
echo ""
echo "3. Starting test render log generator in 3 seconds..."
echo "   (This will simulate Blender rendering 20 frames)"
echo ""

sleep 3

# Run log generator
python3 test_log_generator.py "$TEST_LOG"

echo ""
echo "================================================================"
echo "Test complete!"
echo ""
echo "The server is still running. Visit http://localhost:8080"
echo "to see the final state."
echo ""
echo "Press Ctrl+C to stop the server, or run:"
echo "  kill $SERVER_PID"
echo "================================================================"

# Keep script running so server stays alive
wait $SERVER_PID
