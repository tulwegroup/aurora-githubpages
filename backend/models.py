"""
Aurora OSI v3 - Data Models
Pydantic models for API requests/responses
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Tuple
from datetime import datetime
from enum import Enum


class DetectionTier(str, Enum):
    """Detection confidence tiers"""
    TIER_0 = "TIER_0"  # Low confidence
    TIER_1 = "TIER_1"  # Reconnaissance
    TIER_2 = "TIER_2"  # Exploration target
    TIER_3 = "TIER_3"  # Drill-ready


class MineralDetectionRequest(BaseModel):
    """Request for mineral detection"""
    latitude: float = Field(..., description="Latitude (-90 to 90)")
    longitude: float = Field(..., description="Longitude (-180 to 180)")
    mineral: str = Field(..., description="Mineral to detect")
    sensor: str = Field(default="Sentinel-2", description="Satellite sensor")
    date_start: Optional[str] = None
    date_end: Optional[str] = None


class PixelSpectrum(BaseModel):
    """Spectral data for a single pixel"""
    coordinates: Tuple[float, float] = Field(..., description="(lat, lon)")
    wavelengths_um: List[float] = Field(..., description="Wavelengths in micrometers")
    reflectance: List[float] = Field(..., description="Reflectance values (0-1)")
    timestamp: datetime = Field(default_factory=datetime.now)


class MineralDetectionResult(BaseModel):
    """Result of mineral detection"""
    mineral: str
    confidence_score: float = Field(..., ge=0.0, le=1.0)
    confidence_tier: DetectionTier
    detection_decision: str
    coordinates: Tuple[float, float]
    spectral_match_score: float
    depth_estimate_m: Optional[float] = None
    processing_time_ms: int
    applied_corrections: Dict = {}
    temporal_coherence: Optional[float] = None
    recommendations: List[str] = []


class DigitalTwinQuery(BaseModel):
    """Query the sovereign digital twin"""
    query_type: str = Field(..., description="volume, resource_estimate, drill_site, etc")
    resource_type: Optional[str] = None
    depth_min_m: Optional[int] = None
    depth_max_m: Optional[int] = None
    confidence_min: Optional[float] = 0.6
    region: Optional[str] = None


class VoxelData(BaseModel):
    """Individual voxel in the digital twin"""
    x: int
    y: int
    z: int
    rock_type_probability: Dict[str, float]
    density_kg_m3: float
    density_uncertainty: float
    mineral_assemblage: Dict[str, float]
    timestamp: datetime


class DigitalTwinResponse(BaseModel):
    """Response from digital twin query"""
    query_type: str
    result_count: int
    voxels: List[VoxelData]
    volume_m3: Optional[float] = None
    estimated_resource_tonnes: Optional[float] = None
    confidence_level: float


class SatelliteTaskingRequest(BaseModel):
    """Request autonomous satellite tasking"""
    latitude: float
    longitude: float
    resolution_m: float = Field(..., description="Required resolution in meters")
    sensor_type: str = Field(..., description="SAR, optical, thermal, etc")
    urgency: str = Field(default="standard", description="standard, urgent, critical")
    area_size_km2: float = Field(..., description="Area of interest size")


class SatelliteTask(BaseModel):
    """Satellite task information"""
    task_id: str
    status: str  # pending, scheduled, acquired, processing
    requested_sensor: str
    acquisition_date: Optional[datetime] = None
    data_available: bool = False
    cost_usd: float = 0.0


class PhysicsConstraint(BaseModel):
    """Physics-based constraint for AI model"""
    constraint_type: str
    parameter: str
    min_value: float
    max_value: float
    physics_law: str


class CausalDAG(BaseModel):
    """Directed Acyclic Graph for causal reasoning"""
    nodes: List[Dict]
    edges: List[Tuple[str, str]]
    description: str


class QuantumInversionConfig(BaseModel):
    """Configuration for quantum-assisted inversion"""
    problem_size: int
    num_qubits: int
    quantum_backend: str  # "qaoa", "annealing", "simulator"
    classical_preconditioning: bool = True
    refinement_iterations: int = 5


class GlobalGeodynamicPrior(BaseModel):
    """Global tectono-stratigraphic prior"""
    tectonic_setting: str
    craton_age_ma: Optional[int]
    subduction_zone_distance_km: Optional[int]
    basin_type: Optional[str]
    deposit_likelihood_multiplier: float


class ProbabilisticSeepageNetwork(BaseModel):
    """Network of hydrocarbon migration pathways"""
    source_rock_id: str
    trap_id: str
    fault_id: str
    migration_probability: float
    permeability_md: float
    pressure_gradient_bar_km: float


class SeismicDigitalTwin(BaseModel):
    """2D/3D seismic digital twin representation"""
    survey_id: str
    inline_count: int
    crossline_count: int
    depth_samples: int
    depth_range_m: Tuple[int, int]
    voxel_size_m: int
    time_created: datetime
    last_updated: datetime


class DigitalTwinVoxel(BaseModel):
    """Single voxel in 3D seismic digital twin"""
    inline: int
    crossline: int
    depth_m: int
    amplitude: float
    impedance: float
    porosity_fraction: float
    saturation_fraction: float
    fluid_type: Optional[str] = None


class PhysicsResidual(BaseModel):
    """Physics residual information"""
    location: Tuple[float, float, int]  # lat, lon, depth
    residual_value: float
    physics_law_violated: str
    severity: str  # low, medium, high
    explanation: str


class ResourceEstimate(BaseModel):
    """Resource estimate for a deposit"""
    commodity: str
    resource_class: str  # inferred, indicated, measured
    tonnes: float
    grade: float
    confidence_p90: float
    confidence_p50: float
    confidence_p10: float
    geological_probability: float
