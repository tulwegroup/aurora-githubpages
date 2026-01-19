"""
Aurora Ground Truth Vault (A-GTV) v2.0
Regulatory-grade subsurface data management with provenance tracking and conflict resolution

This module implements:
1. Aurora Common Schema (ACS) ingestion
2. Multi-tier source integration
3. Conflict resolution engine with authority-based weighting
4. Ground Truth Confidence (GTC 2.0) scoring
5. Mineral-specific contextual logic
"""

import json
import hashlib
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from enum import Enum
import logging
import math

logger = logging.getLogger(__name__)


# ============================================================================
# ENUMS & DATA STRUCTURES
# ============================================================================

class DataTier(Enum):
    """Hierarchical ranking of data sources for authority-based weighting"""
    TIER_1_PUBLIC = ("TIER_1_PUBLIC", 1.0)          # USGS, Geoscience Australia
    TIER_2_COMMERCIAL = ("TIER_2_COMMERCIAL", 0.9)  # S&P Global, Wood Mackenzie
    TIER_3_CLIENT = ("TIER_3_CLIENT", 0.8)          # Proprietary client data
    TIER_4_REALTIME = ("TIER_4_REALTIME", 0.7)      # While-drilling sensors
    TIER_5_SECURITY = ("TIER_5_SECURITY", 0.6)      # Access-controlled secure data

    def __init__(self, tier_name: str, authority_weight: float):
        self.tier_name = tier_name
        self.authority_weight = authority_weight


class ValidationStatus(Enum):
    """QC pipeline stages"""
    RAW = "RAW"                    # Ingested, not validated
    QC_PASSED = "QC_PASSED"        # Passed automated QC checks
    PEER_REVIEWED = "PEER_REVIEWED" # Approved by domain expert


class MeasurementType(Enum):
    """Supported measurement types from ground truth sources"""
    SEISMIC_VELOCITY = "seismic_velocity"
    DENSITY = "density"
    ASSAY_PPM = "assay_ppm"
    LITHOLOGY = "lithology"
    POROSITY = "porosity"
    PERMEABILITY = "permeability"
    SONIC_DT = "sonic_dt"
    GRAVITY = "gravity"
    MAGNETIC = "magnetic"
    SPECTRAL_REFLECTANCE = "spectral_reflectance"
    TEMPERATURE = "temperature"
    PRESSURE = "pressure"
    BREAKOUT = "breakout"
    CORE_DESCRIPTION = "core_description"


class Mineral(Enum):
    """Target mineral types with mineral-specific context"""
    GOLD = ("Au", {
        "primary_indicator": "structural_vector",
        "secondary_indicators": ["quartz_vein_frequency", "grade_shell", "alteration_intensity"],
        "typical_hosts": ["granite", "granodiorite", "diorite"],
        "min_gtc_for_drilling": 0.75
    })
    LITHIUM = ("Li", {
        "primary_indicator": "brine_chemistry",
        "secondary_indicators": ["aquifer_thickness", "porosity", "salinity"],
        "typical_hosts": ["evaporite", "salt_lake_sediments"],
        "min_gtc_for_drilling": 0.80
    })
    COPPER = ("Cu", {
        "primary_indicator": "sulfide_association",
        "secondary_indicators": ["structural_position", "hydrothermal_alteration"],
        "typical_hosts": ["granodiorite", "diorite", "monzonite"],
        "min_gtc_for_drilling": 0.73
    })

    def __init__(self, code: str, context: Dict[str, Any]):
        self.code = code
        self.context = context


class ConflictStatus(Enum):
    """Conflict resolution states"""
    CLEAN = "clean"                      # No conflicts detected
    FLAGGED_VS_TIER_1 = "flagged_vs_tier_1"        # Conflicts with public data
    FLAGGED_VS_TIER_2 = "flagged_vs_tier_2"        # Conflicts with commercial data
    FLAGGED_VS_NEIGHBOR = "flagged_vs_neighbor"    # Nearby data contradicts


