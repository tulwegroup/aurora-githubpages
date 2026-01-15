"""
Wrapper that tries to load backend.main, but falls back to minimal if it fails
This ensures we always get useful error messages
"""
import sys
import logging

logging.basicConfig(
    level=logging.DEBUG,
    format='[%(asctime)s] [%(levelname)s] %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

logger.info("=" * 80)
logger.info("AURORA OSI v3 - APP WRAPPER")
logger.info("=" * 80)

# Try to import the full backend
try:
    logger.info("[1/3] Attempting to import backend.main...")
    from backend.main import app
    logger.info("[2/3] ✓ backend.main imported successfully")
    logger.info("[3/3] ✓ Using full backend app")
    logger.info("=" * 80)
    
except Exception as e:
    logger.error(f"[!] FAILED to import backend.main: {type(e).__name__}: {e}")
    logger.error("Detailed error:", exc_info=True)
    logger.warning("\n[FALLBACK] Loading minimal app instead...\n")
    
    # Fallback to minimal app
    from fastapi import FastAPI
    from fastapi.responses import JSONResponse
    from datetime import datetime
    import os
    
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

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    logger.info(f"Starting app on 0.0.0.0:{port}")
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="debug")
