#!/bin/bash
set -e

# Entrypoint script - runs BEFORE CMD, ensures PORT is always set

echo "=========================================="
echo "Aurora OSI v3 - Entrypoint Script"
echo "=========================================="

# Set PORT - use environment variable if available, otherwise default
PORT=${PORT:-8000}
export PORT

echo "[entrypoint] PORT set to: $PORT"
echo "[entrypoint] Starting app wrapper..."
echo "=========================================="

# Run uvicorn directly with explicit port
exec uvicorn app_wrapper:app \
    --host 0.0.0.0 \
    --port "$PORT" \
    --log-level debug
