"""
Minimal FastAPI app for health checks and status
This is the entry point to ensure the app starts even if backend has issues
"""
import sys
import logging

# Configure logging FIRST before any imports
logging.basicConfig(
    level=logging.DEBUG,
    format='[%(asctime)s] [%(levelname)s] %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

logger.info("=" * 60)
logger.info("STARTING AURORA OSI v3 MINIMAL APP")
logger.info("=" * 60)

try:
    from fastapi import FastAPI
    from fastapi.responses import JSONResponse
    import os
    from datetime import datetime
    
    logger.info("✓ All imports successful")
    
    app = FastAPI(
        title="Aurora OSI v3 - Minimal",
        description="Health check endpoint",
        version="3.1.0"
    )
    
    logger.info("✓ FastAPI app initialized")
    logger.info("=" * 60)
    
except Exception as e:
    logger.error(f"FATAL: Failed to initialize app: {e}", exc_info=True)
    sys.exit(1)


@app.get("/system/health")
async def health_check():
    """Health check endpoint - returns ok for Railway"""
    logger.info("Health check received")
    return JSONResponse({
        "status": "ok",
        "timestamp": datetime.now().isoformat(),
        "version": "v3.0",
        "environment": os.getenv("ENVIRONMENT", "production"),
        "service": "minimal"
    }, status_code=200)


@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "Aurora OSI v3 is alive"}


@app.on_event("startup")
async def startup_event():
    logger.info("🚀 Aurora OSI v3 Minimal Backend Started")


@app.on_event("shutdown")
async def shutdown_event():
    logger.info("🛑 Aurora OSI v3 Minimal Backend Shutdown")


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    logger.info(f"Starting server on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)