@dataclass
class AuroraCommonSchema:
    """Aurora Common Schema (ACS) - Standardized record format"""
    
    # Location
    latitude: float
    longitude: float
    depth_m: Optional[float] = None
    depth_bottom_m: Optional[float] = None
    crs: str = "EPSG:4326"
    spatial_uncertainty_m: float = 50.0
    
    # Measurement
    measurement_type: str = None
    measurement_value: Optional[float] = None
    measurement_unit: Optional[str] = None
    detection_limit: Optional[float] = None
    is_non_detect: bool = False
    
    # Lithology & Geologic Context
    lithology_code: Optional[str] = None
    mineralization_style: Optional[str] = None
    alteration_type: Optional[str] = None
    structural_control: Optional[str] = None
    
    # Metadata
    validation_status: str = ValidationStatus.RAW.value
    confidence_basis: Optional[str] = None
    
    # Provenance
    original_file: Optional[str] = None
    ingested_by: str = "system"
    source_tier: str = DataTier.TIER_3_CLIENT.tier_name
    source_organization: Optional[str] = None
    
    # Mineral-specific context
    mineral_context: Dict[str, Any] = None
    
    # Audit
    chain_of_custody: List[str] = None

    def to_dict(self) -> Dict:
        """Convert to dictionary for storage"""
        return {
            k: v for k, v in asdict(self).items()
            if v is not None
        }


@dataclass
class GTCScoreInput:
    """Inputs for Ground Truth Confidence (GTC 2.0) calculation"""
    base_confidence: float          # 0.0-1.0
    data_freshness_factor: float    # Based on age
    consensus_factor: float         # Based on agreement with other data
    authority_weight: float         # Based on source tier
    validation_status: ValidationStatus


@dataclass
class ConflictRecord:
    """Details of a detected conflict between records"""
    record_a_id: str
    record_b_id: str
    conflict_type: str              # e.g., "depth_mismatch", "grade_contradiction"
    severity_level: str             # "low", "medium", "high", "critical"
    delta_percent: float            # Percentage difference
    record_a_value: Any
    record_b_value: Any
    record_a_tier: DataTier
    record_b_tier: DataTier


# ============================================================================
# GROUND TRUTH VAULT ENGINE
# ============================================================================

