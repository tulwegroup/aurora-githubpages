-- Aurora OSI v3 - Scans Table Migration
-- Supports point, radius, and grid scanning operations

CREATE TABLE IF NOT EXISTS scans (
    id SERIAL PRIMARY KEY,
    scan_id VARCHAR(50) UNIQUE NOT NULL,
    scan_type VARCHAR(20) NOT NULL,  -- point, radius, grid
    status VARCHAR(20) NOT NULL DEFAULT 'pending',  -- pending, running, completed, failed, archived
    
    -- Location Information
    latitude FLOAT,
    longitude FLOAT,
    country VARCHAR(100),
    region VARCHAR(100),
    radius_km FLOAT DEFAULT 0,
    grid_spacing_m FLOAT DEFAULT 30,
    area_km2 FLOAT,
    
    -- Scan Configuration
    minerals TEXT[] NOT NULL,  -- Array of mineral names
    resolution VARCHAR(20) DEFAULT 'native',  -- native, high, medium, low
    sensor VARCHAR(50) DEFAULT 'Sentinel-2',  -- Sentinel-2 or Landsat-8
    max_cloud_cover_percent FLOAT DEFAULT 20.0,
    
    -- Temporal Information
    date_start DATE,
    date_end DATE,
    created_at TIMESTAMP DEFAULT NOW(),
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    
    -- Results Metadata
    pixel_count_total INTEGER DEFAULT 0,
    detections_found INTEGER DEFAULT 0,
    confidence_average FLOAT,
    
    -- Error Handling
    error_message TEXT,
    
    -- Indices for fast queries
    INDEX idx_scan_id (scan_id),
    INDEX idx_status (status),
    INDEX idx_created_at (created_at),
    INDEX idx_country_region (country, region)
);

-- Scan Results Table - Stores pixel-by-pixel detection results
CREATE TABLE IF NOT EXISTS scan_results (
    id SERIAL PRIMARY KEY,
    scan_id VARCHAR(50) NOT NULL REFERENCES scans(scan_id) ON DELETE CASCADE,
    
    -- Pixel Location
    latitude FLOAT NOT NULL,
    longitude FLOAT NOT NULL,
    pixel_x INTEGER,
    pixel_y INTEGER,
    
    -- Detection Information
    mineral VARCHAR(100) NOT NULL,
    confidence_score FLOAT NOT NULL,
    confidence_tier VARCHAR(20),
    spectral_match_score FLOAT,
    spectral_features JSONB,
    
    -- Temporal Information
    detected_at TIMESTAMP DEFAULT NOW(),
    satellite_capture_date DATE,
    
    -- Indices
    INDEX idx_scan_id_mineral (scan_id, mineral),
    INDEX idx_coordinates (latitude, longitude),
    INDEX idx_confidence (confidence_score DESC)
);

-- Scan Summary Table - Quick access to aggregated results
CREATE TABLE IF NOT EXISTS scan_summaries (
    id SERIAL PRIMARY KEY,
    scan_id VARCHAR(50) UNIQUE NOT NULL REFERENCES scans(scan_id) ON DELETE CASCADE,
    
    -- Summary Statistics
    total_pixels_scanned INTEGER,
    total_detections INTEGER,
    detection_rate_percent FLOAT,
    high_confidence_detections INTEGER,  -- confidence >= 0.8
    medium_confidence_detections INTEGER,  -- 0.5 <= confidence < 0.8
    low_confidence_detections INTEGER,  -- confidence < 0.5
    
    -- Per-Mineral Breakdown
    mineral_breakdown JSONB,  -- {"gold": 45, "lithium": 12, ...}
    
    -- Processing Information
    scan_duration_minutes FLOAT,
    
    -- Indices
    INDEX idx_scan_id (scan_id)
);

-- Scan Queue Table - For background processing
CREATE TABLE IF NOT EXISTS scan_queue (
    id SERIAL PRIMARY KEY,
    scan_id VARCHAR(50) UNIQUE NOT NULL REFERENCES scans(scan_id) ON DELETE CASCADE,
    
    priority INTEGER DEFAULT 0,  -- Higher = more urgent
    retry_count INTEGER DEFAULT 0,
    max_retries INTEGER DEFAULT 3,
    
    last_attempted TIMESTAMP,
    next_retry_time TIMESTAMP,
    
    -- Worker tracking
    assigned_worker VARCHAR(100),
    
    -- Indices
    INDEX idx_status_priority (status, priority DESC),
    INDEX idx_next_retry (next_retry_time)
);
