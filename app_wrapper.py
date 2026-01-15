"""
Wrapper that tries to load backend.main, but falls back to minimal if it fails
This ensures we always get useful error messages
"""
import sys
import logging
import traceback
import os

# Force unbuffered output immediately
sys.stdout.flush()
sys.stderr.flush()

# Set up logging with immediate flush
class ImmediateFlushHandler(logging.StreamHandler):
    def emit(self, record):
        super().emit(record)
        self.flush()

logging.basicConfig(
    level=logging.DEBUG,
    format='[%(levelname)s] %(message)s',
    handlers=[ImmediateFlushHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

logger.info("=" * 80)
logger.info("AURORA OSI v3 - APP WRAPPER STARTING")
logger.info("=" * 80)
logger.info(f"Python: {sys.version}")
logger.info(f"Working directory: {os.getcwd()}")
logger.info(f"PYTHONPATH: {os.getenv('PYTHONPATH', 'not set')}")

# Try to import the full backend
try:
    logger.info("[1/3] Attempting to import backend.main...")
    from backend.main import app
    logger.info("[2/3] ✓ backend.main imported successfully")
    logger.info("[3/3] ✓ Using full backend app")
    logger.info("=" * 80)
    
except Exception as e:
    logger.error(f"[!] FAILED to import backend.main")
    logger.error(f"[!] Error type: {type(e).__name__}")
    logger.error(f"[!] Error message: {e}")
    logger.error(f"[!] Traceback:\n{traceback.format_exc()}")
    logger.warning("\n[FALLBACK] Loading minimal app instead...\n")
    
    # Fallback to minimal app
    try:
        from fastapi import FastAPI
        from fastapi.responses import JSONResponse
        from datetime import datetime
        
        app = FastAPI(
            title="Aurora OSI v3 - Minimal (Fallback)",
            version="3.1.0"
        )
        
        @app.get("/system/health")
        async def health_check():
            """Health check endpoint"""
            logger.info("[healthcheck] Received health check")
            return JSONResponse({
                "status": "ok",
                "mode": "fallback",
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
                "service": "aurora-minimal"
            }, status_code=200)
        
        @app.on_event("startup")
        async def startup():
            logger.error(f"FALLBACK MODE: Backend failed with: {e}")
        
        logger.info("=" * 80)
        logger.info("✓ Minimal app loaded successfully")
        logger.info("=" * 80)
        
    except Exception as fallback_error:
        logger.error(f"CRITICAL: Even fallback failed: {fallback_error}")
        logger.error(traceback.format_exc())
        sys.exit(1)

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    logger.info(f"Starting app on 0.0.0.0:{port}")
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="debug")
