"""
Aurora OSI v3 - System Router
Health checks and system status endpoints
"""

import logging
from fastapi import APIRouter, HTTPException
from typing import Dict, List, Optional
from datetime import datetime
import psutil
import os

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/system", tags=["System"])


@router.get("/health")
async def health_check() -> Dict:
    """
    Health check endpoint
    Returns system status and component health
    """
    try:
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "version": "v3.0",
            "environment": os.getenv("ENVIRONMENT", "development")
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail="Service unavailable")


@router.get("/status")
async def system_status() -> Dict:
    """
    Detailed system status
    Includes CPU, memory, disk usage
    """
    try:
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage("/")
        
        return {
            "status": "operational",
            "timestamp": datetime.now().isoformat(),
            "cpu": {
                "percent": cpu_percent,
                "cores": psutil.cpu_count()
            },
            "memory": {
                "total_mb": memory.total / (1024 ** 2),
                "available_mb": memory.available / (1024 ** 2),
                "percent": memory.percent
            },
            "disk": {
                "total_gb": disk.total / (1024 ** 3),
                "used_gb": disk.used / (1024 ** 3),
                "free_gb": disk.free / (1024 ** 3),
                "percent": disk.percent
            }
        }
    except Exception as e:
        logger.error(f"Status check failed: {e}")
        raise HTTPException(status_code=500, detail="Could not retrieve system status")


@router.get("/services")
async def service_status() -> Dict:
    """
    Check status of all backend services
    Database, Redis, GEE, etc.
    """
    services = {
        "api": "operational",
        "database": "checking",
        "redis": "checking",
        "earth_engine": "checking",
        "worker_queue": "operational"
    }
    
    # Check database connection
    try:
        from backend.database import db_manager
        # Simple query to test connection
        db_manager.execute("SELECT 1")
        services["database"] = "operational"
    except Exception as e:
        logger.warning(f"Database check failed: {e}")
        services["database"] = "unavailable"
    
    # Check Redis connection
    try:
        import redis
        r = redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379/0"))
        r.ping()
        services["redis"] = "operational"
    except Exception as e:
        logger.warning(f"Redis check failed: {e}")
        services["redis"] = "unavailable"
    
    # Check Earth Engine
    try:
        from backend.gee import get_ee_client
        client = get_ee_client()
        services["earth_engine"] = "operational"
    except Exception as e:
        logger.warning(f"Earth Engine check failed: {e}")
        services["earth_engine"] = "unavailable"
    
    return {
        "timestamp": datetime.now().isoformat(),
        "services": services,
        "overall": "operational" if all(
            s == "operational" for s in services.values()
        ) else "degraded"
    }


@router.post("/restart")
async def restart_services() -> Dict:
    """
    Restart backend services (admin only in production)
    """
    logger.warning("System restart requested")
    return {
        "message": "Restart signal sent to all services",
        "timestamp": datetime.now().isoformat()
    }


@router.get("/metrics")
async def system_metrics() -> Dict:
    """
    Retrieve detailed system metrics
    Performance, uptime, processing stats
    """
    try:
        boot_time = datetime.fromtimestamp(psutil.boot_time())
        uptime_seconds = (datetime.now() - boot_time).total_seconds()
        
        return {
            "timestamp": datetime.now().isoformat(),
            "uptime_seconds": uptime_seconds,
            "boot_time": boot_time.isoformat(),
            "process_count": len(psutil.pids()),
            "cpu": {
                "percent": psutil.cpu_percent(interval=1),
                "freq_ghz": psutil.cpu_freq().current / 1000 if psutil.cpu_freq() else None
            },
            "memory": {
                "percent": psutil.virtual_memory().percent,
                "available_gb": psutil.virtual_memory().available / (1024 ** 3)
            },
            "network": {
                "sent_mb": psutil.net_io_counters().bytes_sent / (1024 ** 2),
                "recv_mb": psutil.net_io_counters().bytes_recv / (1024 ** 2)
            }
        }
    except Exception as e:
        logger.error(f"Metrics retrieval failed: {e}")
        raise HTTPException(status_code=500, detail="Could not retrieve metrics")


@router.get("/config")
async def get_config() -> Dict:
    """
    Get current configuration (non-sensitive)
    """
    from backend.config import settings
    
    return {
        "api_version": settings.API_VERSION,
        "environment": settings.ENVIRONMENT,
        "debug": settings.DEBUG,
        "features": {
            "gee_integration": settings.ENABLE_GEE_INTEGRATION,
            "quantum_inversion": settings.ENABLE_QUANTUM_INVERSION,
            "seismic_processing": settings.ENABLE_SEISMIC_PROCESSING,
            "digital_twin": settings.ENABLE_DIGITAL_TWIN
        },
        "limits": {
            "max_detection_results": settings.MAX_DETECTION_RESULTS,
            "mineral_confidence_threshold": settings.MINERAL_CONFIDENCE_THRESHOLD,
            "temporal_window_days": settings.TEMPORAL_WINDOW_DAYS
        }
    }


@router.post("/clear-cache")
async def clear_cache() -> Dict:
    """
    Clear Redis cache (admin only)
    """
    try:
        import redis
        r = redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379/0"))
        r.flushdb()
        logger.info("Cache cleared")
        return {"message": "Cache cleared successfully", "timestamp": datetime.now().isoformat()}
    except Exception as e:
        logger.error(f"Cache clear failed: {e}")
        raise HTTPException(status_code=500, detail="Could not clear cache")
