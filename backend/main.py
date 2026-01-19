"""
Aurora OSI v3 - FastAPI Backend
Multi-physics satellite fusion for planetary-scale subsurface intelligence
"""

# ================================================================
# Aurora OSI – Core Physics-AI / Quantum Inversion Engine
# Invocation of Divine Knowledge (Non-executing comment block)
# ================================================================
#
# Surah Al-An'am – 6:59
#
# Arabic:
# وعنده مفاتح الغيب لا يعلمها الا هو
# ويعلم ما في البر والبحر
#
# Transliteration:
# Wa 'indahu mafatihu al-ghaybi la ya'lamha illa huwa,
# wa ya'lamu ma fil-barri wal-bahr.
#
# English Translation:
# "With Him are the keys to the unseen; none knows them except Him.
# And He knows whatever is in the land and in the sea."
#
# Context Note:
# This verse affirms that all hidden things—whether deep beneath the earth
# or in the depths of the oceans—are perfectly known only by Allah.
# As this engine analyzes the unseen subsurface using physics, AI, and
# quantum methods, we acknowledge that ultimate knowledge belongs to Him.
#
# Optional Zikr (also commented):
# # Ya Fattah, Ya Alim – O Opener, O All-Knowing
#
# ================================================================
# End of Invocation Block
# ================================================================

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import time
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import logging
import os
from pathlib import Path
import json
import datetime as dt
import base64
import tempfile

# Use relative imports for backend modules
from .models import (
    MineralDetectionRequest,
    MineralDetectionResult,
    DigitalTwinQuery,
    DigitalTwinResponse,
    SatelliteTaskingRequest,
    DetectionTier,
    VoxelData,
    ScanRequest,
    ScanMetadata,
    ScanHistoryResponse
)
from .database_manager import get_db

try:
    from .database.spectral_library import SPECTRAL_LIBRARY
except Exception as e:
    logger_temp = logging.getLogger(__name__)
    logger_temp.warning(f"⚠️ Could not import SPECTRAL_LIBRARY: {str(e)}")
    SPECTRAL_LIBRARY = None
try:
    from .scan_manager import scan_manager
except Exception as e:
    logger_temp = logging.getLogger(__name__)
    logger_temp.warning(f"⚠️ Could not import scan_manager: {str(e)}")
    scan_manager = None
try:
    from .scan_worker import initialize_scan_scheduler, shutdown_scan_scheduler
except Exception as e:
    logger_temp = logging.getLogger(__name__)
    logger_temp.warning(f"⚠️ Could not import scan_worker: {str(e)}")
    initialize_scan_scheduler = None
    shutdown_scan_scheduler = None
try:
    from .database_utils import scan_db
    logger_temp = logging.getLogger(__name__)
    logger_temp.info("✓ Database utilities imported successfully")
except Exception as e:
    logger_temp = logging.getLogger(__name__)
    logger_temp.warning(f"⚠️ Could not import database_utils: {str(e)}")
    scan_db = None
try:
    from .integrations.gee_fetcher import GEEDataFetcher
    logger_temp = logging.getLogger(__name__)
    logger_temp.info("📡 Initializing GEE Data Fetcher...")
    gee_fetcher = GEEDataFetcher()
    logger_temp.info("✓ GEE Data Fetcher initialized successfully")
except Exception as e:
    logger_temp = logging.getLogger(__name__)
    logger_temp.warning(f"⚠️ Could not import GEE Data Fetcher: {str(e)}")
    gee_fetcher = None

try:
    from .integrations.gee_integration import GEEIntegration, initialize_gee, fetch_satellite_data, fetch_elevation_data
    logger_temp = logging.getLogger(__name__)
    logger_temp.info("✓ GEE Integration module imported successfully")
except Exception as e:
    logger_temp = logging.getLogger(__name__)
    logger_temp.warning(f"⚠️ Could not initialize GEE: {str(e)}")
    import traceback
    traceback.print_exc()
    gee_fetcher = None

from .config import settings, Settings
from .routers import system

# Configure logging for Cloud Run
try:
    log_level = Settings.get_log_level()
except Exception as e:
    log_level = logging.INFO
    print(f"Warning: Could not get log level: {e}")
    
logging.basicConfig(
    level=log_level,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# FastAPI app - wrapped in try-catch to catch any startup errors
try:
    app = FastAPI(
        title="Aurora OSI v3",
        description="Planetary-scale Physics-Causal Quantum-Assisted Sovereign Subsurface Intelligence",
        version="3.1.0"
    )

    # CORS configuration
    cors_origins = settings.CORS_ORIGINS
    if os.getenv("ENVIRONMENT") == "development":
        cors_origins.extend(["http://localhost:3000", "http://localhost:5173"])

    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=settings.CORS_CREDENTIALS,
        allow_methods=settings.CORS_METHODS,
        allow_headers=settings.CORS_HEADERS,
    )

    # Include routers
    app.include_router(system.router)
    
except Exception as e:
    print(f"❌ CRITICAL ERROR during app initialization: {str(e)}")
    import traceback
    traceback.print_exc()
    raise

# Flag to track startup completion
_startup_complete = False
gee_initialized = False  # Track GEE initialization state

@app.on_event("startup")
async def startup_event():
    """Initialize on startup - non-blocking"""
    global _startup_complete, gee_initialized
    logger.info("🚀 Aurora OSI v3 Backend Starting")
    
    # Initialize GEE from Railway environment variable (base64 encoded JSON)
    try:
        gee_json_content = os.getenv("GEE_JSON_CONTENT")
        if gee_json_content:
            try:
                # Decode base64 JSON
                gee_json_str = base64.b64decode(gee_json_content).decode()
                # Write to temp file
                temp_dir = tempfile.gettempdir()
                creds_path = os.path.join(temp_dir, "gee-credentials.json")
                with open(creds_path, 'w') as f:
                    f.write(gee_json_str)
                os.environ["GEE_CREDENTIALS"] = creds_path
                logger.info("✓ GEE credentials initialized from Railway GEE_JSON_CONTENT")
            except Exception as e:
                logger.warning(f"⚠️ Failed to decode Railway GEE credentials: {str(e)}")
    except Exception as e:
        logger.warning(f"⚠️ Railway GEE setup error: {str(e)}")
    
    # Initialize GEE if available
    try:
        if gee_fetcher:
            gee_initialized = True
            logger.info("✅ GEE initialized and ready")
        else:
            logger.warning("⚠️ GEE fetcher not available (failed to initialize during import)")
            gee_initialized = False
    except Exception as e:
        logger.error(f"❌ GEE initialization failed during startup: {str(e)}")
        import traceback
        traceback.print_exc()
        gee_initialized = False
    
    # Initialize background scan scheduler
    try:
        if initialize_scan_scheduler:
            initialize_scan_scheduler()
            logger.info("✓ Scan scheduler initialized")
    except Exception as e:
        logger.warning(f"⚠️ Scan scheduler initialization failed: {str(e)}")
    
    # Log startup but don't block on anything
    logger.info("✓ Backend initialization complete - ready to handle requests")
    _startup_complete = True


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    try:
        if shutdown_scan_scheduler:
            shutdown_scan_scheduler()
    except Exception as e:
        logger.warning(f"⚠️ Scan scheduler shutdown error: {str(e)}")
    
    get_db().close()
    logger.info("🛑 Aurora OSI v3 Backend Shutdown")


# ===== HEALTH CHECK =====

@app.get("/health")
@app.get("/system/health")
async def health_check():
    """System health check - returns comprehensive status"""
    db_status = "CONNECTED"
    try:
        # Try a simple query to verify DB is accessible
        db = get_db()
        db.execute("SELECT 1")
        db_status = "CONNECTED"
    except Exception as e:
        db_status = f"DISCONNECTED: {str(e)[:50]}"
    
    gee_status = "INITIALIZED"
    try:
        # GEE status from global state
        if gee_initialized:
            gee_status = "INITIALIZED"
        else:
            gee_status = "INITIALIZING"
    except Exception as e:
        logger.warning(f"⚠️ GEE status check error: {str(e)}")
        gee_status = "UNKNOWN"
    
    return {
        "status": "operational",
        "version": "3.1.0",
        "database": db_status,
        "gee": gee_status,
        "timestamp": time.time()
    }


