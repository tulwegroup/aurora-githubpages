#!/bin/bash
# Startup script for Aurora OSI v3
# This is the main entrypoint with detailed logging

set -e  # Exit on any error

PORT=${PORT:-8000}
export PYTHONUNBUFFERED=1

echo "[startup] ========================================="
echo "[startup] Aurora OSI v3 Backend Starting"
echo "[startup] PORT: $PORT"
echo "[startup] ENVIRONMENT: ${ENVIRONMENT:-production}"
echo "[startup] ========================================="

# Start uvicorn directly (simpler and more reliable than gunicorn)
echo "[startup] Starting uvicorn..."
exec python -m uvicorn app_minimal:app \
    --host 0.0.0.0 \
    --port $PORT \
    --workers 2 \
    --log-level info 2>&1
