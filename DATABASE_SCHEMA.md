# Aurora OSI v3 - Database & Schema Documentation

## Database Architecture

### Deployment Topologies

**Development (Local)**
```
┌─────────────────────┐
│   PostgreSQL 15     │
│   (Docker)          │
│   port: 5432        │
│   user: postgres    │
│   pass: postgres    │
└─────────────────────┘
```

**Production (Neon)**
```
┌─────────────────────────────────┐
│   Neon PostgreSQL 15            │
│   (Managed Cloud)               │
│   SSL/TLS Encryption            │
│   Daily Automated Backups       │
│   Connection Pooling (PgBouncer)│
└─────────────────────────────────┘
```

---

## Schema Design

### Core Tables

#### 1. mineral_detections
Stores all mineral detection results from satellite analysis

```sql
CREATE TABLE mineral_detections (
    id BIGINT PRIMARY KEY,
    mineral VARCHAR(255) NOT NULL,
    confidence_score FLOAT NOT NULL CHECK (confidence_score >= 0 AND confidence_score <= 1),
    confidence_tier VARCHAR(10) NOT NULL IN ('TIER_0', 'TIER_1', 'TIER_2', 'TIER_3'),
    latitude DECIMAL(10, 7) NOT NULL,
    longitude DECIMAL(10, 7) NOT NULL,
    depth_m FLOAT NOT NULL,
    sensor VARCHAR(50) NOT NULL,
    date_detected TIMESTAMP NOT NULL,
    processing_time_ms INT,
    spectral_match_score FLOAT,
    temporal_coherence FLOAT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_mineral (mineral),
    INDEX idx_confidence_tier (confidence_tier),
    INDEX idx_location (latitude, longitude),
    INDEX idx_date_detected (date_detected)
);
```

**Indexes:**
- `idx_mineral`: Find all detections of specific mineral
- `idx_confidence_tier`: Filter by confidence tier (exploration/drill-ready)
- `idx_location`: Geographic queries (spatial)
- `idx_date_detected`: Time-series analysis

**Partitioning Strategy:**
```sql
-- Partition by year for efficient time-based queries
PARTITION BY RANGE (YEAR(date_detected));
```

---

#### 2. digital_twin_voxels
4D subsurface model storage (spatial-temporal voxel grid)

```sql
CREATE TABLE digital_twin_voxels (
    id BIGINT PRIMARY KEY,
    region VARCHAR(255) NOT NULL,
    x INT NOT NULL,
    y INT NOT NULL,
    z INT NOT NULL,  -- Depth
    
    -- Rock properties
    rock_type_primary VARCHAR(100) NOT NULL,
    rock_type_probability JSONB NOT NULL,  -- {sandstone: 0.6, shale: 0.3}
    density_kg_m3 FLOAT NOT NULL,
    density_uncertainty FLOAT,
    
    -- Mineral assemblage
    mineral_assemblage JSONB NOT NULL,  -- {quartz: 0.5, feldspar: 0.3}
    
    -- Fluid properties
    porosity FLOAT,
    saturation FLOAT,
    pore_fluid_type VARCHAR(50),  -- oil, gas, water, mixed
    permeability_mdarcy FLOAT,
    
    -- Temporal
    timestamp TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_region_xyz (region, x, y, z),
    INDEX idx_timestamp (timestamp),
    UNIQUE (region, x, y, z, timestamp)
);
```

**Properties:**
- **Rock Type Probability (JSONB)**: Stores probability distribution over lithologies
- **Mineral Assemblage (JSONB)**: Mineral compositions with percentages
- **Spatial Indexing**: (region, x, y, z) for volumetric queries
- **Temporal**: Multiple voxels per location track 4D evolution

**JSONB Queries:**
```sql
-- Find voxels with high quartz content
SELECT * FROM digital_twin_voxels 
WHERE mineral_assemblage @> '{"quartz": 0.5}';

-- Find voxels with >50% probability of sandstone
SELECT * FROM digital_twin_voxels 
WHERE rock_type_probability ->> 'sandstone'::float > 0.5;
```

---

#### 3. satellite_tasks
Autonomous satellite data acquisition requests

```sql
CREATE TABLE satellite_tasks (
    id BIGINT PRIMARY KEY,
    task_id VARCHAR(255) UNIQUE NOT NULL,
    latitude DECIMAL(10, 7) NOT NULL,
    longitude DECIMAL(10, 7) NOT NULL,
    sensor_type VARCHAR(50) NOT NULL,  -- optical, SAR, thermal, lidar
    resolution_m FLOAT NOT NULL,
    area_km2 FLOAT NOT NULL,
    urgency VARCHAR(20) NOT NULL,  -- standard, urgent, critical
    
    status VARCHAR(50) NOT NULL,  -- pending, scheduled, acquired, processing, ready, failed
    estimated_cost_usd FLOAT NOT NULL,
    actual_cost_usd FLOAT,
    
    data_url VARCHAR(500),
    acquired_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_status (status),
    INDEX idx_created_at (created_at)
);
```