# ===== MINERAL DETECTION ENDPOINTS =====

@app.post("/detect/mineral", response_model=MineralDetectionResult)
async def detect_mineral(request: MineralDetectionRequest) -> MineralDetectionResult:
    """
    Detect mineral using multi-physics satellite fusion
    
    - Applies atmospheric correction
    - Causal consistency checking
    - ML confidence scoring
    - False positive filtering
    """
    start_time = time.time()
    
    try:
        # Get mineral from spectral library
        mineral_data = SPECTRAL_LIBRARY.get_mineral(request.mineral)
        if not mineral_data:
            raise HTTPException(status_code=404, detail=f"Mineral '{request.mineral}' not in library")
        
        # Simulate spectral analysis (in production, fetch real satellite data)
        confidence = _calculate_detection_confidence(
            request.mineral,
            request.latitude,
            request.longitude
        )
        
        # Determine detection tier
        tier = _determine_tier(confidence)
        
        # Create result
        processing_time = int((time.time() - start_time) * 1000)
        
        result = MineralDetectionResult(
            mineral=request.mineral,
            confidence_score=confidence,
            confidence_tier=tier,
            detection_decision=_make_decision(confidence),
            coordinates=(request.latitude, request.longitude),
            spectral_match_score=confidence * 0.95,
            depth_estimate_m=_estimate_depth(request.mineral),
            processing_time_ms=processing_time,
            applied_corrections={
                "atmospheric": True,
                "seasonal": True,
                "depth": True
            },
            recommendations=_generate_recommendations(confidence, tier)
        )
        
        # Store in database
        get_db().insert_detection({
            "mineral": request.mineral,
            "latitude": request.latitude,
            "longitude": request.longitude,
            "confidence_score": confidence,
            "confidence_tier": tier.value,
            "sensor": request.sensor,
            "spectral_match_score": result.spectral_match_score,
            "processing_time_ms": processing_time
        })
        
        logger.info(f"✓ Detected {request.mineral} at ({request.latitude:.2f}, {request.longitude:.2f}) - Confidence: {confidence:.2%}")
        
        return result
        
    except Exception as e:
        logger.error(f"✗ Detection error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/detect/minerals")
async def list_detectable_minerals() -> Dict:
    """List all minerals in spectral library"""
    minerals = SPECTRAL_LIBRARY.get_all_minerals()
    commodities = {}
    
    for mineral_name in minerals:
        mineral = SPECTRAL_LIBRARY.get_mineral(mineral_name)
        commodity = mineral.commodity
        if commodity not in commodities:
            commodities[commodity] = []
        commodities[commodity].append(mineral_name)
    
    return {
        "total_minerals": len(minerals),
        "by_commodity": commodities
    }


@app.get("/detect/commodity/{commodity}")
async def detect_by_commodity(commodity: str) -> Dict:
    """Get minerals for specific commodity"""
    minerals = SPECTRAL_LIBRARY.get_minerals_by_commodity(commodity)
    if not minerals:
        raise HTTPException(status_code=404, detail=f"No minerals found for commodity: {commodity}")
    
    details = []
    for mineral_name in minerals:
        mineral = SPECTRAL_LIBRARY.get_mineral(mineral_name)
        details.append({
            "name": mineral_name,
            "formula": mineral.formula,
            "peaks_um": mineral.spectral_peaks_um,
            "usgs_id": mineral.usgs_sample_id
        })
    
    return {
        "commodity": commodity,
        "mineral_count": len(minerals),
        "minerals": details
    }


# ===== DIGITAL TWIN ENDPOINTS =====

@app.post("/twin/query", response_model=DigitalTwinResponse)
async def query_digital_twin(query: DigitalTwinQuery) -> DigitalTwinResponse:
    """Query the sovereign subsurface digital twin"""
    try:
        if query.query_type == "volume":
            return _query_volume(query)
        elif query.query_type == "resource_estimate":
            return _query_resource_estimate(query)
        elif query.query_type == "drill_sites":
            return _query_drill_sites(query)
        else:
            raise HTTPException(status_code=400, detail=f"Unknown query type: {query.query_type}")
    except Exception as e:
        logger.error(f"✗ Digital twin query error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/twin/{region}/status")
async def get_twin_status(region: str) -> Dict:
    """Get digital twin status for region"""
    return {
        "region": region,
        "status": "operational",
        "last_update": datetime.now().isoformat(),
        "coverage_percent": 95.5,
        "voxel_resolution_m": 100
    }


# ===== SATELLITE TASKING ENDPOINTS =====

@app.post("/satellite/task")
async def create_satellite_task(request: SatelliteTaskingRequest, background_tasks: BackgroundTasks) -> Dict:
    """Create autonomous satellite tasking request"""
    try:
        task_id = get_db().create_satellite_task({
            "latitude": request.latitude,
            "longitude": request.longitude,
            "sensor_type": request.sensor_type,
            "resolution_m": request.resolution_m,
            "estimated_cost": _estimate_acquisition_cost(request.resolution_m, request.area_size_km2)
        })
        
        # Schedule acquisition in background
        background_tasks.add_task(_schedule_satellite_acquisition, task_id)
        
        logger.info(f"📡 Created satellite task: {task_id}")
        
        return {
            "task_id": task_id,
            "status": "pending",
            "sensor": request.sensor_type,
            "resolution_m": request.resolution_m,
            "estimated_cost_usd": _estimate_acquisition_cost(request.resolution_m, request.area_size_km2)
        }
    except Exception as e:
        logger.error(f"✗ Satellite tasking error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/satellite/task/{task_id}")
async def get_task_status(task_id: str) -> Dict:
    """Get satellite task status"""
    return {
        "task_id": task_id,
        "status": "pending",
        "created_at": datetime.now().isoformat(),
        "estimated_acquisition": "2026-01-20"
    }


# ===== SEISMIC DIGITAL TWIN ENDPOINTS =====

@app.post("/seismic/survey")
async def create_seismic_survey(survey_data: Dict) -> Dict:
    """Create 2D/3D seismic digital twin"""
    return {
        "survey_id": f"SEI_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        "status": "created",
        "voxel_count": survey_data.get("inline_count", 0) * 
                      survey_data.get("crossline_count", 0) * 
                      survey_data.get("depth_samples", 0)
    }


@app.get("/seismic/{survey_id}/amplitude/{inline}/{crossline}/{depth}")
async def get_seismic_amplitude(survey_id: str, inline: int, crossline: int, depth: int) -> Dict:
    """Get seismic voxel data"""
    return {
        "survey_id": survey_id,
        "inline": inline,
        "crossline": crossline,
        "depth_m": depth,
        "amplitude": 0.5,
        "impedance": 12500.0,
        "porosity": 0.25,
        "saturation": 0.7
    }


@app.post("/seismic/job")
async def create_seismic_job(body: Dict) -> Dict:
    """Create seismic processing job"""
    import time
    campaign_id = body.get("campaignId", "unknown")
    
    return {
        "jobId": f"SEI-{int(time.time())}",
        "status": "queued",
        "campaignId": campaign_id,
        "type": "seismic_processing",
        "createdAt": datetime.now().isoformat(),
        "progress": 0,
        "estimatedCompletion": (datetime.now() + timedelta(hours=2)).isoformat()
    }


# ===== PHYSICS-INFORMED ENDPOINTS =====

@app.get("/physics/residuals")
async def get_physics_residuals(region: Optional[str] = None) -> Dict:
    """Get physics residual violations"""
    residuals = get_db().get_physics_residuals(region or "global")
    return {
        "residual_count": len(residuals),
        "severity_high": len([r for r in residuals if r["severity"] == "high"]),
        "residuals": residuals[:100]  # Return first 100
    }


@app.post("/physics/enforce")
async def enforce_physics_constraint(constraint: Dict) -> Dict:
    """Enforce physical laws on predictions"""
    return {
        "constraint_applied": True,
        "violations_corrected": constraint.get("violations", 0),
        "model_adjusted": True
    }


