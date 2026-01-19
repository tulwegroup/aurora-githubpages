# Aurora Ground Truth Vault (A-GTV) v2.0
## Technical Implementation Guide

**Project:** Project Aurora - Physics-Informed Satellite Inversion for Subsurface Intelligence  
**Version:** 2.0  
**Date:** 2026-01-19  
**Purpose:** Regulatory-grade subsurface data management with provenance tracking and AI calibration

---

## EXECUTIVE SUMMARY

Project Aurora has evolved from a **Top-Down system** (Satellite → Surface Prediction) to a **Hybrid Joint Inversion** system (Satellite + Ground Truth → High-Fidelity Reality).

The **Ground Truth Vault (A-GTV)** acts as the **Calibration Layer**, ensuring that all AI/Physics models remain anchored to physical reality. This document specifies:

1. **Aurora Common Schema (ACS)** - Standardized data ingestion format
2. **Multi-Tier Conflict Resolution Engine** - Authority-based weighting for competing data sources
3. **Ground Truth Confidence (GTC 2.0)** - Quantitative scoring system
4. **Dry Hole Risk Calculator** - Regulatory-ready risk assessment
5. **System Calibration Protocol** - Forcing all Aurora modules to respect ground truth

---

## SECTION 1: AURORA COMMON SCHEMA (ACS) DESIGN

### 1.1 Purpose
ACS provides a **universal ingestion format** for heterogeneous subsurface data:
- Seismic velocity logs (sonic, checkshot)
- Assay data (chemical analysis)
- Wireline logs (gamma ray, density, porosity)
- Lithology descriptions
- Geochemical surveys (surface geochem)
- Spectroscopy (lab-measured core samples)
- Structural measurements

### 1.2 Core Schema Structure

```yaml
aurora_record:
  # ---- LOCATION & COORDINATES ----
  location:
    latitude: float (-90 to +90)
    longitude: float (-180 to +180)
    depth_m: float (top of measurement interval)
    depth_bottom_m: float (bottom of measurement interval, for logs)
    crs: "EPSG:4326" (default; supports other CRS via string)
    spatial_uncertainty_m: float (default 50m)

  # ---- MEASUREMENT ----
  measurement:
    type: enum (seismic_velocity | density | assay_ppm | lithology | porosity | 
                permeability | sonic_dt | gravity | magnetic | spectral_reflectance | 
                temperature | pressure | breakout | core_description)
    value: float | null (NULL for categorical measurements like lithology)
    unit: string (m/s, kg/m3, ppm, %, etc.)
    detection_limit: float (critical for assay non-detects)
    is_non_detect: boolean (TRUE if value < detection_limit)

  # ---- GEOLOGIC CONTEXT (Semantic Understanding) ----
  geologic_context:
    lithology_code: string (e.g., "granodiorite", "shale")
    mineralization_style: enum (porphyry | vein | placer | MVT | sediment_hosted | skarn | epithermal | none)
    alteration_type: enum (argillic | phyllic | potassic | silicic | carbonate | propylitic | none)
    structural_control: enum (fault_zone | fold_hinge | stratabound | none)

  # ---- VALIDATION STATUS ----
  validation:
    status: enum (RAW | QC_PASSED | PEER_REVIEWED)
    gtc_score: float (0.0-1.0, calculated via GTC 2.0)
    confidence_basis: string (e.g., "Laboratory_Assay", "Wireline_Log")

  # ---- CONFLICT TRACKING ----
  conflict:
    status: enum (clean | flagged_vs_tier_1 | flagged_vs_tier_2 | flagged_vs_neighbor)
    notes: string (Description of detected conflict)
    resolved_by: string (Admin user who reviewed)
    resolved_at: timestamp

  # ---- MINERAL-SPECIFIC CONTEXT (JSON for flexibility) ----
  mineral_context:
    target_mineral: "Au" | "Li" | "Cu" | etc.
    grade_shell: "high" | "medium" | "low"
    specific_metrics: {...} # Mineral-specific data

  # ---- PROVENANCE (Chain of Custody) ----
  provenance:
    original_file: string (e.g., "Scan_Core_Box_4_1990.pdf")
    ingestion_timestamp: ISO8601 timestamp
    ingested_by: string (System user ID)
    chain_of_custody: [string] (e.g., ["Client_Upload", "Quality_Check", "Vault"])
    data_hash: "SHA256:..." (Immutable integrity check)
    source_tier: "TIER_1_PUBLIC" | "TIER_2_COMMERCIAL" | "TIER_3_CLIENT" | "TIER_4_REALTIME" | "TIER_5_SECURITY"
    source_organization: string
    source_license: string
```

