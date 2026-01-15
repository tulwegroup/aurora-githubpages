#!/bin/bash
# Health check wrapper script
# This runs as the healthcheck, separate from the main app

set -e

PORT=${PORT:-8000}
TIMEOUT=5

echo "[healthcheck] Attempting to reach http://localhost:${PORT}/system/health"

# Try to hit the health endpoint with curl
response=$(curl -s -f -m $TIMEOUT http://localhost:${PORT}/system/health 2>&1) || {
    echo "[healthcheck] FAILED: Could not reach health endpoint"
    exit 1
}

# Check if response contains "healthy"
if echo "$response" | grep -q "healthy"; then
    echo "[healthcheck] SUCCESS: Service is healthy"
    exit 0
else
    echo "[healthcheck] FAILED: Service responded but not healthy: $response"
    exit 1
fi
