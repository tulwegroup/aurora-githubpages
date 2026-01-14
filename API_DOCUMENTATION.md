# Aurora OSI v3 - Complete API Documentation

## Base URL

**Development:** `http://localhost:8000`  
**Production:** `https://api.aurora-osi.com`

## Authentication

Currently uses API key in headers (implement OAuth2 for production):

```
X-API-Key: your-api-key
```

## Health & Status

### GET /health
Check system operational status

**Response:**
```json
{
  "status": "operational",
  "timestamp": "2026-01-14T10:30:00Z",
  "components": {
    "spectral_library": "operational",
    "database": "operational",
    "quantum_interface": "operational"
  }
}
```

## Mineral Detection

### POST /detect/mineral
Detect mineral at specified coordinates using multi-physics satellite fusion

**Request:**
```json
{
  "latitude": -20.5,
  "longitude": 134.5,
  "mineral": "arsenopyrite",
  "sensor": "Sentinel-2",
  "date_start": "2025-01-01",
  "date_end": "2026-01-14"
}
```

**Response:**
```json
{
  "mineral": "arsenopyrite",
  "confidence_score": 0.78,
  "confidence_tier": "TIER_2",
  "detection_decision": "ACCEPT_MODERATE_CONFIDENCE",
  "coordinates": [-20.5, 134.5],
  "spectral_match_score": 0.741,
  "depth_estimate_m": 200.0,
  "processing_time_ms": 1250,
  "applied_corrections": {
    "atmospheric": true,
    "seasonal": true,
    "depth": true
  },
  "temporal_coherence": 0.85,
  "recommendations": [
    "Conduct ground validation",
    "Request adaptive satellite tasking"
  ]
}
```

**Parameters:**
- `latitude` (float, -90 to 90): Target latitude
- `longitude` (float, -180 to 180): Target longitude
- `mineral` (string): Mineral name (see GET /detect/minerals)
- `sensor` (string): Sentinel-2, Landsat8, ASTER, WorldView3
- `date_start` (optional): ISO date string
- `date_end` (optional): ISO date string

**Confidence Tiers:**
- `TIER_0`: < 0.55 confidence - Reject
- `TIER_1`: 0.55-0.70 - Reconnaissance target
- `TIER_2`: 0.70-0.85 - Exploration target
- `TIER_3`: > 0.85 - Drill-ready prospect

---

### GET /detect/minerals
List all detectable minerals in spectral library

**Response:**
```json
{
  "total_minerals": 18,
  "by_commodity": {
    "Gold": ["arsenopyrite", "quartz", "pyrite", "muscovite", "alunite"],
    "Copper": ["chalcopyrite", "malachite", "bornite", "chalcocite", "covellite", "azurite"],
    "Zinc": ["sphalerite", "smithsonite"],
    "Nickel": ["pentlandite", "garnierite"],
    "Lithium": ["spodumene", "lepidolite"],
    "Iron": ["hematite", "magnetite", "goethite"]
  }
}
```

---

### GET /detect/commodity/{commodity}
Get all minerals for specific commodity

**Parameters:**
- `commodity` (string): Gold, Copper, Lithium, Zinc, Nickel, Tungsten, Iron, REE

**Response:**
```json
{
  "commodity": "Gold",
  "mineral_count": 5,
  "minerals": [
    {
      "name": "arsenopyrite",
      "formula": "FeAsS",
      "peaks_um": [0.548, 0.652, 0.895, 1.450, 2.050, 2.850],
      "usgs_id": "NMNH_145212"
    },
    {
      "name": "quartz",
      "formula": "SiO₂",
      "peaks_um": [8.600, 9.100, 12.500],
      "usgs_id": "NMNH_111312"
    }
  ]
}
```

## Digital Twin Queries

### POST /twin/query
Query the sovereign 4D subsurface digital twin

**Request:**
```json
{
  "query_type": "resource_estimate",
  "resource_type": "copper",
  "depth_min_m": 0,
  "depth_max_m": 2000,
  "confidence_min": 0.7,
  "region": "Australia"
}
```

**Query Types:**
- `volume`: Calculate volumetric resource
- `resource_estimate`: Estimate tonnage
- `drill_sites`: Find optimal drill locations
- `material_properties`: Get rock/fluid properties

