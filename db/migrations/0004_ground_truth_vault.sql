-- Aurora Ground Truth Vault (A-GTV) v2.0
-- Enhanced schema for regulatory-grade subsurface data with provenance tracking
-- Migration: 0004_ground_truth_vault.sql

-- 1. PROVENANCE & AUDIT TRAIL
CREATE TABLE IF NOT EXISTS gtv_provenance (
    id SERIAL PRIMARY KEY,
    record_id UUID NOT NULL,
    ingestion_timestamp TIMESTAMP NOT NULL DEFAULT NOW(),
    ingested_by VARCHAR(255) NOT NULL,
    original_file VARCHAR(512),
    chain_of_custody TEXT[] DEFAULT ARRAY[]::TEXT[], -- e.g., ['Client_Upload', 'Quality_Check', 'Vault']
    data_hash VARCHAR(128) NOT NULL, -- SHA256 digest
    source_tier VARCHAR(50) NOT NULL CHECK (source_tier IN ('TIER_1_PUBLIC', 'TIER_2_COMMERCIAL', 'TIER_3_CLIENT', 'TIER_4_REALTIME', 'TIER_5_SECURITY')),
    source_organization VARCHAR(255),
    source_license VARCHAR(255) DEFAULT 'Proprietary',
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(record_id, data_hash)
);

-- 2. GROUND TRUTH RECORDS (Aurora Common Schema)
CREATE TABLE IF NOT EXISTS gtv_records (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Location & Coordinates
    latitude FLOAT8 NOT NULL,
    longitude FLOAT8 NOT NULL,
    depth_m FLOAT8, -- Single point or top of interval
    depth_bottom_m FLOAT8, -- Bottom of interval (for logs)
    crs VARCHAR(50) DEFAULT 'EPSG:4326',
    spatial_uncertainty_m FLOAT8 DEFAULT 50.0,
    
    -- Measurement Type & Value
    measurement_type VARCHAR(50) NOT NULL CHECK (measurement_type IN (
        'seismic_velocity', 'density', 'assay_ppm', 'lithology', 'porosity',
        'permeability', 'sonic_dt', 'gravity', 'magnetic', 'spectral_reflectance',
        'temperature', 'pressure', 'breakout', 'core_description'
    )),
    measurement_value FLOAT8, -- NULL for categorical (lithology)
    measurement_unit VARCHAR(50), -- e.g., 'm/s', 'kg/m3', 'ppm', '%'
    detection_limit FLOAT8, -- For non-detects
    is_non_detect BOOLEAN DEFAULT FALSE, -- Crucial for assay data
    
    -- Lithology & Geologic Context
    lithology_code VARCHAR(50), -- e.g., 'granodiorite', 'shale', 'limestone'
    mineralization_style VARCHAR(50) CHECK (mineralization_style IN (
        'porphyry', 'vein', 'placer', 'MVT', 'sediment_hosted', 'skarn', 'epithermal', 'none'
    )),
    alteration_type VARCHAR(50) CHECK (alteration_type IN (
        'argillic', 'phyllic', 'potassic', 'silicic', 'carbonate', 'propylitic', 'none'
    )),
    structural_control VARCHAR(50) CHECK (structural_control IN (
        'fault_zone', 'fold_hinge', 'stratabound', 'none'
    )),
    
    -- Quality & Validation
    validation_status VARCHAR(50) NOT NULL DEFAULT 'RAW' CHECK (validation_status IN ('RAW', 'QC_PASSED', 'PEER_REVIEWED')),
    gtc_score FLOAT8 NOT NULL DEFAULT 0.5, -- Ground Truth Confidence: 0.0-1.0
    confidence_basis VARCHAR(255), -- e.g., 'Laboratory_Assay', 'Wireline_Log', 'Seismic_Interpretation'
    
    -- Conflict Resolution
    conflict_status VARCHAR(50) DEFAULT 'clean' CHECK (conflict_status IN ('clean', 'flagged_vs_tier_1', 'flagged_vs_tier_2', 'flagged_vs_neighbor')),
    conflict_notes TEXT,
    resolved_by VARCHAR(255), -- Admin user who resolved conflict
    resolved_at TIMESTAMP,
    
    -- Mineral-Specific Metadata (JSON for flexibility)
    mineral_context JSONB DEFAULT '{}', -- e.g., {"target_mineral": "Au", "grade_shell": "high", "vein_width_cm": 45}
    
    -- Provenance Foreign Key
    provenance_id INTEGER REFERENCES gtv_provenance(id) ON DELETE CASCADE,
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    CONSTRAINT gtv_records_location CHECK (latitude BETWEEN -90 AND 90 AND longitude BETWEEN -180 AND 180)
);