### 1.3 Handling Non-Detects

**CRITICAL for Statistical Validity:**

In assay data, concentrations below the analytical detection limit (e.g., <0.05 ppm Au) are often reported as "non-detects." Treating non-detects as zeros biases statistical inference.

**Protocol:**
```yaml
assay_record:
  measurement_value: null  # Don't record a placeholder value
  detection_limit: 0.05 # Record the actual DL
  is_non_detect: true # Flag as non-detect
  measurement_unit: "ppm"
  # Statistical analysis MUST account for left-censoring
```

---

## SECTION 2: INGESTION & CONFLICT RESOLUTION ENGINE

### 2.1 Multi-Tier Data Sources

```
┌─────────────────────────────────────────────────────────┐
│  AURORA DATA TIER HIERARCHY (Authority Ranking)         │
├─────────────────────────────────────────────────────────┤
│ TIER 1: PUBLIC AUTHORITATIVE (Weight = 1.0)             │
│   └─ USGS EarthExplorer, Geoscience Australia, GEUS     │
│   └─ Authority: Government; Validation: Peer-reviewed    │
│                                                          │
│ TIER 2: COMMERCIAL LICENSED (Weight = 0.9)             │
│   └─ S&P Global, Wood Mackenzie, IHS Markit            │
│   └─ Authority: Industry; Validation: QC'd by vendor    │
│                                                          │
│ TIER 3: CLIENT PROPRIETARY (Weight = 0.8)              │
│   └─ Seismic, boreholes, assays from project client    │
│   └─ Authority: Direct knowledge; Validation: TBD      │
│                                                          │
│ TIER 4: REAL-TIME OPERATIONAL (Weight = 0.7)           │
│   └─ While-drilling sensors, live assay feeds         │
│   └─ Authority: Fresh; Validation: Provisional         │
│                                                          │
│ TIER 5: SECURITY/ACCESS-CONTROLLED (Weight = 0.6)      │
│   └─ Restricted-access proprietary data                │
│   └─ Authority: Selective; Validation: Admin reviewed  │
└─────────────────────────────────────────────────────────┘
```

### 2.2 Conflict Detection Logic

When a new record is ingested, the system:

1. **Queries nearby records** within a configurable radius (default 1 km)
2. **Identifies conflicts** by comparing:
   - **Depth mismatch:** If depth differs by >10m → Flag as "low" conflict
   - **Value contradiction:** If assay grades differ by >15% → Flag as "medium/high/critical"
3. **Calculates severity:**
   ```
   Severity = "low" if delta < 10%
            = "medium" if 10% ≤ delta < 30%
            = "high" if 30% ≤ delta < 50%
            = "critical" if delta ≥ 50%
   ```

### 2.3 Conflict Resolution Strategy

**Authority-Based Tiering (The "Tiered Truth" Logic):**

```python
def resolve_conflict(record_a, record_b):
    """
    Determine which record "wins" in a conflict.
    """
    # Step 1: Compare source tiers
    tier_a_weight = get_tier_weight(record_a.source_tier)
    tier_b_weight = get_tier_weight(record_b.source_tier)
    
    if tier_a_weight > tier_b_weight:
        return record_a  # TIER 1 data wins over TIER 3
    elif tier_b_weight > tier_a_weight:
        return record_b
    
    # Step 2: If same tier, compare GTC scores
    else:
        gtc_a = calculate_gtc(record_a)
        gtc_b = calculate_gtc(record_b)
        return record_a if gtc_a >= gtc_b else record_b
```

**Example Conflict:**
- **Client assay:** Au grade = 2.8 g/t at depth 155m (TIER_3_CLIENT)
- **USGS survey:** Au grade = 1.2 g/t at depth 150m (TIER_1_PUBLIC)
- **Delta:** 57% difference → "critical" severity
- **Resolution:** USGS data (TIER 1) wins; Client data flagged for review

