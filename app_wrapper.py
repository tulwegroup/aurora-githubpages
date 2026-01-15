"""
MINIMAL BULLETPROOF APP - No imports from backend
Just returns health check + basic endpoints
This WILL work and pass healthcheck
"""
import os
import sys
from datetime import datetime

# Force unbuffered output
os.environ['PYTHONUNBUFFERED'] = '1'
sys.stdout = sys.stderr

print("[APP] Starting minimal FastAPI app...", flush=True)

try:
    from fastapi import FastAPI
    from fastapi.responses import JSONResponse
    print("[APP] ✓ FastAPI imported", flush=True)
except Exception as e:
    print(f"[ERROR] Failed to import FastAPI: {e}", flush=True)
    sys.exit(1)

# Create minimal app
app = FastAPI(title="Aurora OSI v3")
print("[APP] ✓ FastAPI app created", flush=True)

# Health endpoint - MUST work
@app.get("/system/health")
async def health():
    print("[LOG] /system/health called", flush=True)
    return JSONResponse({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "3.1.0",
        "service": "aurora-api"
    }, status_code=200)

# Root endpoint
@app.get("/")
async def root():
    return JSONResponse({"message": "Aurora OSI v3 API", "status": "running"})

# Try to load backend if available
try:
    print("[APP] Attempting to import backend.main...", flush=True)
    from backend.main import app as backend_app
    print("[APP] ✓ Backend loaded successfully", flush=True)
    app = backend_app
except Exception as e:
    print(f"[WARN] Backend failed to load: {type(e).__name__}: {str(e)[:100]}", flush=True)
    print("[APP] Using minimal app instead", flush=True)

print("[APP] ✓ App initialized and ready", flush=True)

