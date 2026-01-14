"""
Aurora OSI v3 - Database Layer
PostgreSQL integration via psycopg2
"""

import os
from typing import Optional, List, Dict, Tuple
import psycopg2
from psycopg2 import pool, sql
import json
from datetime import datetime
from contextlib import contextmanager


class DatabaseManager:
    """Manages PostgreSQL connections for Aurora OSI"""

    def __init__(self):
        self.connection_string = os.getenv(
            "DATABASE_URL",
            "postgresql://user:password@localhost:5432/aurora_osi"
        )
        self.connection_pool: Optional[pool.SimpleConnectionPool] = None
        self._init_pool()
        self._init_schema()

    def _init_pool(self):
        """Initialize connection pool"""
        try:
            self.connection_pool = pool.SimpleConnectionPool(1, 20, self.connection_string)
            print("✓ Database pool initialized")
        except Exception as e:
            print(f"✗ Database pool error: {e}")
            raise

    @contextmanager
    def get_connection(self):
        """Context manager for database connections"""
        conn = self.connection_pool.getconn()
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            self.connection_pool.putconn(conn)

    def _init_schema(self):
        """Initialize database schema"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Mineral detections table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS mineral_detections (
                    id SERIAL PRIMARY KEY,
                    mineral_name VARCHAR(100),
                    latitude FLOAT,
                    longitude FLOAT,
                    confidence_score FLOAT,
                    confidence_tier VARCHAR(20),
                    depth_estimate_m FLOAT,
                    sensor_type VARCHAR(50),
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    spectral_match_score FLOAT,
                    processing_time_ms INT,
                    raw_spectrum TEXT,  -- JSON
                    geometry POINT  -- PostGIS
                )
            """)
            
            # Digital twin voxels table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS digital_twin_voxels (
                    id SERIAL PRIMARY KEY,
                    region VARCHAR(200),
                    voxel_x INT,
                    voxel_y INT,
                    voxel_z INT,
                    rock_type_distribution TEXT,  -- JSON
                    density_kg_m3 FLOAT,
                    mineral_assemblage TEXT,  -- JSON
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Satellite tasks table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS satellite_tasks (
                    id SERIAL PRIMARY KEY,
                    task_id VARCHAR(100) UNIQUE,
                    latitude FLOAT,
                    longitude FLOAT,
                    sensor_type VARCHAR(50),
                    status VARCHAR(50),
                    requested_resolution_m FLOAT,
                    cost_usd FLOAT,
                    acquisition_date TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    data_url TEXT
                )
            """)
            
            # Seismic digital twin table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS seismic_twin (
                    id SERIAL PRIMARY KEY,
                    survey_id VARCHAR(100) UNIQUE,
                    inline_count INT,
                    crossline_count INT,
                    depth_samples INT,
                    depth_min_m INT,
                    depth_max_m INT,
                    voxel_size_m INT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Seismic voxel data table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS seismic_voxels (
                    id SERIAL PRIMARY KEY,
                    survey_id VARCHAR(100),
                    inline INT,
                    crossline INT,
                    depth_m INT,
                    amplitude FLOAT,
                    impedance FLOAT,
                    porosity FLOAT,
                    saturation FLOAT,
                    fluid_type VARCHAR(50)
                )
            """)
            
            # Physics residuals table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS physics_residuals (
                    id SERIAL PRIMARY KEY,
                    latitude FLOAT,
                    longitude FLOAT,
                    depth_m INT,
                    residual_value FLOAT,
                    physics_law VARCHAR(100),
                    severity VARCHAR(20),
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.commit()
            print("✓ Database schema initialized")

    def insert_detection(self, detection: Dict) -> int:
        """Insert mineral detection result"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO mineral_detections 
                (mineral_name, latitude, longitude, confidence_score, confidence_tier, 
                 depth_estimate_m, sensor_type, spectral_match_score, processing_time_ms,
                 raw_spectrum)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (
                detection.get("mineral"),
                detection.get("latitude"),
                detection.get("longitude"),
                detection.get("confidence_score"),
                detection.get("confidence_tier"),
                detection.get("depth_estimate_m"),
                detection.get("sensor"),
                detection.get("spectral_match_score"),
                detection.get("processing_time_ms"),
                json.dumps(detection.get("spectrum", []))
            ))
            return cursor.fetchone()[0]

    def insert_voxel(self, region: str, voxel_data: Dict) -> int:
        """Insert digital twin voxel"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO digital_twin_voxels
                (region, voxel_x, voxel_y, voxel_z, rock_type_distribution, 
                 density_kg_m3, mineral_assemblage)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (
                region,
                voxel_data.get("x"),
                voxel_data.get("y"),
                voxel_data.get("z"),
                json.dumps(voxel_data.get("rock_types", {})),
                voxel_data.get("density"),
                json.dumps(voxel_data.get("minerals", {}))
            ))
            return cursor.fetchone()[0]

    def get_detections_in_area(self, lat_min: float, lat_max: float, 
                               lon_min: float, lon_max: float) -> List[Dict]:
        """Get all detections in geographic area"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT mineral_name, latitude, longitude, confidence_score, 
                       confidence_tier, depth_estimate_m, timestamp
                FROM mineral_detections
                WHERE latitude BETWEEN %s AND %s
                  AND longitude BETWEEN %s AND %s
                ORDER BY timestamp DESC
            """, (lat_min, lat_max, lon_min, lon_max))
            
            columns = ["mineral", "latitude", "longitude", "confidence", "tier", "depth", "time"]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]

    def get_voxel_data(self, region: str, x: int, y: int, z: int) -> Optional[Dict]:
        """Get specific voxel data"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT rock_type_distribution, density_kg_m3, mineral_assemblage
                FROM digital_twin_voxels
                WHERE region = %s AND voxel_x = %s AND voxel_y = %s AND voxel_z = %s
                LIMIT 1
            """, (region, x, y, z))
            
            row = cursor.fetchone()
            if row:
                return {
                    "rocks": json.loads(row[0]),
                    "density": row[1],
                    "minerals": json.loads(row[2])
                }
            return None

    def create_satellite_task(self, task_data: Dict) -> str:
        """Create new satellite tasking request"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            task_id = f"SAT_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            cursor.execute("""
                INSERT INTO satellite_tasks
                (task_id, latitude, longitude, sensor_type, status, requested_resolution_m, cost_usd)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (
                task_id,
                task_data.get("latitude"),
                task_data.get("longitude"),
                task_data.get("sensor_type"),
                "pending",
                task_data.get("resolution_m"),
                task_data.get("estimated_cost", 0.0)
            ))
            return task_id

    def get_physics_residuals(self, region: str, severity: str = "high") -> List[Dict]:
        """Get physics residuals in region"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT latitude, longitude, depth_m, residual_value, physics_law, severity
                FROM physics_residuals
                WHERE severity = %s
                ORDER BY residual_value DESC
            """, (severity,))
            
            columns = ["lat", "lon", "depth", "residual", "law", "severity"]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]

    def close(self):
        """Close connection pool"""
        if self.connection_pool:
            self.connection_pool.closeall()


# Global database instance
db = DatabaseManager()