CREATE INDEX idx_gtv_records_location ON gtv_records (latitude, longitude);
CREATE INDEX idx_gtv_records_depth ON gtv_records (depth_m);
CREATE INDEX idx_gtv_records_measurement ON gtv_records (measurement_type);
CREATE INDEX idx_gtv_records_validation ON gtv_records (validation_status);
CREATE INDEX idx_gtv_records_mineral ON gtv_records (mineral_context);

-- 3. TIER 1 (PUBLIC AUTHORITATIVE) CACHED DATA
CREATE TABLE IF NOT EXISTS gtv_tier1_usgs (
    id SERIAL PRIMARY KEY,
    usgs_record_id VARCHAR(255) UNIQUE,
    latitude FLOAT8 NOT NULL,
    longitude FLOAT8 NOT NULL,
    depth_m FLOAT8,
    data_type VARCHAR(100), -- e.g., 'borehole_assay', 'geochemistry'
    value_json JSONB NOT NULL,
    source_url TEXT,
    fetched_at TIMESTAMP DEFAULT NOW(),
    expires_at TIMESTAMP DEFAULT NOW() + INTERVAL '1 year', -- Cache TTL
    UNIQUE(usgs_record_id, latitude, longitude)
);

CREATE INDEX idx_tier1_usgs_location ON gtv_tier1_usgs (latitude, longitude);
CREATE INDEX idx_tier1_usgs_expiry ON gtv_tier1_usgs (expires_at);

-- 4. CONFLICT RESOLUTION LOG
CREATE TABLE IF NOT EXISTS gtv_conflicts (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP DEFAULT NOW(),
    record_id_a UUID REFERENCES gtv_records(id) ON DELETE CASCADE,
    record_id_b UUID REFERENCES gtv_records(id) ON DELETE CASCADE,
    conflict_type VARCHAR(100), -- e.g., 'depth_mismatch', 'grade_contradiction', 'lithology_disagreement'
    severity_level VARCHAR(50) CHECK (severity_level IN ('low', 'medium', 'high', 'critical')),
    delta_percent FLOAT8, -- Percentage difference
    resolution_method VARCHAR(100), -- e.g., 'authority_ranking', 'manual_review', 'consensus_weighted'
    winning_record_id UUID REFERENCES gtv_records(id),
    reviewer_notes TEXT,
    resolved_at TIMESTAMP,
    resolved_by VARCHAR(255),
    CONSTRAINT conflict_not_self CHECK (record_id_a != record_id_b)
);

CREATE INDEX idx_conflicts_records ON gtv_conflicts (record_id_a, record_id_b);
CREATE INDEX idx_conflicts_severity ON gtv_conflicts (severity_level);

-- 5. MINERAL-SPECIFIC CONTEXT TABLE
CREATE TABLE IF NOT EXISTS gtv_mineral_domains (
    id SERIAL PRIMARY KEY,
    mineral_code VARCHAR(20) NOT NULL UNIQUE, -- 'Au', 'Li', 'Cu', 'Fe', etc.
    mineral_name VARCHAR(100),
    
    -- Mineral-specific ground truth metrics
    primary_indicator VARCHAR(100), -- e.g., 'structural_vector' for Au, 'brine_chemistry' for Li
    secondary_indicators TEXT[], -- Additional validation checks
    depth_range_min_m FLOAT8,
    depth_range_max_m FLOAT8,
    typical_host_lithologies TEXT[],
    
    -- Risk weighting
    false_positive_weight FLOAT8 DEFAULT 0.3, -- Cost of predicting mineral when absent
    false_negative_weight FLOAT8 DEFAULT 0.7, -- Cost of missing actual mineral
    
    -- Quality thresholds
    min_gtc_for_drilling FLOAT8 DEFAULT 0.75,
    
    created_at TIMESTAMP DEFAULT NOW()
);