class GroundTruthVault:
    """
    Core Ground Truth Vault engine implementing:
    - Multi-tier ingestion
    - Conflict resolution
    - GTC scoring
    - Risk assessment
    """

    def __init__(self):
        self.records: Dict[str, AuroraCommonSchema] = {}
        self.conflicts: List[ConflictRecord] = []
        self.gtc_cache: Dict[str, float] = {}
        self.logger = logging.getLogger(self.__class__.__name__)

    def ingest_record(self, acs: AuroraCommonSchema) -> Tuple[str, bool, Optional[str]]:
        """
        Ingest a single record into the vault.
        
        Returns:
            (record_id, success, error_message)
        """
        try:
            record_id = str(uuid.uuid4())
            
            # Validate schema
            if not self._validate_acs(acs):
                return record_id, False, "Aurora Common Schema validation failed"
            
            # Compute data hash for provenance
            data_hash = self._compute_data_hash(acs)
            
            # Check for conflicts with existing records
            nearby_conflicts = self._detect_conflicts(acs)
            if nearby_conflicts:
                acs.validation_status = ValidationStatus.RAW.value
                conflict_details = [f"{c.conflict_type} (Δ={c.delta_percent:.1f}%)" 
                                  for c in nearby_conflicts]
                self.logger.warning(f"Record {record_id}: Conflicts detected: {', '.join(conflict_details)}")
                self.conflicts.extend(nearby_conflicts)
            
            # Store record
            self.records[record_id] = acs
            
            # Invalidate GTC cache for nearby records
            self.gtc_cache.clear()
            
            self.logger.info(f"✓ Record {record_id} ingested: {acs.measurement_type} @ ({acs.latitude}, {acs.longitude})")
            return record_id, True, None
            
        except Exception as e:
            self.logger.error(f"✗ Ingestion error: {str(e)}")
            return "", False, str(e)

    def _validate_acs(self, acs: AuroraCommonSchema) -> bool:
        """Validate Aurora Common Schema record"""
        # Location validation
        if not (-90 <= acs.latitude <= 90 and -180 <= acs.longitude <= 180):
            self.logger.error("Invalid coordinates")
            return False
        
        # Measurement type required
        if acs.measurement_type is None:
            self.logger.error("Measurement type required")
            return False
        
        # Value/unit consistency
        if acs.measurement_type not in ['lithology', 'core_description']:
            if acs.measurement_value is None or acs.measurement_unit is None:
                self.logger.error("Numeric measurements require value and unit")
                return False
        
        return True

    def _compute_data_hash(self, acs: AuroraCommonSchema) -> str:
        """Compute SHA256 hash of record for integrity"""
        data_str = json.dumps(acs.to_dict(), sort_keys=True)
        return hashlib.sha256(data_str.encode()).hexdigest()

    def _detect_conflicts(self, new_record: AuroraCommonSchema, 
                         search_radius_km: float = 1.0) -> List[ConflictRecord]:
        """
        Detect conflicts between new record and existing records within radius.
        """
        conflicts = []
        
        # Find nearby records within search radius
        nearby = self._find_nearby_records(
            new_record.latitude,
            new_record.longitude,
            search_radius_km
        )
        
        for existing_id, existing_rec in nearby:
            # Same measurement type comparison
            if existing_rec.measurement_type == new_record.measurement_type:
                
                # Depth-based conflict
                if existing_rec.depth_m and new_record.depth_m:
                    depth_delta = abs(existing_rec.depth_m - new_record.depth_m)
                    if depth_delta > 10:  # >10m difference flagged
                        conflicts.append(ConflictRecord(
                            record_a_id=existing_id,
                            record_b_id="new",
                            conflict_type="depth_mismatch",
                            severity_level="low" if depth_delta < 50 else "medium",
                            delta_percent=(depth_delta / max(existing_rec.depth_m, 1)) * 100,
                            record_a_value=existing_rec.depth_m,
                            record_b_value=new_record.depth_m,
                            record_a_tier=DataTier[existing_rec.source_tier],
                            record_b_tier=DataTier[new_record.source_tier]
                        ))
                
                # Value-based conflict (for numeric measurements)
                if (existing_rec.measurement_value is not None and 
                    new_record.measurement_value is not None):
                    
                    delta = abs(existing_rec.measurement_value - new_record.measurement_value)
                    avg_value = (existing_rec.measurement_value + new_record.measurement_value) / 2
                    delta_percent = (delta / max(avg_value, 1)) * 100
                    
                    if delta_percent > 15:  # >15% difference flagged
                        severity = "critical" if delta_percent > 50 else "high" if delta_percent > 30 else "medium"
                        conflicts.append(ConflictRecord(
                            record_a_id=existing_id,
                            record_b_id="new",
                            conflict_type=f"{existing_rec.measurement_type}_contradiction",
                            severity_level=severity,
                            delta_percent=delta_percent,
                            record_a_value=existing_rec.measurement_value,
                            record_b_value=new_record.measurement_value,
                            record_a_tier=DataTier[existing_rec.source_tier],
                            record_b_tier=DataTier[new_record.source_tier]
                        ))
        
        return conflicts

    def _find_nearby_records(self, lat: float, lon: float, 
                            radius_km: float) -> List[Tuple[str, AuroraCommonSchema]]:
        """Find records within geographic radius"""
        nearby = []
        lat_delta = radius_km / 111.0  # 1 degree latitude ≈ 111 km
        lon_delta = lat_delta / math.cos(math.radians(lat))
        
        for rec_id, rec in self.records.items():
            if (abs(rec.latitude - lat) < lat_delta and 
                abs(rec.longitude - lon) < lon_delta):
                nearby.append((rec_id, rec))
        
        return nearby

    def calculate_gtc_score(self, record_id: str) -> float:
        """
        Calculate Ground Truth Confidence (GTC 2.0) score.
        
        GTC 2.0 = (Base_Confidence) × (Data_Freshness_Factor) × (Consensus_Factor)
        
        Range: 0.0-1.0
        """
        if record_id in self.gtc_cache:
            return self.gtc_cache[record_id]
        
        record = self.records.get(record_id)
        if not record:
            return 0.0
        
        # Step 1: Base Confidence (by measurement type)
        base_confidence = {
            MeasurementType.ASSAY_PPM.value: 1.0,
            MeasurementType.SONIC_DT.value: 0.95,
            MeasurementType.DENSITY.value: 0.9,
            MeasurementType.SEISMIC_VELOCITY.value: 0.75,
            MeasurementType.GRAVITY.value: 0.65,
            MeasurementType.SPECTRAL_REFLECTANCE.value: 0.6,
        }.get(record.measurement_type, 0.5)
        
        # Step 2: Data Freshness Factor (age degradation)
        # Assume ingested_by timestamp available in provenance
        freshness_factor = 1.0  # Placeholder
        
        # Step 3: Consensus Factor (weighted by neighboring data)
        consensus_factor = self._calculate_consensus_factor(record)
        
        # Step 4: Authority Weight (by source tier)
        authority_weight = DataTier[record.source_tier].authority_weight
        
        # Step 5: Validation Status multiplier
        validation_multiplier = {
            ValidationStatus.RAW.value: 0.7,
            ValidationStatus.QC_PASSED.value: 0.95,
            ValidationStatus.PEER_REVIEWED.value: 1.0,
        }.get(record.validation_status, 0.7)
        
        # Composite GTC 2.0
        gtc = (base_confidence * freshness_factor * consensus_factor * 
               authority_weight * validation_multiplier)
        
        # Clamp to 0.0-1.0
        gtc = max(0.0, min(1.0, gtc))
        
        self.gtc_cache[record_id] = gtc
        return gtc

    def _calculate_consensus_factor(self, record: AuroraCommonSchema) -> float:
        """
        Calculate consensus factor based on agreement with neighboring data.
        
        IF nearby data MATCHES: Multiplier = 1.1
        IF nearby data CONTRADICTS (but higher authority): Multiplier = 0.9
        IF nearby data CONTRADICTS (but lower authority): Multiplier = 0.5
        """
        nearby_with_values = []
        search_radius = 2.0  # 2 km
        
        for nearby_id, nearby_rec in self._find_nearby_records(
            record.latitude, record.longitude, search_radius
        ):
            if (nearby_rec.measurement_type == record.measurement_type and
                nearby_rec.measurement_value is not None and
                record.measurement_value is not None):
                nearby_with_values.append((nearby_id, nearby_rec))
        
        if not nearby_with_values:
            return 1.0  # No consensus data
        
        # Calculate agreement
        total_consensus = 0.0
        for nearby_id, nearby_rec in nearby_with_values:
            delta_pct = abs(record.measurement_value - nearby_rec.measurement_value) / \
                       max(record.measurement_value, 1) * 100
            
            if delta_pct < 10:  # Good agreement
                consensus_contrib = 1.1
            elif delta_pct < 30:  # Moderate agreement
                consensus_contrib = 1.0
            elif delta_pct < 50:
                # Contradicts but check authority
                nearby_tier = DataTier[nearby_rec.source_tier]
                record_tier = DataTier[record.source_tier]
                if nearby_tier.authority_weight > record_tier.authority_weight:
                    consensus_contrib = 0.9
                else:
                    consensus_contrib = 0.5
            else:  # Strong contradiction
                consensus_contrib = 0.3
            
            total_consensus += consensus_contrib
        
        avg_consensus = total_consensus / len(nearby_with_values)
        return min(1.2, avg_consensus)  # Cap at 1.2 to avoid over-weighting

    def resolve_conflict(self, conflict: ConflictRecord) -> str:
        """
        Resolve conflict using authority-based tiering.
        
        Returns: ID of winning record
        """
        # Higher authority tier wins
        tier_a_weight = conflict.record_a_tier.authority_weight
        tier_b_weight = conflict.record_b_tier.authority_weight
        
        if tier_a_weight > tier_b_weight:
            return conflict.record_a_id
        elif tier_b_weight > tier_a_weight:
            return conflict.record_b_id
        else:
            # Same tier: use higher GTC score
            gtc_a = self.calculate_gtc_score(conflict.record_a_id)
            gtc_b = self.calculate_gtc_score(conflict.record_b_id)
            return conflict.record_a_id if gtc_a >= gtc_b else conflict.record_b_id

    def calculate_dry_hole_risk(self, target_lat: float, target_lon: float,
                                mineral: Mineral = Mineral.GOLD,
                                search_radius_km: float = 5.0) -> Dict[str, Any]:
        """
        Calculate dry hole probability using structural plausibility and grade uncertainty.
        
        Inputs:
            target_lat, target_lon: Proposed drilling location
            mineral: Target mineral type
            search_radius_km: Radius for ground truth search
        
        Returns:
            {
                'risk_percent': 0-100,
                'critical_failure_mode': 'structure' | 'grade' | 'mineral_absence',
                'recommended_action': 'Proceed' | 'Acquire_3D_Seismic' | 'Acquire_More_Data',
                'data_density': count,
                'structural_integrity': 0.0-1.0,
                'grade_probability': 0.0-1.0,
                'confidence_90_low': float,
                'confidence_90_high': float,
                'anchor_records': [record_ids]
            }
        """
        
        # 1. DATA DENSITY CHECK
        nearby_records = self._find_nearby_records(target_lat, target_lon, search_radius_km)
        mineral_relevant = [r for r in nearby_records 
                           if r[1].measurement_type in ['assay_ppm', 'lithology']]
        
        data_density_risk = 0.8 if len(mineral_relevant) < 5 else 0.3 if len(mineral_relevant) < 15 else 0.1
        
        # 2. STRUCTURAL PLAUSIBILITY CHECK
        structural_integrity = self._check_structural_closure(
            target_lat, target_lon, mineral, nearby_records
        )
        
        # 3. GRADE UNCERTAINTY vs. CUTOFF
        grade_stats = self._calculate_grade_statistics(mineral_relevant)
        economic_cutoffs = {
            Mineral.GOLD: 0.5,      # g/t
            Mineral.LITHIUM: 0.1,   # % Li2O
            Mineral.COPPER: 0.3,    # %
        }
        cutoff = economic_cutoffs.get(mineral, 0.5)
        
        if grade_stats['mean'] is not None:
            grade_probability = self._calculate_prob_exceeding_cutoff(
                grade_stats['mean'], grade_stats['std_dev'], cutoff
            )
        else:
            grade_probability = 0.3
        
        # 4. COMPOSITE RISK CALCULATION
        risk_score = (
            (1.0 - structural_integrity) * 0.4 +
            (1.0 - grade_probability) * 0.4 +
            data_density_risk * 0.2
        )
        
        # 5. DETERMINE CRITICAL FAILURE MODE
        if structural_integrity < 0.5:
            failure_mode = "structure"
            action = "Acquire_3D_Seismic"
        elif grade_probability < 0.4:
            failure_mode = "grade"
            action = "Acquire_More_Data"
        else:
            failure_mode = "mineral_absence"
            action = "Proceed" if risk_score < 0.4 else "Acquire_More_Data"
        
        # 6. CONFIDENCE INTERVALS (90% CI)
        ci_low = max(0.0, risk_score - 0.15)
        ci_high = min(1.0, risk_score + 0.15)
        
        return {
            "risk_percent": risk_score * 100,
            "critical_failure_mode": failure_mode,
            "recommended_action": action,
            "data_density": len(mineral_relevant),
            "structural_integrity": structural_integrity,
            "grade_probability": grade_probability,
            "confidence_90_low": ci_low * 100,
            "confidence_90_high": ci_high * 100,
            "anchor_records": [r[0] for r in mineral_relevant[:5]],
            "mineral_context": Mineral.GOLD.context if mineral == Mineral.GOLD else {}
        }

    def _check_structural_closure(self, lat: float, lon: float, 
                                  mineral: Mineral, nearby: List) -> float:
        """
        Validate structural plausibility.
        Returns 0.0-1.0 integrity score.
        """
        # Check for structural control indicators
        structural_records = [r for r in nearby 
                             if r[1].structural_control is not None]
        
        if not structural_records:
            return 0.5  # No structural data
        
        favorable_controls = [r for r in structural_records 
                             if r[1].structural_control in ['fault_zone', 'fold_hinge']]
        
        return len(favorable_controls) / max(len(structural_records), 1)

    def _calculate_grade_statistics(self, records: List) -> Dict[str, Optional[float]]:
        """Calculate mean and std dev of assay grades"""
        values = []
        for rec_id, rec in records:
            if rec.measurement_type == 'assay_ppm' and rec.measurement_value is not None:
                if not rec.is_non_detect:
                    values.append(rec.measurement_value)
        
        if len(values) < 2:
            return {"mean": None, "std_dev": None, "count": len(values)}
        
        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / len(values)
        std_dev = math.sqrt(variance)
        
        return {
            "mean": mean,
            "std_dev": std_dev,
            "count": len(values),
            "min": min(values),
            "max": max(values)
        }

    def _calculate_prob_exceeding_cutoff(self, mean: float, std_dev: float, 
                                        cutoff: float) -> float:
        """
        Calculate probability that grade exceeds economic cutoff.
        Assumes log-normal distribution (typical for commodity grades).
        """
        if std_dev is None or std_dev == 0:
            return 1.0 if mean > cutoff else 0.0
        
        # Z-score
        z = (cutoff - mean) / std_dev
        
        # Approximation of normal CDF (simple Hastings)
        prob = 0.5 * (1 + math.tanh(0.07 * z))
        
        return 1.0 - prob  # P(X > cutoff)

    def get_conflicting_records(self) -> List[ConflictRecord]:
        """Return all detected conflicts"""
        return self.conflicts

    def get_mineral_specific_guidance(self, mineral: Mineral) -> Dict[str, Any]:
        """Return mineral-specific ground truth requirements"""
        return {
            "mineral": mineral.code,
            "context": mineral.context,
            "required_measurements": mineral.context.get("secondary_indicators", []),
            "minimum_gtc_for_drilling": mineral.context.get("min_gtc_for_drilling", 0.75),
            "typical_host_rocks": mineral.context.get("typical_hosts", [])
        }


# ============================================================================
# SINGLETON INSTANCE
# ============================================================================

_gtv_instance = None

def get_vault() -> GroundTruthVault:
    """Get or create the singleton Ground Truth Vault instance"""
    global _gtv_instance
    if _gtv_instance is None:
        _gtv_instance = GroundTruthVault()
        logger.info("✓ Ground Truth Vault initialized")
    return _gtv_instance
