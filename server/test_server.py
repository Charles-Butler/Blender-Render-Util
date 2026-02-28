#!/usr/bin/env python3
"""
Simple test to verify server files are valid Python
"""

import sys
from pathlib import Path

print("Testing server files...")
print("="*60)

# Test app.py syntax
print("1. Checking app.py syntax...")
try:
    with open('app.py', 'r') as f:
        compile(f.read(), 'app.py', 'exec')
    print("   ✓ app.py syntax valid")
except SyntaxError as e:
    print(f"   ✗ app.py syntax error: {e}")
    sys.exit(1)

# Test monitor.py syntax
print("2. Checking monitor.py syntax...")
try:
    with open('monitor.py', 'r') as f:
        compile(f.read(), 'monitor.py', 'exec')
    print("   ✓ monitor.py syntax valid")
except SyntaxError as e:
    print(f"   ✗ monitor.py syntax error: {e}")
    sys.exit(1)

# Check requirements.txt
print("3. Checking requirements.txt...")
try:
    with open('requirements.txt', 'r') as f:
        deps = f.readlines()
    print(f"   ✓ Found {len(deps)} dependencies")
    for dep in deps:
        print(f"     - {dep.strip()}")
except Exception as e:
    print(f"   ✗ Error reading requirements.txt: {e}")
    sys.exit(1)

print("="*60)
print("✓ All server files are valid!")
print("\nNext steps:")
print("1. Install dependencies: pip3 install -r requirements.txt")
print("2. Run server: python3 app.py --port 8080")
