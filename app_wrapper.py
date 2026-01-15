"""
Wrapper that tries to load backend.main, but falls back to minimal if it fails
This is the actual app object that uvicorn will load
"""
import sys
import logging
import traceback
import os
from datetime import datetime

# MUST be unbuffered for Railway logging
os.environ['PYTHONUNBUFFERED'] = '1'
sys.stdout.flush()
sys.stderr.flush()

# Configure logging FIRST with immediate flush
class ImmediateFlushHandler(logging.StreamHandler):
    def emit(self, record):
        try:
            msg = self.format(record)
            self.stream.write(msg + self.terminator)
            self.flush()
        except Exception:
            self.handleError(record)

handler = ImmediateFlushHandler(sys.stdout)
handler.setFormatter(logging.Formatter('[%(levelname)s] %(message)s'))
logging.basicConfig(level=logging.INFO, handlers=[handler], force=True)
logger = logging.getLogger(__name__)

logger.info("=" * 80)
logger.info("AURORA OSI v3 - APP WRAPPER LOADING")
logger.info("=" * 80)
logger.info(f"Python: {sys.version}")
logger.info(f"CWD: {os.getcwd()}")
logger.info(f"PYTHONPATH: {os.getenv('PYTHONPATH', 'not set')}")

# Try to load real backend
app = None
backend_error = None

try:
    logger.info("Importing backend.main...")
    from backend.main import app as backend_app
    app = backend_app
    logger.info("✓ Backend loaded successfully")
except Exception as e:
    logger.error(f"✗ Backend import failed: {type(e).__name__}: {e}")
    backend_error = str(e)
    logger.error(f"Traceback:\n{traceback.format_exc()}")

# If backend failed, use fallback
if app is None:
    logger.warning("Creating fallback minimal app...")
    from fastapi import FastAPI
    from fastapi.responses import JSONResponse
    
    app = FastAPI(title="Aurora OSI v3 - Fallback", version="3.1.0")
    
    @app.get("/system/health")
    async def health_check():
        logger.info("Health check requested")
        return JSONResponse({
            "status": "ok",
            "mode": "fallback",
            "backend_error": backend_error,
            "timestamp": datetime.now().isoformat(),
            "service": "aurora-minimal"
        }, status_code=200)
    
    @app.get("/")
    async def root():
        return JSONResponse({
            "message": "Aurora OSI v3 (Fallback Mode)",
            "status": "running",
            "error": backend_error
        })
    
    logger.info("✓ Fallback app initialized")

logger.info("=" * 80)
logger.info("APP READY FOR UVICORN")
logger.info("=" * 80)