**Response:**
```json
{
  "query_type": "resource_estimate",
  "result_count": 1,
  "voxels": [
    {
      "x": 0,
      "y": 0,
      "z": 0,
      "rock_type_probability": {"sandstone": 0.6, "shale": 0.3, "limestone": 0.1},
      "density_kg_m3": 2600.0,
      "density_uncertainty": 100.0,
      "mineral_assemblage": {"quartz": 0.5, "feldspar": 0.3},
      "timestamp": "2026-01-14T10:30:00Z"
    }
  ],
  "volume_m3": 1000000.0,
  "estimated_resource_tonnes": 1000000.0,
  "confidence_level": 0.75
}
```

---

### GET /twin/{region}/status
Get digital twin status for geographic region

**Parameters:**
- `region` (string): Region name (e.g., "Australia", "Africa", "Peru")

**Response:**
```json
{
  "region": "Australia",
  "status": "operational",
  "last_update": "2026-01-14T08:00:00Z",
  "coverage_percent": 95.5,
  "voxel_resolution_m": 100,
  "voxel_count": 15000000,
  "depth_range_m": [0, 5000]
}
```

## Satellite Tasking

### POST /satellite/task
Request autonomous satellite acquisition

**Request:**
```json
{
  "latitude": -20.5,
  "longitude": 134.5,
  "resolution_m": 3.0,
  "sensor_type": "SAR",
  "urgency": "standard",
  "area_size_km2": 100.0
}
```

**Sensor Types:**
- `SAR`: Synthetic Aperture Radar (Capella, ICEYE)
- `optical`: High-resolution optical (Planet, Maxar)
- `thermal`: Thermal infrared (night-pass)
- `lidar`: LiDAR (topography, structure)

**Urgency Levels:**
- `standard`: Normal priority (7-14 days)
- `urgent`: High priority (2-7 days)
- `critical`: Immediate (within 24 hours, higher cost)

**Response:**
```json
{
  "task_id": "SAT_20260114_103000",
  "status": "pending",
  "sensor": "SAR",
  "resolution_m": 3.0,
  "estimated_cost_usd": 15000.0,
  "area_km2": 100.0,
  "urgency": "standard",
  "estimated_acquisition": "2026-01-20"
}
```

---

### GET /satellite/task/{task_id}
Get satellite tasking request status

**Response:**
```json
{
  "task_id": "SAT_20260114_103000",
  "status": "scheduled",
  "sensor": "SAR",
  "created_at": "2026-01-14T10:30:00Z",
  "scheduled_date": "2026-01-20",
  "data_available": false,
  "estimated_cost_usd": 15000.0,
  "progress_percent": 25
}
```

**Status Values:**
- `pending`: Awaiting scheduling
- `scheduled`: Scheduled for acquisition
- `acquired`: Data collected
- `processing`: Being processed
- `ready`: Ready for download
- `failed`: Acquisition failed

## Seismic Digital Twin

### POST /seismic/survey
Create new 2D/3D seismic digital twin survey

**Request:**
```json
{
  "survey_id": "SEIS_2025_001",
  "inline_count": 500,
  "crossline_count": 750,
  "depth_samples": 4000,
  "depth_min_m": 0,
  "depth_max_m": 5000,
  "voxel_size_m": 12.5
}
```

**Response:**
```json
{
  "survey_id": "SEIS_2025_001",
  "status": "created",
  "voxel_count": 1500000000,
  "created_at": "2026-01-14T10:30:00Z"
}
```

---

### GET /seismic/{survey_id}/amplitude/{inline}/{crossline}/{depth}
Get seismic voxel data at specific location

**Parameters:**
- `survey_id`: Survey identifier
- `inline`: Inline number
- `crossline`: Crossline number
- `depth`: Depth in meters

**Response:**
```json
{
  "survey_id": "SEIS_2025_001",
  "inline": 250,
  "crossline": 375,
  "depth_m": 2500,
  "amplitude": 0.5,
  "impedance": 12500.0,
  "porosity": 0.25,
  "saturation": 0.7,
  "fluid_type": "oil"
}
```

## Physics & Constraints

### GET /physics/residuals
Get physics residual violations