---

## SECTION 3: GROUND TRUTH CONFIDENCE (GTC 2.0) SCORING

### 3.1 GTC 2.0 Formula

```
GTC 2.0 = (Base_Confidence) 
        × (Data_Freshness_Factor) 
        × (Consensus_Factor) 
        × (Authority_Weight) 
        × (Validation_Multiplier)

Range: 0.0 (completely unreliable) to 1.0 (perfectly reliable)
```

### 3.2 Component Calculations

#### A. Base Confidence (by Measurement Type)
```
Assay (lab-analyzed core): 1.0
Sonic Log (wireline):      0.95
Density Log (wireline):    0.90
Seismic Velocity:          0.75
Gravity Survey:            0.65
Spectral Reflectance:      0.60
Surface Geochem:           0.50
```

#### B. Data Freshness Factor
```
Age < 1 year:   1.0
Age 1-5 years:  0.9
Age 5-10 years: 0.75
Age > 10 years: 0.5
```

#### C. Consensus Factor (Agreement with Nearby Data)
```
IF nearby_records AGREE (within ±10%):
    Multiplier = 1.1 (confidence boost from consensus)

ELSE IF nearby_records PARTIALLY_AGREE (10-30% delta):
    Multiplier = 1.0 (no boost, no penalty)

ELSE IF nearby_records CONTRADICT (30-50% delta):
    IF nearby_tier > current_tier:
        Multiplier = 0.9 (slight downgrade; higher authority contradicts)
    ELSE:
        Multiplier = 0.5 (significant downgrade; lower authority contradicts)

ELSE IF nearby_records STRONGLY_CONTRADICT (>50% delta):
    Multiplier = 0.3 (severe downgrade; major disagreement)
```

#### D. Authority Weight (by Source Tier)
```
TIER_1_PUBLIC:        1.0
TIER_2_COMMERCIAL:    0.9
TIER_3_CLIENT:        0.8
TIER_4_REALTIME:      0.7
TIER_5_SECURITY:      0.6
```

#### E. Validation Status Multiplier
```
RAW:             0.7 (Not yet validated)
QC_PASSED:       0.95 (Passed automated checks)
PEER_REVIEWED:   1.0 (Expert approval)
```

### 3.3 Example GTC 2.0 Calculation

**Scenario:**
- Record: Assay of 2.5 g/t Au from drill core
- Tier: TIER_3_CLIENT (authority_weight = 0.8)
- Status: QC_PASSED (validation_mult = 0.95)
- Age: 2 years (freshness_factor = 0.9)
- Nearby records: 3 assays of 2.3, 2.6, 2.4 g/t (agreement within ±8%)
  - consensus_factor = 1.1 (strong agreement)

**Calculation:**
```
GTC 2.0 = 1.0 × 0.9 × 1.1 × 0.8 × 0.95
        = 0.7524
        ≈ 0.75 (75% confidence)
```

**Interpretation:** This record has **"good but not excellent" confidence**. It should inform medium-confidence decisions (exploration targeting) but not alone justify a multi-million-dollar drilling campaign.

---

## SECTION 4: MINERAL-SPECIFIC CONTEXT

Different minerals have fundamentally different "ground truths."

### 4.1 Mineral Domain Models

#### GOLD (Au)
```yaml
Primary Indicator: Structural Vector
  - Measured fault/vein geometry
  - Fault dip, strike, displacement
Secondary Indicators:
  - Quartz vein frequency (veins/meter)
  - Alteration intensity (phyllic, argillic)
  - Depth range: 100-1500m (typical)
Typical Host Rocks: Granite, granodiorite, diorite
Min GTC for Drilling: 0.75 (75% confidence required)
```

#### LITHIUM (Li)
```yaml
Primary Indicator: Brine Chemistry
  - Li concentration (mg/L in pore fluid)
  - Salinity (TDS)
  - pH, potassium ratio
Secondary Indicators:
  - Aquifer thickness (m)
  - Porosity & permeability
  - Depth range: 10-500m (near surface)
Typical Host Rocks: Evaporite, salt lake sediments
Min GTC for Drilling: 0.80 (80% confidence required - higher threshold due to economic sensitivity)
```

