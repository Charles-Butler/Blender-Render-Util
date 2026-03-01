#!/usr/bin/env python3
"""
Quick test to verify the server is serving batch data correctly
"""
import json
import subprocess
import time

print("="*60)
print("Testing Blender Render Monitor Server")
print("="*60)

# Start server in background
print("\n1. Starting server...")
proc = subprocess.Popen([
    'python3', 'app.py',
    '--port', '8081',
    '--logfile', '/Users/me/Podcast/3D-Animation/Repos/renders/005_TOR_RER_2026-02-27_18-07-23/005_TOR_RER_2026-02-27_18-07-23_render_log.txt',
    '--project', '005_TOR_RER',
    '--batches', '8',
    '--frames', '527'
], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

# Wait for server to start
time.sleep(8)

# Test API
print("2. Testing API endpoint...")
result = subprocess.run(['curl', '-s', 'http://localhost:8081/api/status'],
                       capture_output=True, text=True)

if result.returncode == 0:
    data = json.loads(result.stdout)
    rs = data['render_state']

    print("\n" + "="*60)
    print("RENDER STATUS")
    print("="*60)
    print(f"Project: {rs.get('project_name')}")
    print(f"Frames: {rs.get('frames_completed')}/{rs.get('total_frames')} ({rs.get('overall_progress')}%)")
    print(f"Current Batch: #{rs.get('current_batch')}")

    print("\n" + "="*60)
    print("BATCH STATISTICS")
    print("="*60)
    print(f"High Priority: {rs.get('high_priority_batches')} batches ({rs.get('high_priority_frames')} frames)")
    print(f"Low Priority:  {rs.get('low_priority_batches')} batches ({rs.get('low_priority_frames')} frames)")
    print(f"Completed:     {rs.get('completed_batches')} batches ({rs.get('completed_batch_frames')} frames)")

    print("\n" + "="*60)
    print("COMPLETED BATCHES")
    print("="*60)
    for batch in rs.get('completed_list', []):
        print(f"  • {batch['name']}: frames {batch['start']:04d}-{batch['end']:04d} ({batch['frames']} frames)")

    print("\n" + "="*60)
    print("HIGH PRIORITY BATCHES (Pending)")
    print("="*60)
    for batch in rs.get('high_priority_list', []):
        print(f"  • {batch['name']}: frames {batch['start']:04d}-{batch['end']:04d} ({batch['frames']} frames)")

    print("\n" + "="*60)
    print("LOW PRIORITY BATCHES (Pending)")
    print("="*60)
    low_list = rs.get('low_priority_list', [])
    if low_list:
        for batch in low_list:
            print(f"  • {batch['name']}: frames {batch['start']:04d}-{batch['end']:04d} ({batch['frames']} frames)")
    else:
        print("  (none)")

    print("\n" + "="*60)
    print("SERVER INFO")
    print("="*60)
    print(f"Dashboard: http://localhost:8081")
    print(f"Server PID: {proc.pid}")
    print("\nTo stop the server, run:")
    print(f"  kill {proc.pid}")
    print("\nTo view in browser:")
    print("  Open http://localhost:8081")
    print("  Press Cmd+Shift+R (Mac) or Ctrl+Shift+R (Windows) to hard refresh")
    print("="*60)

else:
    print("❌ Failed to connect to server")
    proc.kill()
