"""
Wrapper app - tries to use backend, falls back to minimal app
"""
import os
import sys
import logging

# Unbuffered output
os.environ['PYTHONUNBUFFERED'] = '1'

# Basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from datetime import datetime

# Try to import and use the full backend
app = None
backend_loaded = False

try:
    logger.info("🚀 Attempting to load backend.main...")
    from backend.main import app as backend_app
    app = backend_app
    backend_loaded = True
    logger.info("✓ Backend loaded successfully")
except ImportError as e:
    logger.warning(f"⚠️ Could not import backend.main: {e}")
except Exception as e:
    logger.error(f"✗ Error loading backend: {e}", exc_info=True)

# Fallback minimal app if backend failed
if app is None:
    logger.info("Using fallback minimal app")
    app = FastAPI(title="Aurora OSI v3 - Fallback")
    
    @app.get("/system/health")
    async def health():
        return JSONResponse({
            "status": "healthy",
            "mode": "fallback",
            "timestamp": datetime.now().isoformat(),
            "version": "3.1.0"
        })
    
    @app.get("/health")
    async def health_alt():
        return JSONResponse({
            "status": "healthy",
            "mode": "fallback",
            "timestamp": datetime.now().isoformat(),
            "version": "3.1.0"
        })
    
    @app.get("/")
    async def root():
        return JSONResponse({
            "message": "Aurora OSI v3 - Fallback Mode",
            "status": "running"
        })

logger.info(f"✓ App ready. Backend loaded: {backend_loaded}")