**Query Parameters:**
- `region` (optional): Geographic region
- `severity` (optional): high, medium, low

**Response:**
```json
{
  "residual_count": 45,
  "severity_high": 12,
  "residuals": [
    {
      "lat": -20.5,
      "lon": 134.5,
      "depth": 1500,
      "residual": 2.5,
      "law": "Poisson_equation",
      "severity": "high"
    }
  ]
}
```

---

### POST /physics/enforce
Apply physical constraints to model predictions

**Request:**
```json
{
  "constraint_type": "density_gradient",
  "parameter": "density",
  "min_value": 2000,
  "max_value": 3500,
  "physics_law": "lithostatic_gradient"
}
```

**Response:**
```json
{
  "constraint_applied": true,
  "violations_corrected": 234,
  "model_adjusted": true,
  "residual_reduction": 0.35
}
```

## Quantum Acceleration

### POST /quantum/invert
Submit gravimetric inversion for quantum acceleration

**Request:**
```json
{
  "problem_size": 1000,
  "num_qubits": 250,
  "quantum_backend": "qaoa",
  "classical_preconditioning": true,
  "refinement_iterations": 5
}
```

**Quantum Backends:**
- `qaoa`: Quantum Approximate Optimization Algorithm
- `annealing`: D-Wave quantum annealing
- `simulator`: Classical tensor network simulator

**Response:**
```json
{
  "inversion_id": "QI_20260114_103000",
  "status": "processing",
  "quantum_backend": "qaoa",
  "problem_size": 1000,
  "qubits_required": 250,
  "classical_refinement_iterations": 5,
  "expected_speedup": "2-5x",
  "estimated_time_seconds": 600
}
```

## Error Handling

### Error Response Format

```json
{
  "detail": "Mineral 'invalid' not found in spectral library",
  "status": 404,
  "timestamp": "2026-01-14T10:30:00Z"
}
```

### Common HTTP Status Codes

- `200`: Success
- `201`: Created
- `400`: Bad request (invalid parameters)
- `401`: Unauthorized (missing API key)
- `403`: Forbidden (insufficient permissions)
- `404`: Not found (resource doesn't exist)
- `409`: Conflict (duplicate resource)
- `500`: Internal server error
- `503`: Service unavailable

## Rate Limiting

**Limits per API key:**
- Detection requests: 100/minute
- Digital twin queries: 50/minute
- Satellite tasks: 10/hour
- Quantum inversions: 5/day

**Headers:**
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1642159200
```

## Pagination

List endpoints support pagination:

```
?page=1&page_size=50
```

**Response:**
```json
{
  "data": [...],
  "pagination": {
    "page": 1,
    "page_size": 50,
    "total_count": 1500,
    "total_pages": 30
  }
}
```

## Webhooks

Subscribe to events (coming soon):

```
POST /webhooks/subscribe
{
  "event": "detection.completed",
  "url": "https://yourapp.com/webhook",
  "secret": "webhook-secret"
}
```

## SDK/Client Libraries

**Python:**
```python
from aurora_osi import Client

client = Client(api_key="your-key")
result = client.detect_mineral(
    latitude=-20.5,
    longitude=134.5,
    mineral="arsenopyrite"
)
```

**JavaScript/TypeScript:**
```typescript
import { AuroraOSI } from 'aurora-osi-js'

const client = new AuroraOSI({ apiKey: 'your-key' })
const result = await client.detectMineral({
  latitude: -20.5,
  longitude: 134.5,
  mineral: 'arsenopyrite'
})
```

## Testing & Examples

### Interactive API Docs
- Swagger UI: `/docs`
- ReDoc: `/redoc`

### Example Requests

**Detect gold in Australia:**
```bash
curl -X POST http://localhost:8000/detect/mineral \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-key" \
  -d '{
    "latitude": -20.5,
    "longitude": 134.5,
    "mineral": "arsenopyrite",
    "sensor": "Sentinel-2"
  }'
```

**Query digital twin:**
```bash
curl -X POST http://localhost:8000/twin/query \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-key" \
  -d '{
    "query_type": "resource_estimate",
    "resource_type": "copper",
    "region": "Australia"
  }'
```

---

**API Version:** 3.1.0  
**Last Updated:** January 14, 2026  
**Status:** Production Ready
