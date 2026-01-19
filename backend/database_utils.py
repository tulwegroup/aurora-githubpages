"""
Aurora OSI v3 - Database Utilities
High-level functions for scan persistence, retrieval, and updates
"""

import json
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any
import logging
from .database_manager import db_manager

logger = logging.getLogger(__name__)


class ScanDatabase:
    """Database operations for scans, results, and visualizations"""

    @staticmethod
    def create_scan(scan_name: str, latitude: float, longitude: float, user_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Create a new scan record.
        Returns: {id, success, error}
        """
        try:
            scan_id = str(uuid.uuid4())
            
            with db_manager.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO scans (id, scan_name, latitude, longitude, overall_status, user_id, started_at)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """, (scan_id, scan_name, latitude, longitude, 'running', user_id, datetime.utcnow()))
                    
            logger.info(f"✓ Created scan {scan_id} at ({latitude}, {longitude})")
            return {"id": scan_id, "success": True}
            
        except Exception as e:
            logger.error(f"✗ Failed to create scan: {str(e)}")
            return {"error": str(e), "code": "SCAN_CREATE_ERROR"}

    @staticmethod
    def create_scan_results(scan_id: str) -> Dict[str, Any]:
        """
        Create scan results record for detailed outputs.
        Returns: {id, success, error}
        """
        try:
            result_id = str(uuid.uuid4())
            
            with db_manager.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO scan_results (id, scan_id, created_at, updated_at)
                        VALUES (%s, %s, %s, %s)
                    """, (result_id, scan_id, datetime.utcnow(), datetime.utcnow()))
                    
            logger.info(f"✓ Created scan results {result_id} for scan {scan_id}")
            return {"id": result_id, "success": True}
            
        except Exception as e:
            logger.error(f"✗ Failed to create scan results: {str(e)}")
            return {"error": str(e), "code": "RESULTS_CREATE_ERROR"}

    @staticmethod
    def update_scan_status(scan_id: str, status: str, error_msg: Optional[str] = None, error_code: Optional[str] = None) -> Dict[str, Any]:
        """
        Update scan overall status and optional error information.
        status: 'pending', 'running', 'completed', 'failed'
        """
        try:
            with db_manager.get_connection() as conn:
                with conn.cursor() as cur:
                    if status == 'completed':
                        cur.execute("""
                            UPDATE scans 
                            SET overall_status = %s, completed_at = %s, duration_seconds = EXTRACT(EPOCH FROM (NOW() - started_at))::INTEGER
                            WHERE id = %s
                        """, (status, datetime.utcnow(), scan_id))
                    else:
                        cur.execute("""
                            UPDATE scans 
                            SET overall_status = %s, error_message = %s, error_code = %s
                            WHERE id = %s
                        """, (status, error_msg, error_code, scan_id))
                    
            logger.info(f"✓ Updated scan {scan_id} status to {status}")
            return {"success": True}
            
        except Exception as e:
            logger.error(f"✗ Failed to update scan status: {str(e)}")
            return {"error": str(e), "code": "STATUS_UPDATE_ERROR"}

    @staticmethod
    def update_step_result(scan_id: str, step: str, output_json: str, status: str = 'completed', error_msg: Optional[str] = None) -> Dict[str, Any]:
        """
        Update a specific analysis step result (PINN, USHE, TMAL).
        step: 'pinn', 'ushe', 'tmal'
        """
        try:
            with db_manager.get_connection() as conn:
                with conn.cursor() as cur:
                    if status == 'completed':
                        cur.execute(f"""
                            UPDATE scan_results 
                            SET {step}_output_json = %s, {step}_status = %s, {step}_completed_at = %s, updated_at = %s
                            WHERE scan_id = %s
                        """, (output_json, status, datetime.utcnow(), datetime.utcnow(), scan_id))
                    else:
                        cur.execute(f"""
                            UPDATE scan_results 
                            SET {step}_status = %s, {step}_error = %s, updated_at = %s
                            WHERE scan_id = %s
                        """, (status, error_msg, datetime.utcnow(), scan_id))
                    
            logger.info(f"✓ Updated {step} results for scan {scan_id}")
            return {"success": True}
            
        except Exception as e:
            logger.error(f"✗ Failed to update step result: {str(e)}")
            return {"error": str(e), "code": "STEP_UPDATE_ERROR"}

    @staticmethod
    def create_visualizations(scan_id: str) -> Dict[str, Any]:
        """
        Create visualization record for 2D and 3D outputs.
        Returns: {id, success, error}
        """
        try:
            viz_id = str(uuid.uuid4())
            
            with db_manager.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO visualizations (id, scan_id, created_at, updated_at)
                        VALUES (%s, %s, %s, %s)
                    """, (viz_id, scan_id, datetime.utcnow(), datetime.utcnow()))
                    
            logger.info(f"✓ Created visualization {viz_id} for scan {scan_id}")
            return {"id": viz_id, "success": True}
            
        except Exception as e:
            logger.error(f"✗ Failed to create visualization: {str(e)}")
            return {"error": str(e), "code": "VIZ_CREATE_ERROR"}

    @staticmethod
    def update_visualization(scan_id: str, viz_2d: Optional[str] = None, viz_3d: Optional[str] = None) -> Dict[str, Any]:
        """
        Update 2D and/or 3D visualization data.
        viz_2d, viz_3d: JSON strings
        """
        try:
            with db_manager.get_connection() as conn:
                with conn.cursor() as cur:
                    if viz_2d and viz_3d:
                        cur.execute("""
                            UPDATE visualizations 
                            SET visualization_2d_data = %s, visualization_2d_generated_at = %s,
                                visualization_3d_data = %s, visualization_3d_generated_at = %s, updated_at = %s
                            WHERE scan_id = %s
                        """, (viz_2d, datetime.utcnow(), viz_3d, datetime.utcnow(), datetime.utcnow(), scan_id))
                    elif viz_2d:
                        cur.execute("""
                            UPDATE visualizations 
                            SET visualization_2d_data = %s, visualization_2d_generated_at = %s, updated_at = %s
                            WHERE scan_id = %s
                        """, (viz_2d, datetime.utcnow(), datetime.utcnow(), scan_id))
                    elif viz_3d:
                        cur.execute("""
                            UPDATE visualizations 
                            SET visualization_3d_data = %s, visualization_3d_generated_at = %s, updated_at = %s
                            WHERE scan_id = %s
                        """, (viz_3d, datetime.utcnow(), datetime.utcnow(), scan_id))
                    
            logger.info(f"✓ Updated visualization for scan {scan_id}")
            return {"success": True}
            
        except Exception as e:
            logger.error(f"✗ Failed to update visualization: {str(e)}")
            return {"error": str(e), "code": "VIZ_UPDATE_ERROR"}

    @staticmethod
    def get_all_scans(limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
        """Retrieve all scans with pagination"""
        try:
            with db_manager.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT id, scan_name, latitude, longitude, timestamp, overall_status, 
                               started_at, completed_at, duration_seconds
                        FROM scans
                        ORDER BY timestamp DESC
                        LIMIT %s OFFSET %s
                    """, (limit, offset))
                    
                    rows = cur.fetchall()
                    scans = []
                    for row in rows:
                        scans.append({
                            "id": row[0],
                            "name": row[1],
                            "latitude": row[2],
                            "longitude": row[3],
                            "timestamp": row[4].isoformat() if row[4] else None,
                            "status": row[5],
                            "started_at": row[6].isoformat() if row[6] else None,
                            "completed_at": row[7].isoformat() if row[7] else None,
                            "duration_seconds": row[8]
                        })
                    
            logger.info(f"✓ Retrieved {len(scans)} scans")
            return scans
            
        except Exception as e:
            logger.error(f"✗ Failed to retrieve scans: {str(e)}")
            return []

    @staticmethod
    def get_scan_details(scan_id: str) -> Dict[str, Any]:
        """Retrieve complete scan details including results and visualizations"""
        try:
            with db_manager.get_connection() as conn:
                with conn.cursor() as cur:
                    # Get scan info
                    cur.execute("""
                        SELECT id, scan_name, latitude, longitude, timestamp, overall_status, 
                               error_message, error_code, duration_seconds, cloud_coverage
                        FROM scans WHERE id = %s
                    """, (scan_id,))
                    
                    scan_row = cur.fetchone()
                    if not scan_row:
                        return {"error": "Scan not found", "code": "NOT_FOUND"}
                    
                    # Get scan results
                    cur.execute("""
                        SELECT pinn_output_json, pinn_status, ushe_output_json, ushe_status, 
                               tmal_output_json, tmal_status
                        FROM scan_results WHERE scan_id = %s
                    """, (scan_id,))
                    
                    result_row = cur.fetchone()
                    
                    # Get visualizations
                    cur.execute("""
                        SELECT visualization_2d_data, visualization_3d_data
                        FROM visualizations WHERE scan_id = %s
                    """, (scan_id,))
                    
                    viz_row = cur.fetchone()
                    
                    scan_detail = {
                        "id": scan_row[0],
                        "name": scan_row[1],
                        "latitude": scan_row[2],
                        "longitude": scan_row[3],
                        "timestamp": scan_row[4].isoformat() if scan_row[4] else None,
                        "status": scan_row[5],
                        "error": scan_row[6],
                        "error_code": scan_row[7],
                        "duration_seconds": scan_row[8],
                        "cloud_coverage": scan_row[9],
                        "results": {}
                    }
                    
                    if result_row:
                        scan_detail["results"] = {
                            "pinn": {
                                "output": json.loads(result_row[0]) if result_row[0] else None,
                                "status": result_row[1]
                            },
                            "ushe": {
                                "output": json.loads(result_row[2]) if result_row[2] else None,
                                "status": result_row[3]
                            },
                            "tmal": {
                                "output": json.loads(result_row[4]) if result_row[4] else None,
                                "status": result_row[5]
                            }
                        }
                    
                    if viz_row:
                        scan_detail["visualizations"] = {
                            "viz_2d": json.loads(viz_row[0]) if viz_row[0] else None,
                            "viz_3d": json.loads(viz_row[1]) if viz_row[1] else None
                        }
                    
                    logger.info(f"✓ Retrieved details for scan {scan_id}")
                    return scan_detail
                    
        except Exception as e:
            logger.error(f"✗ Failed to retrieve scan details: {str(e)}")
            return {"error": str(e), "code": "QUERY_ERROR"}


# Module-level convenience instance
scan_db = ScanDatabase()
