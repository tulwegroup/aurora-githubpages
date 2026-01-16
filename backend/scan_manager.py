"""
Aurora OSI v3 - Scan Manager
Manages all scanning operations including point, radius, and grid scans
"""

import asyncio
import logging
import uuid
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from sqlalchemy import text
from enum import Enum

from .models import (
    ScanRequest,
    ScanResult,
    ScanMetadata,
    PixelDetection,
    ScanStatus,
    ScanType,
    ScanResolution,
    DetectionTier,
)
from .database_manager import get_db

logger = logging.getLogger(__name__)


class ScanManager:
    """Manages scanning operations and persistence"""

    def __init__(self):
        self.active_scans: Dict[str, dict] = {}

    async def create_scan(self, request: ScanRequest) -> str:
        """
        Create a new scan and queue it for processing
        Returns: scan_id
        """
        scan_id = f"SCAN_{uuid.uuid4().hex[:12].upper()}"
        
        # Determine location description
        if request.country:
            location_desc = f"{request.country}"
            if request.region:
                location_desc += f" - {request.region}"
        else:
            location_desc = f"{request.latitude:.4f}, {request.longitude:.4f}"
        
        # Calculate area
        area_km2 = self._calculate_area(request)
        
        db = get_db()
        try:
            # Insert scan record
            query = """
            INSERT INTO scans (
                scan_id, scan_type, status, latitude, longitude,
                country, region, radius_km, grid_spacing_m, area_km2,
                minerals, resolution, sensor, max_cloud_cover_percent,
                date_start, date_end, created_at
            ) VALUES (
                :scan_id, :scan_type, :status, :latitude, :longitude,
                :country, :region, :radius_km, :grid_spacing_m, :area_km2,
                :minerals, :resolution, :sensor, :max_cloud_cover_percent,
                :date_start, :date_end, NOW()
            )
            """
            
            db.execute(text(query), {
                "scan_id": scan_id,
                "scan_type": request.scan_type.value,
                "status": ScanStatus.PENDING.value,
                "latitude": request.latitude,
                "longitude": request.longitude,
                "country": request.country,
                "region": request.region,
                "radius_km": request.radius_km or 0,
                "grid_spacing_m": request.grid_spacing_m or 30,
                "area_km2": area_km2,
                "minerals": request.minerals,
                "resolution": request.resolution.value,
                "sensor": request.sensor,
                "max_cloud_cover_percent": request.max_cloud_cover_percent,
                "date_start": request.date_start,
                "date_end": request.date_end,
            })
            
            # Create scan queue entry
            queue_query = """
            INSERT INTO scan_queue (scan_id, priority, status)
            VALUES (:scan_id, 0, :status)
            """
            db.execute(text(queue_query), {
                "scan_id": scan_id,
                "status": ScanStatus.PENDING.value,
            })
            
            db.commit()
            logger.info(f"✓ Scan created: {scan_id} - {request.scan_type.value} scan for {location_desc}")
            
            return scan_id
            
        except Exception as e:
            db.rollback()
            logger.error(f"✗ Failed to create scan: {str(e)}")
            raise

    async def get_scan(self, scan_id: str) -> Optional[Dict]:
        """Retrieve scan metadata and results"""
        db = get_db()
        
        try:
            # Get scan metadata
            metadata_query = """
            SELECT 
                scan_id, scan_type, status, latitude, longitude,
                country, region, radius_km, area_km2, minerals,
                resolution, sensor, created_at, started_at, completed_at,
                pixel_count_total, detections_found, confidence_average
            FROM scans
            WHERE scan_id = :scan_id
            """
            
            result = db.execute(text(metadata_query), {"scan_id": scan_id}).fetchone()
            
            if not result:
                return None
            
            # Get summary
            summary_query = """
            SELECT 
                total_detections, detection_rate_percent,
                mineral_breakdown, scan_duration_minutes
            FROM scan_summaries
            WHERE scan_id = :scan_id
            """
            
            summary = db.execute(text(summary_query), {"scan_id": scan_id}).fetchone()
            
            # Get results if completed
            results = None
            if result[2] == ScanStatus.COMPLETED.value:  # status
                results_query = """
                SELECT 
                    latitude, longitude, mineral, confidence_score,
                    confidence_tier, spectral_match_score, detected_at
                FROM scan_results
                WHERE scan_id = :scan_id
                ORDER BY confidence_score DESC
                LIMIT 10000
                """
                
                results_data = db.execute(text(results_query), {"scan_id": scan_id}).fetchall()
                
                pixel_detections = [
                    PixelDetection(
                        latitude=float(r[0]),
                        longitude=float(r[1]),
                        mineral=r[2],
                        confidence_score=float(r[3]),
                        confidence_tier=DetectionTier(r[4]) if r[4] else DetectionTier.TIER_0,
                        spectral_match_score=float(r[5]),
                        timestamp=r[6]
                    )
                    for r in results_data
                ]
                
                if pixel_detections:
                    results = ScanResult(
                        pixel_detections=pixel_detections,
                        total_pixels_scanned=result[14],  # pixel_count_total
                        total_pixels_with_detection=len(pixel_detections),
                        detection_rate_percent=(len(pixel_detections) / max(result[14], 1)) * 100,
                        area_km2=result[7],
                        scan_duration_minutes=summary[3] if summary else 0,
                    )
            
            metadata = ScanMetadata(
                scan_id=result[0],
                scan_type=ScanType(result[1]),
                status=ScanStatus(result[2]),
                location_description=f"{result[4] or 'Coordinate'}: {result[5]}, {result[6]}" if result[5] else result[4] or "Unknown",
                minerals_requested=result[9] or [],
                scan_area_km2=result[7],
                pixel_count_total=result[14],
                detections_found=result[15],
                created_at=result[12],
                started_at=result[13],
                completed_at=result[14],
                confidence_average=result[15],
            )
            
            return {
                "scan_id": scan_id,
                "metadata": metadata,
                "results": results,
                "summary": summary[1] if summary else None,
            }
            
        except Exception as e:
            logger.error(f"✗ Failed to retrieve scan {scan_id}: {str(e)}")
            return None

    async def list_scans(self, limit: int = 100, offset: int = 0, status: Optional[str] = None) -> List[Dict]:
        """List all scans with optional filtering"""
        db = get_db()
        
        try:
            query = """
            SELECT 
                scan_id, scan_type, status, latitude, longitude,
                country, region, area_km2, minerals,
                created_at, completed_at, detections_found
            FROM scans
            """
            
            params = {}
            if status:
                query += " WHERE status = :status"
                params["status"] = status
            
            query += " ORDER BY created_at DESC LIMIT :limit OFFSET :offset"
            params["limit"] = limit
            params["offset"] = offset
            
            results = db.execute(text(query), params).fetchall()
            
            return [
                {
                    "scan_id": r[0],
                    "scan_type": r[1],
                    "status": r[2],
                    "location": f"{r[4] or r[5]} {r[6] or ''}".strip(),
                    "area_km2": r[7],
                    "minerals": r[8] or [],
                    "created_at": r[9],
                    "completed_at": r[10],
                    "detections_found": r[11],
                }
                for r in results
            ]
            
        except Exception as e:
            logger.error(f"✗ Failed to list scans: {str(e)}")
            return []

    async def delete_scan(self, scan_id: str) -> bool:
        """Delete a scan and its results"""
        db = get_db()
        
        try:
            # Delete results first (cascade may not work)
            db.execute(text("DELETE FROM scan_results WHERE scan_id = :scan_id"), {"scan_id": scan_id})
            db.execute(text("DELETE FROM scan_summaries WHERE scan_id = :scan_id"), {"scan_id": scan_id})
            db.execute(text("DELETE FROM scan_queue WHERE scan_id = :scan_id"), {"scan_id": scan_id})
            db.execute(text("DELETE FROM scans WHERE scan_id = :scan_id"), {"scan_id": scan_id})
            
            db.commit()
            logger.info(f"✓ Scan deleted: {scan_id}")
            return True
            
        except Exception as e:
            db.rollback()
            logger.error(f"✗ Failed to delete scan {scan_id}: {str(e)}")
            return False

    def _calculate_area(self, request: ScanRequest) -> float:
        """Calculate scan area in km²"""
        if request.scan_type == ScanType.POINT:
            return 0.0001  # Very small area for point
        elif request.scan_type == ScanType.RADIUS:
            # Area of circle: π * r²
            radius_m = (request.radius_km or 0) * 1000
            return 3.14159 * (radius_m ** 2) / (1000000)  # Convert to km²
        elif request.scan_type == ScanType.GRID:
            # Grid area depends on grid spacing and predefined bounds
            # Default: 100km x 100km
            return 10000.0
        return 0.0

    async def store_detection(self, scan_id: str, detection: PixelDetection, satellite_date: Optional[str] = None):
        """Store a pixel detection result"""
        db = get_db()
        
        try:
            query = """
            INSERT INTO scan_results (
                scan_id, latitude, longitude, mineral,
                confidence_score, confidence_tier, spectral_match_score,
                detected_at, satellite_capture_date, spectral_features
            ) VALUES (
                :scan_id, :latitude, :longitude, :mineral,
                :confidence_score, :confidence_tier, :spectral_match_score,
                :detected_at, :satellite_date, :spectral_features
            )
            """
            
            db.execute(text(query), {
                "scan_id": scan_id,
                "latitude": detection.latitude,
                "longitude": detection.longitude,
                "mineral": detection.mineral,
                "confidence_score": detection.confidence_score,
                "confidence_tier": detection.confidence_tier.value,
                "spectral_match_score": detection.spectral_match_score,
                "detected_at": detection.timestamp,
                "satellite_date": satellite_date,
                "spectral_features": str(detection.wavelength_features),
            })
            
            db.commit()
            
        except Exception as e:
            db.rollback()
            logger.error(f"✗ Failed to store detection: {str(e)}")

    async def update_scan_status(self, scan_id: str, status: ScanStatus, error_message: Optional[str] = None):
        """Update scan status"""
        db = get_db()
        
        try:
            if status == ScanStatus.RUNNING:
                query = """
                UPDATE scans 
                SET status = :status, started_at = NOW()
                WHERE scan_id = :scan_id
                """
            elif status == ScanStatus.COMPLETED:
                query = """
                UPDATE scans 
                SET status = :status, completed_at = NOW()
                WHERE scan_id = :scan_id
                """
            else:
                query = """
                UPDATE scans 
                SET status = :status
                WHERE scan_id = :scan_id
                """
            
            if error_message and status == ScanStatus.FAILED:
                query = query.replace("WHERE", ", error_message = :error_message WHERE")
            
            params = {"status": status.value, "scan_id": scan_id}
            if error_message:
                params["error_message"] = error_message
            
            db.execute(text(query), params)
            db.commit()
            
        except Exception as e:
            db.rollback()
            logger.error(f"✗ Failed to update scan status: {str(e)}")


# Global scan manager instance
scan_manager = ScanManager()