#### COPPER (Cu)
```yaml
Primary Indicator: Sulfide Association
  - Chalcopyrite, bornite presence
  - Sulfide grain size
Secondary Indicators:
  - Structural position (fault intersections)
  - Hydrothermal alteration (potassic, phyllic)
  - Depth range: 200-2000m
Typical Host Rocks: Granodiorite, diorite, monzonite
Min GTC for Drilling: 0.73 (73% confidence required)
```

### 4.2 Mineral-Specific Risk Adjustment

```python
def calculate_dry_hole_risk_mineral_specific(
    proposed_location,
    mineral_type,
    ground_truth_vault
):
    """
    Risk calculation adapted for mineral-specific requirements.
    """
    
    # Step 1: Extract mineral-specific indicator data
    if mineral_type == "Au":
        primary_indicators = vault.query(
            mineral="Au",
            measurement_type="quartz_vein_frequency",
            location=proposed_location,
            radius=5km
        )
    elif mineral_type == "Li":
        primary_indicators = vault.query(
            mineral="Li",
            measurement_type="brine_chemistry",
            location=proposed_location,
            radius=5km
        )
    
    # Step 2: Check min GTC threshold
    min_gtc = MINERAL_THRESHOLDS[mineral_type]
    avg_gtc = mean([rec.gtc_score for rec in primary_indicators])
    
    if avg_gtc < min_gtc:
        return {
            "risk": "VERY_HIGH",
            "reason": f"Average GTC ({avg_gtc:.2f}) below mineral threshold ({min_gtc:.2f})"
        }
    
    # Step 3: Proceed with standard risk calculation
    return standard_dry_hole_risk(proposed_location, ground_truth_vault)
```

---

## SECTION 5: DRY HOLE RISK CALCULATOR

### 5.1 Algorithm Overview

```python
def calculate_dry_hole_probability(target_location, vault, mineral='Au'):
    """
    Calculate dry hole probability using structural plausibility 
    and grade uncertainty.
    
    Returns: {
        'risk_percent': 0-100,
        'critical_failure_mode': 'structure' | 'grade' | 'mineral_absence',
        'recommended_action': 'Proceed' | 'Acquire_3D_Seismic' | 'Acquire_More_Data'
    }
    """
```

### 5.2 Risk Components

#### Component 1: Data Density Check
```
IF nearby_records < 5:
    data_density_risk = 0.8 (high risk)
ELIF nearby_records < 15:
    data_density_risk = 0.3 (moderate risk)
ELSE:
    data_density_risk = 0.1 (low risk)
```

#### Component 2: Structural Plausibility
```
Check for structural closures, fault traps, fold hinges.

structural_integrity = (# favorable structures) / (# total structures)

IF structural_integrity < 0.5:
    Critical Failure Mode = "STRUCTURE"
    Recommendation = "ACQUIRE_3D_SEISMIC"
```

#### Component 3: Grade Uncertainty vs. Cutoff
```
1. Extract all assay grades from nearby records
2. Calculate: mean(grade), stdev(grade)
3. Define economic cutoff (e.g., 0.5 g/t Au)
4. Calculate P(grade > cutoff) using log-normal distribution
5. IF P(grade > cutoff) < 0.4:
     Critical Failure Mode = "GRADE"
     Recommendation = "ACQUIRE_MORE_DATA"
```

#### Component 4: Composite Risk
```
risk_score = (1.0 - structural_integrity) × 0.4 
           + (1.0 - grade_probability) × 0.4 
           + data_density_risk × 0.2

risk_percent = risk_score × 100
```

### 5.3 Example Calculation

**Proposed Location:** 35.2°N, 107.8°W (Porphyry Au target)

**Nearby Ground Truth (5 km radius):**
- 8 assay records (GTC avg = 0.82)
- 6 structural measurements (faults, veins)
- 3 seismic velocities (suggest competent host rock)

**Calculation:**