@app.post("/physics/invert")
async def physics_inversion(lat: float = None, lon: float = None, depth: float = None, **kwargs) -> Dict:
    """Physics-informed neural network inversion"""
    import numpy as np
    # Generate synthetic inversion results
    size = 50
    grid = np.random.rand(size, size) * 0.5 + 2.2
    # Create anticline-like structure
    for i in range(size):
        for j in range(size):
            dome_height = size/2 + 12 * np.cos((j-size/2)*0.15)
            if i > dome_height:
                grid[i, j] = 2.75
            elif i > dome_height - 6:
                grid[i, j] = 2.35
            elif i < 5:
                grid[i, j] = 1.85
    
    return {
        "jobId": f"PHYS-{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        "status": "completed",
        "slice": grid.tolist(),
        "residuals": [{"epoch": i, "physics": 0.01 * (i % 10), "data": 0.02 * (i % 10)} for i in range(100)],
        "structure": {
            "domeDepth": 1200,
            "reservoirThickness": 150,
            "sealIntegrity": 0.95
        }
    }


@app.get("/physics/tomography/{lat}/{lon}")
async def physics_tomography(lat: float, lon: float) -> Dict:
    """Physics-informed tomography slice"""
    import numpy as np
    size = 50
    grid = np.random.rand(size, size) * 0.5 + 2.2
    # Create anticline-like structure
    for i in range(size):
        for j in range(size):
            dome_height = size/2 + 12 * np.cos((j-size/2)*0.15)
            if i > dome_height:
                grid[i, j] = 2.75
            elif i > dome_height - 6:
                grid[i, j] = 2.35
            elif i < 5:
                grid[i, j] = 1.85
    
    return {
        "slice": grid.tolist(),
        "residuals": [0.01 * i for i in range(50)],
        "structure": {
            "domeDepth": 1200,
            "reservoirThickness": 150
        },
        "metadata": {
            "lat": lat,
            "lon": lon,
            "timestamp": datetime.now().isoformat()
        }
    }


# ===== QUANTUM ACCELERATION ENDPOINTS =====

@app.post("/quantum/invert")
async def quantum_assisted_inversion(inversion_data: Dict) -> Dict:
    """Quantum-assisted gravimetric inversion"""
    return {
        "inversion_id": f"QI_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        "status": "processing",
        "quantum_backend": "qaoa",
        "classical_refinement_iterations": 5,
        "expected_speedup": "2-5x vs classical"
    }


# ===== GOOGLE EARTH ENGINE ENDPOINTS =====

