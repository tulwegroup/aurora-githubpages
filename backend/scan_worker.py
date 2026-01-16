"""
Aurora OSI v3 - Background Scan Worker
Processes scans asynchronously, even when app is closed
Uses APScheduler for background task management
"""

import asyncio
import logging
from typing import Optional
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

from .scan_manager import scan_manager, ScanStatus
from .pixel_scanner import pixel_scanner
from .database_manager import get_db
from sqlalchemy import text

logger = logging.getLogger(__name__)

# Global scheduler instance
scan_scheduler = None


class ScanWorker:
    """Background worker for processing scans"""

    def __init__(self, check_interval_seconds: int = 30):
        self.check_interval = check_interval_seconds
        self.is_running = False

    async def process_pending_scans(self):
        """Check queue and process pending scans"""
        if self.is_running:
            logger.debug("Scan worker already running, skipping")
            return

        self.is_running = True

        try:
            db = get_db()

            # Get pending scans
            query = """
            SELECT s.scan_id, s.scan_type, s.latitude, s.longitude,
                   s.radius_km, s.grid_spacing_m, s.minerals, s.resolution,
                   s.sensor, s.date_start, s.date_end, s.max_cloud_cover_percent
            FROM scans s
            JOIN scan_queue q ON s.scan_id = q.scan_id
            WHERE s.status = :status
            LIMIT 10
            """

            results = db.execute(
                text(query), {"status": ScanStatus.PENDING.value}
            ).fetchall()

            if not results:
                logger.debug("No pending scans")
                return

            logger.info(f"📋 Processing {len(results)} pending scans")

            for result in results:
                scan_id = result[0]
                try:
                    await self._process_scan(
                        scan_id=scan_id,
                        scan_type=result[1],
                        latitude=result[2],
                        longitude=result[3],
                        radius_km=result[4],
                        grid_spacing_m=result[5],
                        minerals=result[6],
                        resolution=result[7],
                        sensor=result[8],
                        date_start=result[9],
                        date_end=result[10],
                        max_cloud_cover=result[11],
                    )
                except Exception as e:
                    logger.error(f"✗ Error processing scan {scan_id}: {str(e)}")
                    await scan_manager.update_scan_status(
                        scan_id, ScanStatus.FAILED, str(e)
                    )

        except Exception as e:
            logger.error(f"✗ Scan worker error: {str(e)}")
        finally:
            self.is_running = False

    async def _process_scan(
        self,
        scan_id: str,
        scan_type: str,
        latitude: float,
        longitude: float,
        radius_km: float,
        grid_spacing_m: float,
        minerals: list,
        resolution: str,
        sensor: str,
        date_start: Optional[str],
        date_end: Optional[str],
        max_cloud_cover: float,
    ):
        """Process a single scan"""
        logger.info(f"🚀 Starting scan: {scan_id} ({scan_type})")

        # Mark as running
        await scan_manager.update_scan_status(scan_id, ScanStatus.RUNNING)

        start_time = datetime.now()
        detections = []

        try:
            # Perform appropriate scan type
            if scan_type == "point":
                detections = await pixel_scanner.scan_point(
                    latitude=latitude,
                    longitude=longitude,
                    minerals=minerals,
                    sensor=sensor,
                    date_start=date_start,
                    date_end=date_end,
                    max_cloud_cover=max_cloud_cover,
                )

            elif scan_type == "radius":
                detections = await pixel_scanner.scan_radius(
                    latitude=latitude,
                    longitude=longitude,
                    radius_km=radius_km,
                    minerals=minerals,
                    resolution=resolution,
                    sensor=sensor,
                    date_start=date_start,
                    date_end=date_end,
                    max_cloud_cover=max_cloud_cover,
                )

            elif scan_type == "grid":
                detections = await pixel_scanner.scan_grid(
                    latitude=latitude,
                    longitude=longitude,
                    grid_spacing_m=grid_spacing_m,
                    minerals=minerals,
                    sensor=sensor,
                    date_start=date_start,
                    date_end=date_end,
                )

            # Store all detections
            for detection in detections:
                await scan_manager.store_detection(
                    scan_id=scan_id,
                    detection=detection,
                    satellite_date=date_start,
                )

            # Update scan with results
            duration = (datetime.now() - start_time).total_seconds() / 60  # minutes
            await self._update_scan_results(
                scan_id=scan_id,
                total_pixels=len(detections) * 10,  # Estimate
                detections=len(detections),
                duration=duration,
                minerals=minerals,
            )

            # Mark as completed
            await scan_manager.update_scan_status(scan_id, ScanStatus.COMPLETED)
            logger.info(
                f"✅ Scan completed: {scan_id} - {len(detections)} detections in {duration:.1f} min"
            )

        except Exception as e:
            logger.error(f"✗ Scan failed: {scan_id} - {str(e)}")
            await scan_manager.update_scan_status(
                scan_id, ScanStatus.FAILED, str(e)
            )
            raise

    async def _update_scan_results(
        self,
        scan_id: str,
        total_pixels: int,
        detections: int,
        duration: float,
        minerals: list,
    ):
        """Update scan results in database"""
        db = get_db()

        try:
            # Update scan table
            update_query = """
            UPDATE scans
            SET pixel_count_total = :total_pixels,
                detections_found = :detections,
                confidence_average = CASE 
                    WHEN :detections > 0 THEN 0.75
                    ELSE 0.0
                END
            WHERE scan_id = :scan_id
            """

            db.execute(
                text(update_query),
                {
                    "scan_id": scan_id,
                    "total_pixels": total_pixels,
                    "detections": detections,
                },
            )

            # Create summary
            if detections > 0:
                detection_rate = (detections / max(total_pixels, 1)) * 100

                summary_query = """
                INSERT INTO scan_summaries 
                    (scan_id, total_detections, detection_rate_percent,
                     scan_duration_minutes, mineral_breakdown)
                VALUES (:scan_id, :detections, :rate, :duration,
                        :breakdown)
                """

                breakdown = {mineral: detections // max(len(minerals), 1) for mineral in minerals}

                db.execute(
                    text(summary_query),
                    {
                        "scan_id": scan_id,
                        "detections": detections,
                        "rate": detection_rate,
                        "duration": duration,
                        "breakdown": str(breakdown),
                    },
                )

            db.commit()

        except Exception as e:
            db.rollback()
            logger.error(f"✗ Failed to update scan results: {str(e)}")


# Global worker instance
scan_worker = ScanWorker()


def initialize_scan_scheduler():
    """Initialize background scan scheduler"""
    global scan_scheduler

    if scan_scheduler is None:
        scan_scheduler = BackgroundScheduler()

        # Add job to process pending scans every 30 seconds
        scan_scheduler.add_job(
            func=lambda: asyncio.run(scan_worker.process_pending_scans()),
            trigger=IntervalTrigger(seconds=30),
            id="process_pending_scans",
            name="Process Pending Scans",
            replace_existing=True,
        )

        scan_scheduler.start()
        logger.info("✓ Scan scheduler initialized - processing every 30 seconds")


def shutdown_scan_scheduler():
    """Shutdown background scan scheduler"""
    global scan_scheduler

    if scan_scheduler:
        scan_scheduler.shutdown(wait=True)
        scan_scheduler = None
        logger.info("✓ Scan scheduler shutdown")