1. **Data Density:** 8 records → data_density_risk = 0.3
2. **Structural Integrity:** 5/6 favorable structures → 0.83
3. **Grade Statistics:**
   - Assays: [0.4, 0.6, 0.8, 1.2, 1.5, 2.0, 2.1, 2.3] g/t Au
   - Mean = 1.3 g/t
   - StDev = 0.8 g/t
   - Cutoff = 0.5 g/t
   - P(Au > 0.5 g/t) ≈ 0.82

4. **Composite Risk:**
   ```
   risk = (1.0 - 0.83) × 0.4 + (1.0 - 0.82) × 0.4 + 0.3 × 0.2
        = 0.068 + 0.072 + 0.06
        = 0.20 (20% dry hole risk)
   ```

5. **Recommendation:** "Proceed" (risk < 40%)

---

## SECTION 6: SYSTEM CALIBRATION PROTOCOL

### 6.1 Calibration Overview

The **Calibration Layer** forces all Aurora sub-modules to respect physical reality:

```
┌──────────────────────────────────────────────────────┐
│          AURORA SYSTEM CALIBRATION PROTOCOL          │
├──────────────────────────────────────────────────────┤
│                                                      │
│  Input: Ground Truth Vault Data                     │
│    ├─ Sonic logs (DT)                               │
│    ├─ Density logs (RHOB)                           │
│    ├─ Lab spectroscopy (ASD)                        │
│    ├─ Assay data                                    │
│    └─ Structural measurements                       │
│                                                      │
│  Process: Apply calibration to modules              │
│    ├─ Seismic Synthesizer (well-tie)               │
│    ├─ Spectral Harmonization (spectral GT)         │
│    ├─ Causal Core (edge reweighting)               │
│    ├─ Temporal Analytics (T-Zero reset)            │
│    ├─ Quantum Engine (Hamiltonian pinning)         │
│    └─ Digital Twin (physics injection)              │
│                                                      │
│  Output: Calibrated models with confidence delta    │
│                                                      │
└──────────────────────────────────────────────────────┘
```

### 6.2 Module-Specific Calibration

#### Module 1: SEISMIC SYNTHESIZER - Well-Tie Calibration

**Current:** Generates synthetic seismic from satellite-derived velocity models.

**New Calibration Logic:**
1. Extract sonic (DT) logs from Ground Truth
2. Extract density (RHOB) logs from Ground Truth
3. Calculate acoustic impedance: Z = velocity × density
4. Identify layer boundaries (impedance contrasts)
5. Extract **dominant wavelet** from impedance stratigraphy
6. **Force** the regional seismic synthesizer to use this calibrated wavelet

**Pseudo-code:**
```python
def well_tie_calibration(sonic_logs, density_logs, regional_model):
    # Convert DT (µs/ft) → velocity (m/s)
    velocity = 3280.84 / sonic_log['dt_us_ft']
    
    # Calculate impedance
    impedance = velocity * density_log['rhob_kg_m3']
    
    # Extract wavelet from impedance contrasts
    wavelet_peak_freq = extract_wavelet_frequency(impedance)
    
    # Correction factor
    correction = wavelet_peak_freq / regional_model['current_peak_freq']
    
    # Update regional model
    regional_model['wavelet_peak_freq'] *= correction
    regional_model['confidence'] = 0.9  # Boosted from well-tie
    
    return {"calibration_factor": correction, "confidence_gain": 0.3}
```

#### Module 2: SPECTRAL HARMONIZATION - Spectral Ground-Truthing

**Current:** Harmonizes satellite bands (ASTER, Sentinel) for mineral mapping.

**New Calibration Logic:**
1. Extract lab spectroscopy (ASD) from core samples in Ground Truth
2. Map to satellite pixels at borehole (x,y) coordinates
3. Calculate **atmospheric correction factor:** Lab_Feature / Satellite_Feature
4. Apply correction to entire region

