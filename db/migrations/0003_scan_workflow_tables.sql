-- Aurora OSI v3: Scan Workflow Tables
-- Purpose: Store scan execution history and all analysis outputs
-- Created: 2024

-- Table: scans (master scan records)
CREATE TABLE IF NOT EXISTS scans (
    id TEXT PRIMARY KEY,
    scan_name TEXT NOT NULL,
    latitude REAL NOT NULL,
    longitude REAL NOT NULL,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    overall_status TEXT DEFAULT 'pending', -- pending, running, completed, failed
    user_id TEXT,
    
    -- Timing
    started_at DATETIME,
    completed_at DATETIME,
    duration_seconds INTEGER,
    
    -- Error tracking
    error_message TEXT,
    error_code TEXT,
    
    -- Metadata
    source_satellite TEXT DEFAULT 'sentinel-2',
    cloud_coverage REAL,
    spatial_resolution_m INTEGER DEFAULT 10,
    
    INDEX idx_timestamp (timestamp),
    INDEX idx_status (overall_status),
    INDEX idx_location (latitude, longitude)
);

-- Table: scan_results (detailed analysis outputs)
CREATE TABLE IF NOT EXISTS scan_results (
    id TEXT PRIMARY KEY,
    scan_id TEXT NOT NULL,
    
    -- PINN Analysis
    pinn_output_json TEXT,
    pinn_status TEXT DEFAULT 'pending', -- pending, running, completed, failed
    pinn_error TEXT,
    pinn_completed_at DATETIME,
    
    -- USHE Harmonization
    ushe_output_json TEXT,
    ushe_status TEXT DEFAULT 'pending',
    ushe_error TEXT,
    ushe_completed_at DATETIME,
    
    -- TMAL Temporal Analysis
    tmal_output_json TEXT,
    tmal_status TEXT DEFAULT 'pending',
    tmal_error TEXT,
    tmal_completed_at DATETIME,
    
    -- Metadata
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (scan_id) REFERENCES scans(id) ON DELETE CASCADE,
    INDEX idx_scan_id (scan_id),
    INDEX idx_created_at (created_at)
);

-- Table: visualizations (2D and 3D visualization outputs)
CREATE TABLE IF NOT EXISTS visualizations (
    id TEXT PRIMARY KEY,
    scan_id TEXT NOT NULL,
    
    -- 2D Visualization
    visualization_2d_data TEXT, -- JSON: map coordinates, colors, overlays
    visualization_2d_generated_at DATETIME,
    
    -- 3D Visualization
    visualization_3d_data TEXT, -- JSON: mesh data, terrain, subsurface layers
    visualization_3d_generated_at DATETIME,
    
    -- Metadata
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (scan_id) REFERENCES scans(id) ON DELETE CASCADE,
    INDEX idx_scan_id (scan_id)
);

-- Table: mineral_detections (detected minerals per scan)
CREATE TABLE IF NOT EXISTS mineral_detections (
    id TEXT PRIMARY KEY,
    scan_id TEXT NOT NULL,
    
    mineral_name TEXT NOT NULL,
    confidence_score REAL,
    wavelength_feature REAL,
    
    location_lat REAL,
    location_lon REAL,
    area_km2 REAL,
    
    depth_estimate_m REAL,
    
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (scan_id) REFERENCES scans(id) ON DELETE CASCADE,
    INDEX idx_scan_id (scan_id),
    INDEX idx_mineral (mineral_name),
    INDEX idx_confidence (confidence_score)
);

-- Table: scan_steps (track each step of the 7-step workflow)
CREATE TABLE IF NOT EXISTS scan_steps (
    id TEXT PRIMARY KEY,
    scan_id TEXT NOT NULL,
    
    step_name TEXT NOT NULL, -- fetch-satellite, spectral, pinn, ushe, tmal, visualizations, store
    step_order INTEGER,
    
    status TEXT DEFAULT 'pending', -- pending, running, completed, error
    progress_percentage INTEGER DEFAULT 0,
    
    error_message TEXT,
    error_code TEXT,
    
    started_at DATETIME,
    completed_at DATETIME,
    duration_ms INTEGER,
    
    FOREIGN KEY (scan_id) REFERENCES scans(id) ON DELETE CASCADE,
    INDEX idx_scan_id (scan_id),
    INDEX idx_step_order (scan_id, step_order)
);

-- Create indexes for common queries
CREATE INDEX IF NOT EXISTS idx_scans_recent ON scans(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_scans_user ON scans(user_id, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_scan_results_by_scan ON scan_results(scan_id);
CREATE INDEX IF NOT EXISTS idx_visualizations_by_scan ON visualizations(scan_id);