**Status Lifecycle:**
```
pending → scheduled → acquired → processing → ready
                ↘                    ↗
                         ↓
                       failed
```

---

#### 4. seismic_twin
3D seismic survey metadata

```sql
CREATE TABLE seismic_twin (
    id BIGINT PRIMARY KEY,
    survey_id VARCHAR(255) UNIQUE NOT NULL,
    region VARCHAR(255) NOT NULL,
    
    grid_config JSONB NOT NULL,  -- {inlines: 500, crosslines: 750}
    depth_samples INT NOT NULL,
    depth_min_m FLOAT NOT NULL,
    depth_max_m FLOAT NOT NULL,
    voxel_size_m FLOAT NOT NULL,
    
    total_voxel_count BIGINT,
    storage_gb FLOAT,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_survey_id (survey_id),
    INDEX idx_region (region)
);
```

---

#### 5. seismic_voxels
Individual seismic voxel data

```sql
CREATE TABLE seismic_voxels (
    id BIGINT PRIMARY KEY,
    survey_id VARCHAR(255) NOT NULL,
    inline INT NOT NULL,
    crossline INT NOT NULL,
    depth_m FLOAT NOT NULL,
    
    -- Seismic attributes
    amplitude FLOAT NOT NULL,
    frequency_hz FLOAT,
    phase FLOAT,
    
    -- Rock properties derived from seismic
    impedance FLOAT,
    p_wave_velocity_m_s FLOAT,
    s_wave_velocity_m_s FLOAT,
    
    -- Fluid properties
    porosity FLOAT,
    saturation FLOAT,
    fluid_type VARCHAR(50),
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_survey_location (survey_id, inline, crossline, depth_m),
    UNIQUE (survey_id, inline, crossline, depth_m)
);
```

**Partitioning Strategy:**
```sql
-- Partition by survey for efficient bulk loading
CREATE TABLE seismic_voxels_SEIS_2025_001 
  PARTITION OF seismic_voxels
  FOR VALUES IN ('SEIS_2025_001');
```

---

#### 6. physics_residuals
Physics constraint violation tracking

```sql
CREATE TABLE physics_residuals (
    id BIGINT PRIMARY KEY,
    latitude DECIMAL(10, 7) NOT NULL,
    longitude DECIMAL(10, 7) NOT NULL,
    depth_m FLOAT NOT NULL,
    
    physics_law VARCHAR(100) NOT NULL,  -- Poisson_equation, lithostatic_gradient, etc.
    residual_magnitude FLOAT NOT NULL,
    severity VARCHAR(20) NOT NULL,  -- low, medium, high, critical
    
    violation_type VARCHAR(100),
    recommended_correction JSONB,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_severity (severity),
    INDEX idx_physics_law (physics_law),
    INDEX idx_created_at (created_at)
);
```

---

## Data Dictionary

### Enumerations

**Confidence Tiers**
```
TIER_0: < 55% confidence → REJECT
TIER_1: 55-70% confidence → RECONNAISSANCE target
TIER_2: 70-85% confidence → EXPLORATION target
TIER_3: > 85% confidence → DRILL-READY prospect
```

**Satellite Sensors**
```
optical: High-resolution multispectral (Planet, Maxar)
SAR: Synthetic Aperture Radar (Capella, ICEYE)
thermal: Thermal infrared (night-time temp)
lidar: Light Detection and Ranging (topography)
hyperspectral: Full spectrum imaging (PRISMA)
```

**Urgency Levels**
```
standard: 7-14 day acquisition window
urgent: 2-7 day acquisition window
critical: 24-hour acquisition (premium cost)
```

**Rock Types** (from USGS classification)
```
sandstone, shale, limestone, dolomite, granite, basalt, 
andesite, rhyolite, gneiss, schist, amphibolite, eclogite,
marble, quartzite, mudstone, siltstone, conglomerate, 
breccia, tuff, obsidian, pumice
```

**Fluid Types**
```
oil: Crude oil
gas: Natural gas
water: Fresh/saline water
mixed: Multi-phase (oil + gas)
brine: High salinity water
```

---

## Migration Strategy

### Development to Production Migration

```bash
# 1. Create backup of development
pg_dump -U postgres aurora_osi_v3 > dev_backup.sql

# 2. Create Neon database (via web console)
# 3. Connect to Neon
export DATABASE_URL="postgresql://user:pass@endpoint.neon.tech/aurora_osi_v3"

# 4. Initialize schema (automatic on backend startup)
python -c "from backend.database import DatabaseManager; db = DatabaseManager()"

# 5. Verify tables created
psql $DATABASE_URL -c "\dt"

# 6. Optional: Migrate sample data
psql $DATABASE_URL < dev_backup.sql
```

### Schema Migrations (if needed)