**Pseudo-code:**
```python
def spectral_ground_truthing(lab_spectra, satellite_bands, borehole_coords):
    # Extract key absorption features from lab
    lab_al_oh = lab_spectra[borehole_coords]['al_oh_2.2um']
    lab_mg_oh = lab_spectra[borehole_coords]['mg_oh_2.3um']
    
    # Extract satellite pixel at borehole
    sat_al_oh = satellite_bands[borehole_coords]['al_oh_2.2um']
    sat_mg_oh = satellite_bands[borehole_coords]['mg_oh_2.3um']
    
    # Atmospheric correction
    correction_al_oh = lab_al_oh / sat_al_oh
    correction_mg_oh = lab_mg_oh / sat_mg_oh
    avg_correction = (correction_al_oh + correction_mg_oh) / 2
    
    # Apply to entire region
    satellite_bands['corrected'] = satellite_bands['original'] * avg_correction
    
    return {"correction_factor": avg_correction, "confidence_gain": 0.25}
```

#### Module 3: CAUSAL CORE - Edge Reweighting

**Current:** Identifies causal relationships (e.g., "Fault → Mineralization").

**New Calibration Logic:**
1. If Ground Truth contradicts a satellite-derived causal link:
   - **Strong contradiction:** Sever the edge (weight = 0)
   - **Weak contradiction:** Downgrade weight by 60%
2. If Ground Truth reinforces link:
   - Upgrade weight by 20% (capped at 1.0)

**Pseudo-code:**
```python
def reweight_causal_edges(causal_graph, assays):
    for edge in causal_graph:
        cause, effect, weight = edge['cause'], edge['effect'], edge['weight']
        
        # Count support/contradiction in assays
        support = len([a for a in assays if cause in a and a['grade'] > 0])
        contradiction = len([a for a in assays if cause in a and a['grade'] == 0])
        
        if contradiction > support * 2:
            edge['weight'] = 0  # SEVER
        elif contradiction > support:
            edge['weight'] *= 0.4  # DOWNGRADE
        elif support > 0:
            edge['weight'] = min(1.0, weight * 1.2)  # REINFORCE
```

#### Module 4: TEMPORAL ANALYTICS - T-Zero Baseline Reset

**Current:** Tracks 4D changes via satellite (subsidence, uplift, etc.).

**New Calibration Logic:**
- When a new borehole is logged, set that timestamp as the new **T-Zero baseline**
- Future satellite data is compared against this new physical reality
- Detects subtle subsurface shifts previously invisible

#### Module 5: QUANTUM ENGINE - Hamiltonian Constraints

**Current:** Optimizes search space via quantum annealing.

**New Calibration Logic:**
- Ground Truth points become **pinned vertices** in the quantum lattice
- Energy landscape (Hamiltonian) has local minima defined by Ground Truth
- Quantum solution must return high-probability states consistent with known data

**Pseudo-code:**
```python
def apply_hamiltonian_constraints(hamiltonian, ground_truth):
    for gt_point in ground_truth:
        # Add constraint: P(quantum_output = gt_value) > 0.95
        hamiltonian.add_constraint(
            variable=gt_point['location'],
            preferred_value=gt_point['measurement_value'],
            penalty_weight=1000  # High penalty for deviation
        )
    return hamiltonian
```

#### Module 6: DIGITAL TWIN - Physics-Based Accuracy

**Current:** 3D visual model based on satellite data (statistical approximation).

**New Calibration Logic:**
- Inject geological logs and core measurements directly into Twin geometry
- Twin becomes a **CAD-accurate representation** of the known subsurface
- AI/Quantum models only interpolate between known points

---

## SECTION 7: REGULATORY COMPLIANCE & EXPLAINABILITY

### 7.1 NI 43-101 / JORC Compliance

**Requirement:** Every prediction must cite its Ground Truth anchors.

**Format:**

> **Predicted Grade:** 2.4 g/t Au (± 0.6 g/t, 90% CI)  
> **Confidence Score:** 0.78 (78%)  
> **Anchored By:** 12 distinct data points  
> 
> **Key Anchors:**
> - Borehole DDH-1992-01 (USGS Public) - 2.1 g/t @ 150m depth (GTC=0.92)
> - Client Assay A (TIER_3_CLIENT) - 2.8 g/t @ 155m depth (GTC=0.81)
> - Borehole Core Photo Log - Phyllic alteration observed @ 148-152m depth
> - Structural Measurements - NE-striking fault within 200m (favorable)

### 7.2 Audit Trail Requirements

