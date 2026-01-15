#!/usr/bin/env python
"""
Entry point script - runs the app with proper PORT handling
This bypasses any shell environment variable issues
"""
import os
import sys
import subprocess

# Get PORT from environment, default to 8000
port = os.getenv("PORT", "8000")

print("=" * 80)
print("Aurora OSI v3 - Python Entrypoint")
print("=" * 80)
print(f"[entrypoint] PORT = {port}")
print("[entrypoint] Starting uvicorn app_wrapper...")
print("=" * 80)

# Run uvicorn directly with the port as an integer
try:
    subprocess.run(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "app_wrapper:app",
            "--host",
            "0.0.0.0",
            "--port",
            port,
            "--log-level",
            "debug"
        ],
        check=False
    )
except Exception as e:
    print(f"[ERROR] Failed to start: {e}", file=sys.stderr)
    sys.exit(1)