Create migration files:
```sql
-- migrations/0002_add_seismic_voxel_indexes.sql
CREATE INDEX CONCURRENTLY idx_seismic_voxels_amplitude 
  ON seismic_voxels(survey_id, amplitude);
```

Run migrations:
```python
# In backend/database.py
async def run_migrations():
    migration_files = sorted(glob("migrations/*.sql"))
    async with engine.begin() as conn:
        for file in migration_files:
            with open(file) as f:
                await conn.run_sync(lambda c: c.execute(text(f.read())))
```

---

## Backup & Recovery

### Neon Automated Backups

Enable in Neon console:
- **Daily backups**: Automatic (included)
- **Point-in-time recovery**: 7 days
- **Manual snapshots**: Create anytime

### Manual Backup

```bash
# Full backup
pg_dump -U postgres -d aurora_osi_v3 \
  --format=custom \
  --file=backup_$(date +%Y%m%d).dump

# Restore from backup
pg_restore --format=custom --dbname=aurora_osi_v3 backup_20260114.dump

# Schema-only backup (for version control)
pg_dump -U postgres -d aurora_osi_v3 \
  --schema-only > schema.sql
```

### Disaster Recovery

```bash
# If database becomes corrupted
# 1. In Neon: Select "Restore from backup"
# 2. Choose restore point
# 3. Wait for restore (usually < 5 minutes)
# 4. Update DATABASE_URL if endpoint changed
# 5. Verify data integrity
```

---

## Query Optimization

### Common Queries

**Find all TIER_2+ detections in region**
```sql
SELECT * FROM mineral_detections 
WHERE latitude BETWEEN -21 AND -20
  AND longitude BETWEEN 134 AND 135
  AND confidence_tier IN ('TIER_2', 'TIER_3')
ORDER BY confidence_score DESC;
```

**Query volumetric resource in depth range**
```sql
SELECT 
  COUNT(*) as voxel_count,
  AVG(density_kg_m3) as avg_density,
  SUM(CAST(mineral_assemblage->'copper' as float)) as copper_total
FROM digital_twin_voxels 
WHERE region = 'Australia'
  AND z BETWEEN 100 AND 1500;
```

**Get satellite task status**
```sql
SELECT 
  status,
  COUNT(*) as count,
  AVG(EXTRACT(DAY FROM (acquired_at - created_at))) as avg_days_to_acquire
FROM satellite_tasks 
WHERE created_at > NOW() - INTERVAL '30 days'
GROUP BY status;
```

### Index Strategy

**Columns to Index:**
- `mineral` (frequent filter)
- `confidence_tier` (tier-based decisions)
- `latitude, longitude` (spatial queries)
- `date_detected` (time-series)
- `survey_id, inline, crossline, depth_m` (seismic queries)
- `physics_law`, `severity` (constraint filtering)

**Avoid Indexing:**
- JSONB fields (unless using GIN indexes for contains queries)
- Columns with low cardinality
- Columns updated frequently

---

## Performance Tuning

### Connection Pooling

**For Railway/Neon:**
```python
from sqlalchemy.pool import QueuePool

engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=20,
    max_overflow=40,
    pool_pre_ping=True,  # Test connections before use
    pool_recycle=3600,   # Recycle connections every hour
)
```

### Query Hints

```python
# For large seismic voxel queries, use batch processing
def query_seismic_voxels_batched(survey_id, batch_size=10000):
    query = session.query(SeismicVoxel).filter_by(survey_id=survey_id)
    for i in range(0, query.count(), batch_size):
        yield query.offset(i).limit(batch_size).all()
```

### EXPLAIN ANALYZE

```bash
# Analyze query performance
psql $DATABASE_URL << EOF
EXPLAIN ANALYZE
SELECT * FROM mineral_detections 
WHERE latitude BETWEEN -21 AND -20
  AND confidence_tier = 'TIER_2';
EOF
```

---

## Data Retention Policy

### Automatic Cleanup

```sql
-- Archive old detections (> 2 years)
DELETE FROM mineral_detections 
WHERE date_detected < NOW() - INTERVAL '2 years'
  AND confidence_tier = 'TIER_0';

-- Archive completed satellite tasks
DELETE FROM satellite_tasks 
WHERE status IN ('failed', 'ready')
  AND updated_at < NOW() - INTERVAL '90 days';
```

---

## Monitoring & Alerts

### Key Metrics

```sql
-- Database size
SELECT pg_size_pretty(pg_database_size('aurora_osi_v3'));

-- Table sizes
SELECT schemaname, tablename, pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) 
FROM pg_tables 
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;

-- Index size and usage
SELECT schemaname, tablename, indexname, pg_size_pretty(pg_relation_size(indexrelid))
FROM pg_indexes;

-- Active connections
SELECT count(*) FROM pg_stat_activity;
```

### Neon Monitoring Dashboard

Access at: https://console.neon.tech

Monitor:
- Storage usage
- Connection count
- Compute size
- Query performance

---

**Last Updated:** January 14, 2026  
**Version:** 3.1.0