-- 6. BOREHOLE CATALOG (Integration with logs)
CREATE TABLE IF NOT EXISTS gtv_boreholes (
    id SERIAL PRIMARY KEY,
    hole_id VARCHAR(255) UNIQUE NOT NULL,
    latitude FLOAT8 NOT NULL,
    longitude FLOAT8 NOT NULL,
    collar_elevation_m FLOAT8,
    total_depth_m FLOAT8 NOT NULL,
    
    -- Status & Type
    hole_status VARCHAR(50), -- 'completed', 'in_progress', 'plugged'
    hole_type VARCHAR(50), -- 'exploration', 'production', 'appraisal'
    drilling_operator VARCHAR(255),
    spud_date DATE,
    completion_date DATE,
    
    -- Associated Data
    has_sonic_log BOOLEAN DEFAULT FALSE,
    has_density_log BOOLEAN DEFAULT FALSE,
    has_assay BOOLEAN DEFAULT FALSE,
    has_core_photos BOOLEAN DEFAULT FALSE,
    
    -- Audit
    ingested_at TIMESTAMP DEFAULT NOW(),
    ingested_by VARCHAR(255),
    
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_boreholes_location ON gtv_boreholes (latitude, longitude);
CREATE INDEX idx_boreholes_status ON gtv_boreholes (hole_status);

-- 7. DRY HOLE RISK ASSESSMENT
CREATE TABLE IF NOT EXISTS gtv_risk_assessments (
    id SERIAL PRIMARY KEY,
    assessment_id UUID DEFAULT gen_random_uuid() UNIQUE,
    target_latitude FLOAT8 NOT NULL,
    target_longitude FLOAT8 NOT NULL,
    target_mineral VARCHAR(20),
    assessment_timestamp TIMESTAMP DEFAULT NOW(),
    
    -- Risk Factors
    data_density_nearby_1km INTEGER, -- Count of GT records within 1km
    structural_integrity_score FLOAT8, -- 0.0-1.0
    grade_probability_vs_cutoff FLOAT8, -- P(grade > economic_threshold)
    
    -- Final Risk
    dry_hole_risk_percent FLOAT8, -- 0-100%
    critical_failure_mode VARCHAR(100), -- 'structure', 'grade', 'mineral_absence'
    recommended_action VARCHAR(255), -- 'Proceed', 'Acquire_3D_Seismic', 'Acquire_More_Data'
    confidence_interval_90_low FLOAT8,
    confidence_interval_90_high FLOAT8,
    
    -- Explainability (Links to anchoring records)
    anchor_record_ids UUID[] DEFAULT ARRAY[]::UUID[],
    
    reviewer_validated BOOLEAN DEFAULT FALSE,
    validated_by VARCHAR(255),
    validated_at TIMESTAMP,
    
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_risk_assessments_location ON gtv_risk_assessments (target_latitude, target_longitude);

-- 8. CALIBRATION AUDIT TRAIL (For module integration)
CREATE TABLE IF NOT EXISTS gtv_calibration_log (
    id SERIAL PRIMARY KEY,
    module_name VARCHAR(100), -- e.g., 'seismic_synthesizer', 'spectral_harmonization'
    operation VARCHAR(100), -- e.g., 'well_tie_calibration', 'wavelet_extraction'
    input_gt_records UUID[] DEFAULT ARRAY[]::UUID[],
    calibration_factor FLOAT8, -- Adjustment applied
    confidence_before FLOAT8,
    confidence_after FLOAT8,
    timestamp TIMESTAMP DEFAULT NOW(),
    execution_time_ms INTEGER,
    success BOOLEAN DEFAULT TRUE,
    error_message TEXT
);

-- Grant permissions (adjust as needed for your environment)
-- GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA public TO aurora_app_user;
-- GRANT USAGE ON ALL SEQUENCES IN SCHEMA public TO aurora_app_user;
