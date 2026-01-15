#!/usr/bin/env python
"""
Entry point script - runs the app with proper PORT handling
This bypasses any shell environment variable issues
"""
import os
import sys
import subprocess

# Force unbuffered output
sys.stdout = os.fdopen(sys.stdout.fileno(), 'w', 0) if hasattr(sys.stdout, 'fileno') else sys.stdout
sys.stderr = os.fdopen(sys.stderr.fileno(), 'w', 0) if hasattr(sys.stderr, 'fileno') else sys.stderr

# Get PORT from environment, default to 8000
port = os.getenv("PORT", "8000")

print("[ENTRYPOINT] ========================================", flush=True)
print("[ENTRYPOINT] Aurora OSI v3 - Python Entrypoint", flush=True)
print("[ENTRYPOINT] ========================================", flush=True)
print(f"[ENTRYPOINT] PORT = {port}", flush=True)
print(f"[ENTRYPOINT] Python version: {sys.version}", flush=True)
print("[ENTRYPOINT] Starting uvicorn app_wrapper...", flush=True)
print("[ENTRYPOINT] ========================================", flush=True)

# Run uvicorn directly with the port as an integer
try:
    print(f"[ENTRYPOINT] Executing: python -m uvicorn app_wrapper:app --host 0.0.0.0 --port {port} --log-level debug", flush=True)
    sys.stdout.flush()
    sys.stderr.flush()
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
    print(f"[ERROR] Failed to start: {e}", file=sys.stderr, flush=True)
    sys.stderr.flush()
    sys.exit(1)