```
Every ground truth record must include:
1. Original source file name & timestamp
2. Ingested by (System user ID)
3. Chain of custody (upload → QC → vault steps)
4. Data hash (SHA256, immutable)
5. Validation status (RAW, QC_PASSED, PEER_REVIEWED)
6. All conflict resolutions and manual overrides
```

---

## SECTION 8: IMPLEMENTATION ARCHITECTURE

### 8.1 Technology Stack

**Backend:**
- FastAPI (Python) for REST API
- PostgreSQL with custom schemas (Tables: gtv_records, gtv_provenance, gtv_conflicts, etc.)
- Redis for caching (optional: conflict cache)

**Frontend:**
- React/TypeScript
- AuroraAPI class with GTV methods

**Database:**
- Migration: `0004_ground_truth_vault.sql` (8 new tables)
- Indexes on: location, depth, measurement_type, validation_status, mineral_context

### 8.2 API Endpoints

```
POST /gtv/ingest
  → Ingest single record into vault
  ← {record_id, gtc_score, success}

GET /gtv/conflicts
  → Retrieve all detected conflicts
  ← {total_conflicts, conflicts[...]}

POST /gtv/dry-hole-risk
  → Calculate dry hole probability
  ← {risk_percent, failure_mode, recommendation, anchors}

POST /gtv/calibrate
  → Execute full system calibration
  ← {modules_calibrated, confidence_improvements[...]}

GET /gtv/status
  → Query vault status
  ← {records_ingested, conflicts_detected, calibration_status}
```

### 8.3 Python Module Structure

```
backend/
├── ground_truth_vault.py
│   ├── GroundTruthVault (main engine)
│   ├── AuroraCommonSchema (data model)
│   ├── DataTier, Mineral, ValidationStatus (enums)
│   └── get_vault() (singleton)
│
├── calibration_controller.py
│   ├── CalibrationController (master orchestrator)
│   ├── SeismicSynthesizerCalibrator
│   ├── SpectralHarmonizationCalibrator
│   ├── CausalCoreCalibrator
│   └── get_calibration_controller() (singleton)
│
├── main.py
│   ├── @app.post("/gtv/ingest")
│   ├── @app.get("/gtv/conflicts")
│   ├── @app.post("/gtv/dry-hole-risk")
│   ├── @app.post("/gtv/calibrate")
│   └── @app.get("/gtv/status")
│
└── db/migrations/
    └── 0004_ground_truth_vault.sql (8 tables)
```

---

## SECTION 9: INTEGRATION CHECKLIST

- [x] Aurora Common Schema (ACS) defined
- [x] Database migration (8 tables) created
- [x] GroundTruthVault engine implemented
- [x] Conflict resolution logic implemented
- [x] GTC 2.0 scoring algorithm implemented
- [x] Dry hole risk calculator implemented
- [x] Calibration controller implemented
- [x] Seismic well-tie calibration implemented
- [x] Spectral harmonization calibration implemented
- [x] Causal core reweighting implemented
- [x] FastAPI endpoints added
- [x] Frontend API methods added
- [ ] Database connection & migrations applied
- [ ] Test suite for conflict resolution
- [ ] Test suite for GTC scoring
- [ ] Production deployment & monitoring

---

## SECTION 10: SUMMARY & NEXT STEPS

**What A-GTV Solves:**

1. **Model Drift Elimination** - Satellite predictions constrained by physical reality
2. **Regulatory Compliance** - Full audit trail, confidence scoring, explainability
3. **Risk Quantification** - Dry hole probability with 90% confidence intervals
4. **Multi-Source Harmonization** - Authority-based conflict resolution
5. **Continuous Learning** - New ground truth automatically recalibrates all modules

**Production Deployment:**

1. Apply database migration to PostgreSQL
2. Seed with TIER_1 (USGS) baseline data via bulk import
3. Configure TIER_3 (client) ingestion workflows
4. Deploy calibration controller and test on existing Aurora modules
5. Validate that satellite predictions respect ground truth constraints

**Key Principle:**

> **"Ground Truth is not another data source. Ground Truth is the anchor that keeps AI honest."**

---

**Document Version:** 2.0  
**Last Updated:** 2026-01-19  
**Status:** Ready for Implementation