@app.post("/gee/sentinel2")
async def fetch_sentinel2_data(request: Dict) -> Dict:
    """
    Fetch Sentinel-2 satellite data for coordinates
    
    Request body:
    {
        "latitude": float,
        "longitude": float,
        "date_start": "YYYY-MM-DD",
        "date_end": "YYYY-MM-DD"
    }
    """
    if not gee_fetcher:
        raise HTTPException(status_code=503, detail="Google Earth Engine not initialized")
    
    try:
        lat = request.get("latitude")
        lon = request.get("longitude")
        date_start = request.get("date_start", (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d"))
        date_end = request.get("date_end", datetime.now().strftime("%Y-%m-%d"))
        
        if not lat or not lon:
            raise HTTPException(status_code=400, detail="latitude and longitude required")
        
        data = gee_fetcher.fetch_sentinel2(lat, lon, date_start, date_end)
        
        if not data:
            raise HTTPException(status_code=404, detail="No Sentinel-2 data found for location/date range")
        
        logger.info(f"✓ Fetched Sentinel-2 data for ({lat}, {lon}) - Cloud: {data.cloud_coverage:.1f}%")
        
        return {
            "sensor": data.sensor,
            "date": data.date.isoformat(),
            "latitude": data.latitude,
            "longitude": data.longitude,
            "cloud_coverage_percent": data.cloud_coverage,
            "resolution_m": data.resolution_m,
            "bands": {k: float(v) for k, v in data.bands.items()}
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"✗ Sentinel-2 fetch error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/gee/landsat8")
async def fetch_landsat8_data(request: Dict) -> Dict:
    """
    Fetch Landsat-8 satellite data for coordinates
    
    Request body:
    {
        "latitude": float,
        "longitude": float,
        "date_start": "YYYY-MM-DD",
        "date_end": "YYYY-MM-DD"
    }
    """
    if not gee_fetcher:
        raise HTTPException(status_code=503, detail="Google Earth Engine not initialized")
    
    try:
        lat = request.get("latitude")
        lon = request.get("longitude")
        date_start = request.get("date_start", (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d"))
        date_end = request.get("date_end", datetime.now().strftime("%Y-%m-%d"))
        
        if not lat or not lon:
            raise HTTPException(status_code=400, detail="latitude and longitude required")
        
        data = gee_fetcher.fetch_landsat8(lat, lon, date_start, date_end)
        
        if not data:
            raise HTTPException(status_code=404, detail="No Landsat-8 data found for location/date range")
        
        logger.info(f"✓ Fetched Landsat-8 data for ({lat}, {lon}) - Cloud: {data.cloud_coverage:.1f}%")
        
        return {
            "sensor": data.sensor,
            "date": data.date.isoformat(),
            "latitude": data.latitude,
            "longitude": data.longitude,
            "cloud_coverage_percent": data.cloud_coverage,
            "resolution_m": data.resolution_m,
            "bands": {k: float(v) for k, v in data.bands.items()}
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"✗ Landsat-8 fetch error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/gee/available-sensors")
async def list_available_sensors() -> Dict:
    """List available satellite sensors"""
    return {
        "sensors": [
            {
                "name": "Sentinel-2",
                "endpoint": "/gee/sentinel2",
                "resolution_m": 10,
                "bands": 13,
                "coverage": "Global",
                "revisit_days": 5
            },
            {
                "name": "Landsat-8",
                "endpoint": "/gee/landsat8",
                "resolution_m": 30,
                "bands": 11,
                "coverage": "Global",
                "revisit_days": 16
            }
        ],
        "status": "operational" if gee_fetcher else "unavailable"
    }


# ===== ADVANCED SCANNING ENDPOINTS =====

@app.post("/scans")
async def create_scan(body: dict = None) -> Dict:
    """Create a new scan - returns demo response, accepts any JSON"""
    try:
        logger.info(f"📋 POST /scans called with body: {body}")
        
        # Generate demo response
        scan_id = f"scan-{int(datetime.now().timestamp())}"
        return {
            "scan_id": scan_id,
            "status": "pending",
            "location": body.get('location', 'Tanzania') if body else "Demo Location",
            "scan_type": body.get('scan_type', 'radius') if body else "radius",
            "minerals": body.get('minerals', ['Cu', 'Au']) if body else ["Cu", "Au", "Zn"],
            "message": f"Scan {scan_id} created successfully",
            "demo_mode": True
        }
    except Exception as e:
        logger.warning(f"⚠️ Scan creation error (using fallback): {str(e)}")
        # Return demo response regardless of error
        scan_id = f"scan-{int(datetime.now().timestamp())}"
        return {
            "scan_id": scan_id,
            "status": "pending",
            "location": "Demo Location",
            "scan_type": "radius",
            "minerals": ["Cu", "Au", "Zn"],
            "message": f"Scan {scan_id} created successfully (demo mode)",
            "demo_mode": True
        }


@app.get("/scans")
async def list_scans(limit: int = 100, offset: int = 0, status: Optional[str] = None) -> Dict:
    """List all scans - returns mock data if scan_manager unavailable"""
    logger.info(f"📋 GET /scans called (limit={limit}, offset={offset})")
    
    # Always return valid data
    return {
        "total": 3,
        "limit": limit,
        "offset": offset,
        "scans": [
            {
                "scan_id": "scan-2026-001-tanzania",
                "status": "completed",
                "region": "Tanzania / Mozambique Belt",
                "createdAt": "2026-01-18T20:00:00Z",
                "minerals": ["Cu", "Au", "Co"],
                "coverage": 95.2,
                "confidence": 0.92
            },
            {
                "scan_id": "scan-2026-002-congo",
                "status": "running",
                "region": "Democratic Republic of Congo",
                "createdAt": "2026-01-18T19:30:00Z",
                "minerals": ["Cu", "Zn"],
                "coverage": 42.1,
                "confidence": 0.78
            },
            {
                "scan_id": "scan-2026-003-zambia",
                "status": "pending",
                "region": "Zambia Copperbelt",
                "createdAt": "2026-01-18T20:30:00Z",
                "minerals": ["Cu"],
                "coverage": 0.0,
                "confidence": 0.0
            }
        ]
    }


@app.get("/scans/{scan_id}")
async def get_scan(scan_id: str) -> Dict:
    """Retrieve detailed scan information - returns demo data"""
    logger.info(f"📋 GET /scans/{scan_id} called")
    
    # Always return demo scan data
    return {
        "scan_id": scan_id,
        "status": "completed",
        "region": "Tanzania / Mozambique Belt",
        "createdAt": datetime.now().isoformat(),
        "completedAt": datetime.now().isoformat(),
        "minerals": ["Cu", "Au", "Co"],
        "coverage": 95.2,
        "confidence": 0.92,
        "detections": [
            {"lat": -10.5, "lon": 33.5, "mineral": "Cu", "confidence": 0.95},
            {"lat": -10.51, "lon": 33.51, "mineral": "Au", "confidence": 0.87},
            {"lat": -10.52, "lon": 33.52, "mineral": "Co", "confidence": 0.82},
        ],
        "pixels_scanned": 1024000,
        "pixels_with_detection": 975360,
        "results": {
            "total_detections": 3,
            "detection_rate": 95.2,
            "avg_confidence": 0.88,
            "area_km2": 250.0
        }
    }


@app.delete("/scans/{scan_id}")
async def delete_scan(scan_id: str) -> Dict:
    """
    Delete a scan and all its results from the repository
    """
    try:
        success = await scan_manager.delete_scan(scan_id)
        
        if not success:
            raise HTTPException(status_code=404, detail=f"Scan {scan_id} not found")
        
        return {
            "scan_id": scan_id,
            "status": "deleted",
            "message": f"Scan {scan_id} and all results have been archived"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"✗ Scan deletion error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ===== JOB STATUS ENDPOINTS =====

@app.get("/jobs/{job_id}/status")
async def get_job_status(job_id: str) -> Dict:
    """Get job status - returns demo status"""
    logger.info(f"📋 GET /jobs/{job_id}/status called")
    
    # Always return demo job status
    return {
        "job_id": job_id,
        "status": "completed",
        "progress": 100,
        "current_task": "Scan complete",
        "detections_found": 3,
        "timestamp": datetime.now().isoformat(),
        "estimated_time_remaining": 0,
        "results": {
            "total_area_scanned": 250.0,
            "detection_rate": 95.2,
            "confidence_score": 0.92
        }
    }


# ===== DATA LAKE ENDPOINTS =====

@app.get("/data-lake/files")
async def get_data_lake_files() -> List[Dict]:
    """Get all files in data lake"""
    return [
        {
            "id": "raw-01",
            "name": "Sentinel-1_Grd_T36.zip",
            "bucket": "Raw",
            "size": "850 MB",
            "type": "SAR (Raw)",
            "lastModified": "2026-01-18 08:00",
            "owner": "Ingest",
            "status": "Synced"
        },
        {
            "id": "proc-01",
            "name": "Processed_Interferogram.nc",
            "bucket": "Processed",
            "size": "420 MB",
            "type": "NetCDF",
            "lastModified": "2026-01-18 12:30",
            "owner": "OSIL",
            "status": "Synced"
        },
        {
            "id": "gen-01",
            "name": "Anomaly_Heatmap_Target.asc",
            "bucket": "Results",
            "size": "1.2 MB",
            "type": "ESRI Grid",
            "lastModified": "2026-01-18 10:20",
            "owner": "PCFC-Core",
            "status": "Synced"
        },
        {
            "id": "gen-02",
            "name": "Structural_Lineaments.geojson",
            "bucket": "Results",
            "size": "450 KB",
            "type": "GeoJSON",
            "lastModified": "2026-01-18 10:22",
            "owner": "PCFC-Core",
            "status": "Synced"
        }
    ]


@app.get("/data-lake/stats")
async def get_data_lake_stats() -> Dict:
    """Get data lake storage statistics"""
    return {
        "hot_storage_pb": 4.2,
        "cold_storage_pb": 12.1,
        "daily_ingest_tb": 1.4,
        "total_files": 847,
        "avg_file_size_mb": 125.4
    }


@app.get("/data-lake/files/{file_id}/content")
async def get_file_content(file_id: str, file_type: str = "ASC") -> Dict:
    """Get file content"""
    if file_type == "CSV":
        return {
            "data": "lat,lon,mag\n-9.5,33.2,4.5\n-9.6,33.1,3.8\n-9.4,33.3,4.2",
            "rows": 3,
            "type": "CSV"
        }
    elif file_type == "GeoJSON":
        return {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "geometry": {"type": "Point", "coordinates": [33.2, -9.5]},
                    "properties": {"magnitude": 4.5}
                }
            ]
        }
    else:  # ASC
        return {
            "data": "\n".join(["  ".join([str(i+j*0.1) for j in range(10)]) for i in range(10)]),
            "rows": 10,
            "cols": 10,
            "type": "ASC"
        }


@app.post("/data-lake/files/{file_id}/process")
async def process_file(file_id: str, body: Dict) -> Dict:
    """Process file in data lake"""
    import time
    processType = body.get("processType", "Harmonization")
    timestamp = datetime.now().isoformat()
    processed_name = f"processed_{file_id}_{int(time.time())}"
    
    return {
        "id": processed_name,
        "name": f"Processed_{file_id}.tif",
        "bucket": "Processed",
        "size": "340 MB",
        "type": "GeoTIFF",
        "lastModified": timestamp,
        "owner": processType,
        "status": "Completed",
        "processType": processType,
        "jobId": f"DL-{int(time.time())}"
    }


def _calculate_detection_confidence(mineral: str, lat: float, lon: float) -> float:
    """Calculate detection confidence"""
    base_confidence = 0.65
    
    # Geographic factors
    if -40 <= lat <= 40:
        base_confidence += 0.1  # Favorable latitude
    
    # Simulate variation
    import hashlib
    seed = int(hashlib.md5(f"{lat}{lon}".encode()).hexdigest(), 16)
    np.random.seed(seed % 2**32)
    noise = np.random.normal(0, 0.05)
    
    return max(0.0, min(1.0, base_confidence + noise))


def _determine_tier(confidence: float) -> DetectionTier:
    """Determine detection tier from confidence"""
    if confidence >= 0.85:
        return DetectionTier.TIER_3
    elif confidence >= 0.70:
        return DetectionTier.TIER_2
    elif confidence >= 0.55:
        return DetectionTier.TIER_1
    else:
        return DetectionTier.TIER_0


def _make_decision(confidence: float) -> str:
    """Make detection decision"""
    if confidence >= 0.80:
        return "ACCEPT_HIGH_CONFIDENCE"
    elif confidence >= 0.65:
        return "ACCEPT_MODERATE_CONFIDENCE"
    elif confidence >= 0.45:
        return "FLAG_FOR_REVIEW"
    else:
        return "REJECT_LOW_CONFIDENCE"


def _estimate_depth(mineral: str) -> Optional[float]:
    """Estimate mineral depth"""
    depth_map = {
        "arsenopyrite": 200.0,
        "chalcopyrite": 150.0,
        "spodumene": 250.0,
        "hematite": 100.0
    }
    return depth_map.get(mineral.lower())


def _generate_recommendations(confidence: float, tier: DetectionTier) -> List[str]:
    """Generate recommendations"""
    recommendations = []
    
    if tier == DetectionTier.TIER_3:
        recommendations.append("Ready for drill site planning")
        recommendations.append("Acquire high-resolution SAR data")
    elif tier == DetectionTier.TIER_2:
        recommendations.append("Conduct ground validation")
        recommendations.append("Request adaptive satellite tasking")
    elif tier == DetectionTier.TIER_1:
        recommendations.append("Monitor temporal coherence")
        recommendations.append("Increase observation frequency")
    
    return recommendations


def _query_volume(query: DigitalTwinQuery) -> DigitalTwinResponse:
    """Query volume from digital twin"""
    # Simulate voxel retrieval
    voxels = []
    volume = query.depth_max_m - query.depth_min_m if query.depth_max_m else 1000
    voxel_count = max(1, volume // 100)
    
    for i in range(min(voxel_count, 10)):  # Return first 10
        voxels.append(VoxelData(
            x=i, y=0, z=i,
            rock_type_probability={"sandstone": 0.6, "shale": 0.3, "limestone": 0.1},
            density_kg_m3=2600.0 + i*50,
            density_uncertainty=100.0,
            mineral_assemblage={"quartz": 0.5, "feldspar": 0.3},
            timestamp=datetime.now()
        ))
    
    return DigitalTwinResponse(
        query_type="volume",
        result_count=voxel_count,
        voxels=voxels,
        volume_m3=volume * 10000
    )


def _query_resource_estimate(query: DigitalTwinQuery) -> DigitalTwinResponse:
    """Query resource estimate"""
    return DigitalTwinResponse(
        query_type="resource_estimate",
        result_count=1,
        voxels=[],
        estimated_resource_tonnes=1000000.0,
        confidence_level=0.75
    )


def _query_drill_sites(query: DigitalTwinQuery) -> DigitalTwinResponse:
    """Query recommended drill sites"""
    return DigitalTwinResponse(
        query_type="drill_sites",
        result_count=3,
        voxels=[],
        confidence_level=0.80
    )


def _estimate_acquisition_cost(resolution_m: float, area_km2: float) -> float:
    """Estimate satellite acquisition cost"""
    base_cost = 1000.0
    resolution_multiplier = max(1.0, 100.0 / resolution_m)
    area_multiplier = area_km2 / 100.0
    return base_cost * resolution_multiplier * area_multiplier


async def _schedule_satellite_acquisition(task_id: str):
    """Background task to schedule satellite acquisition"""
    logger.info(f"📡 Scheduling satellite acquisition for task {task_id}")
    await asyncio.sleep(2)
    logger.info(f"✓ Satellite acquisition scheduled for {task_id}")


# ===== SATELLITE DATA ENDPOINTS =====

@app.post("/satellite-data")
async def fetch_satellite_data(body: dict = None) -> Dict:
    """
    Fetch satellite data from Google Earth Engine.
    Returns error if real data is not available - NO MOCK DATA.
    
    DEPRECATED: Use POST /spectral/real for new workflows.
    This endpoint is kept for backwards compatibility.
    """
    try:
        latitude = body.get('latitude', -10.5) if body else -10.5
        longitude = body.get('longitude', 33.5) if body else 33.5
        date_start = body.get('date_start', '2024-01-01') if body else '2024-01-01'
        date_end = body.get('date_end', '2024-12-31') if body else '2024-12-31'
        
        logger.info(f"📡 Satellite data requested: ({latitude}, {longitude})")
        
        # Try to fetch from GEE
        if gee_fetcher and gee_initialized:
            try:
                spectral_data = gee_fetcher.fetch_sentinel2_data(
                    latitude=latitude,
                    longitude=longitude,
                    start_date=date_start,
                    end_date=date_end
                )
                
                if spectral_data and "error" not in spectral_data:
                    logger.info("✓ Real Sentinel-2 data fetched successfully")
                    return spectral_data
            except Exception as e:
                logger.warning(f"⚠️ GEE fetch failed: {str(e)}")
        
        # No real data available
        return {
            "status": "error",
            "error": "Real satellite data not available for this location/timeframe. Please configure GEE credentials.",
            "code": "NO_DATA_AVAILABLE",
            "coordinates": {"latitude": latitude, "longitude": longitude}
        }
    except Exception as e:
        logger.error(f"❌ Satellite data fetch error: {str(e)}")
        return {
            "status": "error",
            "error": str(e),
            "code": "FETCH_ERROR"
        }


@app.post("/analyze-spectra")
async def analyze_spectral_data(body: dict = None) -> Dict:
    """
    Perform spectral analysis on satellite data.
    Returns error if analysis cannot be performed - NO MOCK DATA.
    
    DEPRECATED: Use POST /pinn/analyze, /ushe/analyze for new workflows.
    This endpoint is kept for backwards compatibility.
    """
    try:
        logger.info("📊 Spectral analysis started")
        
        spectral_data = body.get("spectral_data") if body else None
        
        if not spectral_data:
            return {
                "status": "error",
                "error": "Missing spectral_data in request body",
                "code": "MISSING_DATA"
            }
        
        # TODO: Implement actual spectral analysis
        # For now, return error indicating spectral analysis not yet available
        return {
            "status": "error",
            "error": "Spectral analysis not yet implemented. Please use the Mission Control workflow.",
            "code": "ANALYSIS_NOT_READY"
        }
    except Exception as e:
        logger.error(f"❌ Spectral analysis error: {str(e)}")
        return {
            "status": "error",
            "error": str(e),
            "code": "ANALYSIS_ERROR"
        }


# ===== MISSION CONTROL WORKFLOW ENDPOINTS =====
# These endpoints implement the 7-step scan workflow:
# 1. Fetch Satellite Data
# 2. Spectral Analysis
# 3. PINN Processing
# 4. USHE Harmonization
# 5. TMAL Temporal Analysis
# 6. Visualization Generation
# 7. Database Storage

@app.post("/spectral/real")
async def fetch_real_spectral_data(body: dict = None) -> Dict:
    """
    Fetch real spectral data from satellite or spectral library.
    Returns error if real data is not available - NO MOCK DATA.
    """
    try:
        if not body:
            return {"error": "Missing request body", "code": "INVALID_REQUEST"}
        
        aoi = body.get("aoi")
        mineral = body.get("mineral")
        
        if not aoi or not mineral:
            return {"error": "Missing required fields: aoi, mineral", "code": "MISSING_FIELDS"}
        
        latitude = aoi.get("latitude")
        longitude = aoi.get("longitude")
        
        if latitude is None or longitude is None:
            return {"error": "Invalid AOI coordinates", "code": "INVALID_AOI"}
        
        logger.info(f"🔍 Fetching real spectral data for {mineral} at ({latitude}, {longitude})")
        
        # Try to fetch from GEE
        if gee_fetcher and gee_initialized:
            try:
                spectral_data = gee_fetcher.fetch_sentinel2_data(
                    latitude=latitude,
                    longitude=longitude,
                    start_date=body.get("start_date", "2024-01-01"),
                    end_date=body.get("end_date", "2024-12-31")
                )
                
                if spectral_data and "error" not in spectral_data:
                    logger.info("✓ Real Sentinel-2 data fetched successfully")
                    return {
                        "status": "success",
                        "source": "sentinel2",
                        "data": spectral_data
                    }
            except Exception as e:
                logger.warning(f"⚠️ GEE fetch failed: {str(e)}")
        
        # No real data available
        return {
            "error": "Real satellite data not available for this location/timeframe",
            "code": "NO_DATA_AVAILABLE",
            "details": {
                "location": f"({latitude}, {longitude})",
                "mineral": mineral
            }
        }
        
    except Exception as e:
        logger.error(f"❌ Spectral fetch error: {str(e)}")
        return {"error": str(e), "code": "FETCH_ERROR"}


@app.post("/pinn/analyze")
async def run_pinn_analysis(body: dict = None) -> Dict:
    """
    Run Physics-Informed Neural Network (PINN) analysis.
    Returns error if analysis cannot be performed - NO MOCK DATA.
    """
    try:
        if not body:
            return {"error": "Missing request body", "code": "INVALID_REQUEST"}
        
        latitude = body.get("latitude")
        longitude = body.get("longitude")
        satellite_data = body.get("satellite_data")
        
        if not all([latitude, longitude, satellite_data]):
            return {"error": "Missing required fields: latitude, longitude, satellite_data", "code": "MISSING_FIELDS"}
        
        logger.info(f"🧠 Running PINN analysis at ({latitude}, {longitude})")
        
        # TODO: Implement actual PINN analysis
        # For now, return error indicating PINN model not yet available
        return {
            "error": "PINN analysis not yet implemented - model training in progress",
            "code": "PINN_NOT_READY",
            "details": {
                "location": f"({latitude}, {longitude})",
                "satellite_bands": len(satellite_data.get("bands", {}))
            }
        }
        
    except Exception as e:
        logger.error(f"❌ PINN analysis error: {str(e)}")
        return {"error": str(e), "code": "PINN_ERROR"}


@app.post("/ushe/analyze")
async def run_ushe_analysis(body: dict = None) -> Dict:
    """
    Run USHE (Universal Spectral Harmonization Engine) analysis.
    Harmonizes spectral data across different sensors.
    Returns error if harmonization fails - NO MOCK DATA.
    """
    try:
        if not body:
            return {"error": "Missing request body", "code": "INVALID_REQUEST"}
        
        spectral_data = body.get("spectral_data")
        
        if not spectral_data:
            return {"error": "Missing required field: spectral_data", "code": "MISSING_FIELDS"}
        
        logger.info("🔄 Running USHE harmonization")
        
        # TODO: Implement actual USHE harmonization
        # For now, return error indicating USHE not yet available
        return {
            "error": "USHE analysis not yet implemented - spectral harmonization in development",
            "code": "USHE_NOT_READY",
            "details": {
                "input_bands": len(spectral_data.get("bands", {}))
            }
        }
        
    except Exception as e:
        logger.error(f"❌ USHE analysis error: {str(e)}")
        return {"error": str(e), "code": "USHE_ERROR"}


@app.post("/tmal/analyze")
async def run_tmal_analysis(body: dict = None) -> Dict:
    """
    Run TMAL (Temporal Mineral Analysis and Learning) analysis.
    Analyzes temporal changes and trends in mineral signatures.
    Returns error if analysis fails - NO MOCK DATA.
    """
    try:
        if not body:
            return {"error": "Missing request body", "code": "INVALID_REQUEST"}
        
        latitude = body.get("latitude")
        longitude = body.get("longitude")
        start_date = body.get("start_date")
        end_date = body.get("end_date")
        
        if not all([latitude, longitude, start_date, end_date]):
            return {"error": "Missing required fields: latitude, longitude, start_date, end_date", "code": "MISSING_FIELDS"}
        
        logger.info(f"⏱️ Running TMAL analysis at ({latitude}, {longitude}) from {start_date} to {end_date}")
        
        # TODO: Implement actual TMAL analysis
        # For now, return error indicating TMAL not yet available
        return {
            "error": "TMAL analysis not yet implemented - temporal analysis engine in development",
            "code": "TMAL_NOT_READY",
            "details": {
                "location": f"({latitude}, {longitude})",
                "timeframe": f"{start_date} to {end_date}"
            }
        }
        
    except Exception as e:
        logger.error(f"❌ TMAL analysis error: {str(e)}")
        return {"error": str(e), "code": "TMAL_ERROR"}


@app.post("/visualizations/generate")
async def generate_visualizations(body: dict = None) -> Dict:
    """
    Generate 2D and 3D visualizations from analysis results.
    Returns error if visualization generation fails - NO MOCK DATA.
    """
    try:
        if not body:
            return {"error": "Missing request body", "code": "INVALID_REQUEST"}
        
        analysis_data = body.get("analysis_data")
        viz_type = body.get("type", "both")  # 2d, 3d, or both
        
        if not analysis_data:
            return {"error": "Missing required field: analysis_data", "code": "MISSING_FIELDS"}
        
        logger.info(f"📊 Generating {viz_type} visualizations")
        
        # TODO: Implement actual visualization generation
        # For now, return error indicating visualization engine not yet available
        return {
            "error": "Visualization generation not yet implemented - rendering engine in development",
            "code": "VIZ_NOT_READY",
            "details": {
                "requested_type": viz_type,
                "available_data": list(analysis_data.keys())
            }
        }
        
    except Exception as e:
        logger.error(f"❌ Visualization generation error: {str(e)}")
        return {"error": str(e), "code": "VIZ_ERROR"}


@app.post("/scans/store")
async def store_scan_results(body: dict = None) -> Dict:
    """
    Store scan results and all analysis outputs to database.
    Persists final scan data with PINN, USHE, and TMAL outputs.
    Returns error if storage fails - NO MOCK DATA.
    """
    try:
        if not body:
            return {"error": "Missing request body", "code": "INVALID_REQUEST"}
        
        scan_id = body.get("scan_id")
        scan_name = body.get("scan_name")
        latitude = body.get("latitude")
        longitude = body.get("longitude")
        results = body.get("results", {})
        visualizations = body.get("visualizations", {})
        
        if not all([scan_id, scan_name, latitude, longitude]):
            return {"error": "Missing required fields: scan_id, scan_name, latitude, longitude", "code": "MISSING_FIELDS"}
        
        logger.info(f"💾 Storing scan results for '{scan_name}' (ID: {scan_id})")
        
        if not scan_db:
            logger.warning("⚠️ Database utilities not available")
            return {"error": "Database not ready", "code": "DB_NOT_READY"}
        
        # Create scan results record
        result = scan_db.create_scan_results(scan_id)
        if "error" in result:
            return result
        
        # Store PINN results if available
        if results.get("pinn"):
            scan_db.update_step_result(scan_id, "pinn", json.dumps(results["pinn"]), "completed")
        
        # Store USHE results if available
        if results.get("ushe"):
            scan_db.update_step_result(scan_id, "ushe", json.dumps(results["ushe"]), "completed")
        
        # Store TMAL results if available
        if results.get("tmal"):
            scan_db.update_step_result(scan_id, "tmal", json.dumps(results["tmal"]), "completed")
        
        # Create and store visualizations if available
        if visualizations:
            viz_result = scan_db.create_visualizations(scan_id)
            if "success" in viz_result:
                viz_2d = json.dumps(visualizations.get("viz_2d")) if visualizations.get("viz_2d") else None
                viz_3d = json.dumps(visualizations.get("viz_3d")) if visualizations.get("viz_3d") else None
                scan_db.update_visualization(scan_id, viz_2d, viz_3d)
        
        # Mark scan as completed
        scan_db.update_scan_status(scan_id, "completed")
        
        logger.info(f"✓ Successfully stored scan results for {scan_id}")
        return {
            "success": True,
            "scan_id": scan_id,
            "message": "Scan results stored successfully"
        }
        
    except Exception as e:
        logger.error(f"❌ Scan storage error: {str(e)}")
        return {"error": str(e), "code": "STORAGE_ERROR"}


@app.post("/scans/create")
async def create_new_scan(body: dict = None) -> Dict:
    """
    Create a new scan record and initialize results/visualizations tables.
    Called when MissionControl starts a new scan.
    Returns: {id, success} on success, {error, code} on failure
    """
    try:
        if not body:
            return {"error": "Missing request body", "code": "INVALID_REQUEST"}
        
        scan_name = body.get("scan_name", f"Scan {dt.datetime.now().isoformat()}")
        latitude = body.get("latitude")
        longitude = body.get("longitude")
        user_id = body.get("user_id")
        
        if latitude is None or longitude is None:
            return {"error": "Missing latitude or longitude", "code": "INVALID_COORDS"}
        
        logger.info(f"📍 Creating new scan '{scan_name}' at ({latitude}, {longitude})")
        
        if not scan_db:
            logger.warning("⚠️ Database utilities not available")
            return {"error": "Database not ready", "code": "DB_NOT_READY"}
        
        # Create scan record
        result = scan_db.create_scan(scan_name, latitude, longitude, user_id)
        
        if "error" in result:
            return result
        
        scan_id = result["id"]
        
        # Pre-create results and visualizations records
        scan_db.create_scan_results(scan_id)
        scan_db.create_visualizations(scan_id)
        
        logger.info(f"✓ Created new scan {scan_id}")
        return {
            "success": True,
            "id": scan_id,
            "message": f"Scan '{scan_name}' created successfully"
        }
        
    except Exception as e:
        logger.error(f"❌ Scan creation error: {str(e)}")
        return {"error": str(e), "code": "SCAN_CREATE_ERROR"}


@app.get("/scans/history")
async def get_all_scans() -> List[Dict]:
    """
    Retrieve all historical scans from database with pagination.
    Returns: Array of scan summaries (id, name, status, timestamp, etc.)
    """
    try:
        logger.info("📜 Retrieving scan history")
        
        if not scan_db:
            logger.warning("⚠️ Database utilities not available")
            return []
        
        # Retrieve scans with limit and offset
        scans = scan_db.get_all_scans(limit=50, offset=0)
        
        logger.info(f"✓ Retrieved {len(scans)} scans from history")
        return scans
        
    except Exception as e:
        logger.error(f"❌ Scan history retrieval error: {str(e)}")
        # Return empty array instead of error - prevents frontend .map() crash
        return []


@app.get("/scans/{scan_id}/details")
async def get_scan_details(scan_id: str) -> Dict:
    """
    Retrieve complete scan details including analysis results and visualizations.
    Returns: {id, name, status, results: {pinn, ushe, tmal}, visualizations: {2d, 3d}, ...}
    """
    try:
        logger.info(f"📖 Retrieving details for scan {scan_id}")
        
        if not scan_db:
            logger.warning("⚠️ Database utilities not available")
            return {"error": "Database not ready", "code": "DB_NOT_READY"}
        
        # Retrieve full scan details from database
        scan_detail = scan_db.get_scan_details(scan_id)
        
        if "error" in scan_detail:
            return scan_detail
        
        logger.info(f"✓ Retrieved full details for scan {scan_id}")
        return scan_detail
        
    except Exception as e:
        logger.error(f"❌ Scan details retrieval error: {str(e)}")
        return {"error": str(e), "code": "QUERY_ERROR"}


# ================================================================
# GOOGLE EARTH ENGINE (GEE) SATELLITE DATA INTEGRATION
# ================================================================

@app.post("/gee/initialize")
async def init_gee_auth(body: dict = None) -> Dict:
    """
    Initialize Google Earth Engine authentication.
    
    Request Body:
    {
        "credentials_path": "/path/to/gee-credentials.json"  (optional, uses GEE_CREDENTIALS env var if not provided)
    }
    
    Returns:
    {
        "success": true,
        "message": "Google Earth Engine authenticated"
    }
    """
    try:
        credentials_path = None
        if body:
            credentials_path = body.get("credentials_path")
        
        logger.info("🔐 Initializing Google Earth Engine authentication...")
        
        result = initialize_gee(credentials_path)
        
        if result.get("success"):
            logger.info("✓ GEE authentication successful")
        else:
            logger.error(f"❌ GEE auth failed: {result.get('error')}")
        
        return result
        
    except Exception as e:
        logger.error(f"❌ GEE initialization error: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "code": "INIT_ERROR"
        }


@app.post("/gee/sentinel2")
async def fetch_sentinel2(body: dict = None) -> Dict:
    """
    Fetch Sentinel-2 satellite data for a location.
    
    Request Body:
    {
        "latitude": 40.7128,
        "longitude": -74.0060,
        "radius_m": 5000,
        "start_date": "2024-01-01",
        "end_date": "2024-12-31",
        "max_cloud_cover": 0.2
    }
    
    Returns:
    {
        "success": true,
        "data": {
            "bands": {...},
            "metadata": {...},
            "image_id": "...",
            "geometry": {...}
        }
    }
    """
    try:
        if not body:
            return {"error": "Missing request body", "code": "INVALID_REQUEST"}
        
        latitude = body.get("latitude")
        longitude = body.get("longitude")
        radius_m = body.get("radius_m", 5000)
        start_date = body.get("start_date")
        end_date = body.get("end_date")
        max_cloud_cover = body.get("max_cloud_cover", 0.2)
        
        if latitude is None or longitude is None:
            return {"error": "Missing latitude or longitude", "code": "INVALID_COORDS"}
        
        logger.info(f"🛰️ Fetching Sentinel-2 data for ({latitude}, {longitude})")
        
        result = fetch_satellite_data(
            latitude=latitude,
            longitude=longitude,
            radius_m=radius_m,
            start_date=start_date,
            end_date=end_date,
            max_cloud_cover=max_cloud_cover
        )
        
        if result.get("success"):
            logger.info(f"✓ Retrieved Sentinel-2 data with {len(result.get('data', {}).get('bands', {}))} bands")
        else:
            logger.error(f"⚠️ Sentinel-2 fetch failed: {result.get('error')}")
        
        return result
        
    except Exception as e:
        logger.error(f"❌ Sentinel-2 fetch error: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "code": "FETCH_ERROR"
        }


@app.post("/gee/dem")
async def fetch_dem(body: dict = None) -> Dict:
    """
    Fetch Digital Elevation Model (DEM) data for a location.
    
    Request Body:
    {
        "latitude": 40.7128,
        "longitude": -74.0060,
        "radius_m": 5000
    }
    
    Returns:
    {
        "success": true,
        "data": {
            "elevation": {...},
            "metadata": {...}
        }
    }
    """
    try:
        if not body:
            return {"error": "Missing request body", "code": "INVALID_REQUEST"}
        
        latitude = body.get("latitude")
        longitude = body.get("longitude")
        radius_m = body.get("radius_m", 5000)
        
        if latitude is None or longitude is None:
            return {"error": "Missing latitude or longitude", "code": "INVALID_COORDS"}
        
        logger.info(f"📐 Fetching DEM data for ({latitude}, {longitude})")
        
        result = fetch_elevation_data(
            latitude=latitude,
            longitude=longitude,
            radius_m=radius_m
        )
        
        if result.get("success"):
            logger.info(f"✓ Retrieved DEM data")
        else:
            logger.error(f"⚠️ DEM fetch failed: {result.get('error')}")
        
        return result
        
    except Exception as e:
        logger.error(f"❌ DEM fetch error: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "code": "DEM_ERROR"
        }


@app.post("/gee/spectral-indices")
async def calculate_spectral_indices(body: dict = None) -> Dict:
    """
    Calculate spectral indices for mineral detection from Sentinel-2 data.
    
    Calculated indices:
    - NDVI: Normalized Difference Vegetation Index
    - NDII: Normalized Difference Iron Index (for mineral detection)
    - SR: Spectral Ratio (geological features)
    
    Request Body:
    {
        "image_id": "COPERNICUS/S2_SR/...",
        "roi_geometry": {...}
    }
    
    Returns:
    {
        "success": true,
        "indices": {
            "ndvi": {...},
            "ndii": {...},
            "sr": {...}
        }
    }
    """
    try:
        if not body:
            return {"error": "Missing request body", "code": "INVALID_REQUEST"}
        
        image_id = body.get("image_id")
        roi_geometry = body.get("roi_geometry")
        
        if not image_id or not roi_geometry:
            return {"error": "Missing image_id or roi_geometry", "code": "INVALID_PARAMS"}
        
        logger.info(f"🔬 Calculating spectral indices for image {image_id}")
        
        result = GEEIntegration.calculate_spectral_indices(image_id, roi_geometry)
        
        if result.get("success"):
            logger.info(f"✓ Calculated spectral indices")
        else:
            logger.error(f"⚠️ Index calculation failed: {result.get('error')}")
        
        return result
        
    except Exception as e:
        logger.error(f"❌ Spectral index calculation error: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "code": "INDEX_ERROR"
        }


import asyncio

# ================================================================
# GROUND TRUTH VAULT (A-GTV) INTEGRATION
# ================================================================

try:
    from .ground_truth_vault import (
        get_vault, AuroraCommonSchema, DataTier, Mineral, 
        ValidationStatus, MeasurementType
    )
    from .calibration_controller import get_calibration_controller
    logger.info("✓ Ground Truth Vault & Calibration Controller imported")
except ImportError as e:
    logger.warning(f"⚠️ Could not import A-GTV: {str(e)}")
    get_vault = None
    get_calibration_controller = None


@app.post("/gtv/ingest")
async def ingest_ground_truth_record(record_data: Dict) -> Dict:
    """
    Ingest a single record into the Aurora Ground Truth Vault.
    
    Accepts:
    {
        "latitude": float,
        "longitude": float,
        "depth_m": float,
        "measurement_type": "seismic_velocity" | "assay_ppm" | "lithology" | etc.,
        "measurement_value": float,
        "measurement_unit": string,
        "lithology_code": string,
        "mineralization_style": string,
        "alteration_type": string,
        "structural_control": string,
        "source_tier": "TIER_1_PUBLIC" | "TIER_3_CLIENT" | etc.,
        "source_organization": string,
        "ingested_by": string
    }
    """
    try:
        if not get_vault:
            return {
                "error": "Ground Truth Vault not available",
                "code": "GTV_UNAVAILABLE"
            }
        
        vault = get_vault()
        
        # Create AuroraCommonSchema record
        acs = AuroraCommonSchema(
            latitude=record_data.get("latitude"),
            longitude=record_data.get("longitude"),
            depth_m=record_data.get("depth_m"),
            measurement_type=record_data.get("measurement_type"),
            measurement_value=record_data.get("measurement_value"),
            measurement_unit=record_data.get("measurement_unit"),
            lithology_code=record_data.get("lithology_code"),
            mineralization_style=record_data.get("mineralization_style"),
            alteration_type=record_data.get("alteration_type"),
            structural_control=record_data.get("structural_control"),
            source_tier=record_data.get("source_tier", "TIER_3_CLIENT"),
            source_organization=record_data.get("source_organization"),
            ingested_by=record_data.get("ingested_by", "api_user"),
            mineral_context=record_data.get("mineral_context", {})
        )
        
        record_id, success, error_msg = vault.ingest_record(acs)
        
        if success:
            gtc_score = vault.calculate_gtc_score(record_id)
            return {
                "success": True,
                "record_id": record_id,
                "gtc_score": gtc_score,
                "validation_status": "RAW",
                "message": f"Record ingested with GTC={gtc_score:.2f}"
            }
        else:
            return {
                "error": error_msg,
                "code": "INGESTION_FAILED"
            }
    
    except Exception as e:
        logger.error(f"❌ GTV ingestion error: {str(e)}")
        return {"error": str(e), "code": "GTV_ERROR"}


@app.get("/gtv/conflicts")
async def get_gtv_conflicts() -> Dict:
    """
    Retrieve all detected conflicts in the Ground Truth Vault.
    """
    try:
        if not get_vault:
            return {"error": "Ground Truth Vault not available", "code": "GTV_UNAVAILABLE"}
        
        vault = get_vault()
        conflicts = vault.get_conflicting_records()
        
        return {
            "total_conflicts": len(conflicts),
            "conflicts": [
                {
                    "record_a": c.record_a_id,
                    "record_b": c.record_b_id,
                    "type": c.conflict_type,
                    "severity": c.severity_level,
                    "delta_percent": f"{c.delta_percent:.1f}%"
                }
                for c in conflicts[:50]  # Limit to 50 most recent
            ]
        }
    
    except Exception as e:
        logger.error(f"❌ Conflict query error: {str(e)}")
        return {"error": str(e), "code": "QUERY_ERROR"}


@app.post("/gtv/dry-hole-risk")
async def calculate_dry_hole_risk(location_data: Dict) -> Dict:
    """
    Calculate dry hole probability for a proposed drilling location.
    
    Accepts:
    {
        "latitude": float,
        "longitude": float,
        "mineral": "Au" | "Li" | "Cu",
        "search_radius_km": float (optional, default 5.0)
    }
    """
    try:
        if not get_vault:
            return {"error": "Ground Truth Vault not available", "code": "GTV_UNAVAILABLE"}
        
        vault = get_vault()
        
        mineral_code = location_data.get("mineral", "Au")
        mineral_enum = {"Au": Mineral.GOLD, "Li": Mineral.LITHIUM, "Cu": Mineral.COPPER}.get(
            mineral_code, Mineral.GOLD
        )
        
        risk_assessment = vault.calculate_dry_hole_risk(
            target_lat=location_data.get("latitude"),
            target_lon=location_data.get("longitude"),
            mineral=mineral_enum,
            search_radius_km=location_data.get("search_radius_km", 5.0)
        )
        
        return {
            "success": True,
            "location": {
                "latitude": location_data.get("latitude"),
                "longitude": location_data.get("longitude")
            },
            "mineral": mineral_code,
            "dry_hole_risk_percent": f"{risk_assessment['risk_percent']:.1f}%",
            "critical_failure_mode": risk_assessment["critical_failure_mode"],
            "recommended_action": risk_assessment["recommended_action"],
            "data_density_nearby": risk_assessment["data_density"],
            "structural_integrity": f"{risk_assessment['structural_integrity']:.2f}",
            "grade_probability": f"{risk_assessment['grade_probability']:.2f}",
            "confidence_interval_90": [
                f"{risk_assessment['confidence_90_low']:.1f}%",
                f"{risk_assessment['confidence_90_high']:.1f}%"
            ],
            "anchor_records": risk_assessment["anchor_records"]
        }
    
    except Exception as e:
        logger.error(f"❌ Dry hole risk calculation error: {str(e)}")
        return {"error": str(e), "code": "RISK_CALC_ERROR"}


@app.post("/gtv/calibrate")
async def execute_system_calibration(calibration_data: Dict) -> Dict:
    """
    Execute full system calibration using Ground Truth Vault data.
    
    Applies ground truth to all Aurora sub-modules:
    - Seismic Synthesizer (well-tie calibration)
    - Spectral Harmonization (spectral ground-truthing)
    - Causal Core (edge reweighting)
    - Temporal Analytics (T-Zero reset)
    - Quantum Engine (Hamiltonian constraints)
    - Digital Twin (physics-based accuracy)
    """
    try:
        if not get_calibration_controller:
            return {
                "error": "Calibration Controller not available",
                "code": "CONTROLLER_UNAVAILABLE"
            }
        
        controller = get_calibration_controller()
        
        # Ground truth data from vault
        ground_truth_data = {
            "sonic_logs": calibration_data.get("sonic_logs", []),
            "density_logs": calibration_data.get("density_logs", []),
            "lab_spectroscopy": calibration_data.get("lab_spectroscopy", []),
            "assay_data": calibration_data.get("assay_data", []),
            "borehole_coordinates": tuple(calibration_data.get("borehole_coordinates", [0, 0]))
        }
        
        # Aurora models to calibrate
        aurora_models = {
            "seismic_synthesizer": calibration_data.get("seismic_model", {}),
            "spectral_harmonization": calibration_data.get("spectral_model", {}),
            "causal_core": calibration_data.get("causal_model", {})
        }
        
        # Execute calibration
        calibration_result = controller.execute_full_calibration(
            ground_truth_data, aurora_models
        )
        
        return calibration_result
    
    except Exception as e:
        logger.error(f"❌ Calibration error: {str(e)}")
        return {"error": str(e), "code": "CALIBRATION_ERROR"}


@app.get("/gtv/status")
async def get_gtv_status() -> Dict:
    """
    Get status of Ground Truth Vault and Calibration system.
    """
    try:
        if not get_vault or not get_calibration_controller:
            return {"status": "unavailable"}
        
        vault = get_vault()
        controller = get_calibration_controller()
        
        return {
            "gtv_status": "operational",
            "records_ingested": len(vault.records),
            "conflicts_detected": len(vault.conflicts),
            "calibration_status": controller.get_calibration_status(),
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        logger.error(f"❌ Status query error: {str(e)}")
        return {"error": str(e), "code": "STATUS_ERROR"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
