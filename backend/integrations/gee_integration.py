"""
Google Earth Engine Integration for Aurora OSI
Real Sentinel-2 satellite data fetching for subsurface analysis
"""

import ee
import logging
import os
from typing import Dict, Optional, List, Any
from datetime import datetime, timedelta
import json

logger = logging.getLogger(__name__)


class GEEIntegration:
    """Manages Google Earth Engine authentication and data fetching"""
    
    _initialized = False
    _credentials_path = None
    
    @classmethod
    def initialize(cls, credentials_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Initialize Google Earth Engine with service account credentials.
        
        Args:
            credentials_path: Path to GEE service account JSON file
                            If None, uses environment variable: GEE_CREDENTIALS
        
        Returns:
            {success: bool, message: str, error: str}
        """
        try:
            if cls._initialized:
                logger.info("✓ GEE already initialized")
                return {"success": True, "message": "GEE already initialized"}
            
            # Get credentials path
            creds_path = credentials_path or os.getenv("GEE_CREDENTIALS")
            
            if not creds_path:
                logger.error("❌ No GEE credentials provided")
                return {
                    "success": False,
                    "error": "GEE_CREDENTIALS environment variable not set",
                    "code": "NO_CREDENTIALS"
                }
            
            # Authenticate with service account
            ee.Authenticate(credentials_path=creds_path)
            ee.Initialize()
            
            cls._initialized = True
            cls._credentials_path = creds_path
            
            logger.info("✓ Google Earth Engine initialized successfully")
            return {
                "success": True,
                "message": "Google Earth Engine authenticated"
            }
            
        except Exception as e:
            logger.error(f"❌ GEE initialization error: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "code": "INIT_ERROR"
            }
    
    @classmethod
    def fetch_sentinel2_data(
        cls,
        latitude: float,
        longitude: float,
        radius_m: int = 5000,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        max_cloud_cover: float = 0.2
    ) -> Dict[str, Any]:
        """
        Fetch Sentinel-2 satellite data for a given location and time range.
        
        Args:
            latitude: Target latitude
            longitude: Target longitude
            radius_m: Search radius in meters (default: 5km)
            start_date: ISO format date string (default: 30 days ago)
            end_date: ISO format date string (default: today)
            max_cloud_cover: Maximum acceptable cloud cover (0-1, default: 20%)
        
        Returns:
            {
                success: bool,
                data: {
                    bands: {...},
                    metadata: {...},
                    url: str (GEE image ID)
                },
                error: str (if failed)
            }
        """
        try:
            if not cls._initialized:
                init_result = cls.initialize()
                if not init_result.get("success"):
                    return init_result
            
            logger.info(f"🛰️ Fetching Sentinel-2 data for ({latitude}, {longitude})")
            
            # Default date range: last 30 days
            if not end_date:
                end_date = datetime.now().isoformat()
            if not start_date:
                start_date = (datetime.now() - timedelta(days=30)).isoformat()
            
            # Create point geometry
            point = ee.Geometry.Point([longitude, latitude])
            roi = point.buffer(radius_m)
            
            # Load Sentinel-2 collection
            s2_collection = ee.ImageCollection("COPERNICUS/S2_SR") \
                .filterBounds(roi) \
                .filterDate(start_date, end_date) \
                .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", max_cloud_cover * 100)) \
                .sort("CLOUDY_PIXEL_PERCENTAGE")
            
            # Check if data exists
            count = s2_collection.size().getInfo()
            if count == 0:
                logger.warning(f"⚠️ No Sentinel-2 data available for ({latitude}, {longitude})")
                return {
                    "success": False,
                    "error": "No Sentinel-2 images available for this location and date range",
                    "code": "NO_DATA_AVAILABLE"
                }
            
            # Get the best (least cloudy) image
            best_image = s2_collection.first()
            
            # Extract key bands for analysis
            # B4: Red (665nm) - Mineral absorption
            # B3: Green (560nm) - Vegetation reference
            # B2: Blue (490nm) - Water/atmospheric
            # B11: SWIR (1610nm) - Mineral diagnostic
            # B12: SWIR (2190nm) - Geological features
            
            analysis_image = best_image.select(['B2', 'B3', 'B4', 'B8', 'B11', 'B12']) \
                .float() \
                .clip(roi)
            
            # Get band statistics
            stats = analysis_image.reduceRegion(
                reducer=ee.Reducer.mean(),
                geometry=roi,
                scale=10,
                maxPixels=1e6
            ).getInfo()
            
            # Get metadata
            image_props = best_image.toDictionary().getInfo()
            
            logger.info(f"✓ Retrieved Sentinel-2 data: {image_props.get('PRODUCT_ID', 'unknown')}")
            
            return {
                "success": True,
                "data": {
                    "bands": stats,
                    "metadata": {
                        "product_id": image_props.get("PRODUCT_ID"),
                        "acquisition_date": image_props.get("SENSING_TIME"),
                        "cloud_coverage": image_props.get("CLOUDY_PIXEL_PERCENTAGE", 0) / 100,
                        "spatial_resolution_m": 10,
                        "crs": "EPSG:4326"
                    },
                    "image_id": best_image.id().getInfo(),
                    "geometry": roi.getInfo()
                }
            }
            
        except Exception as e:
            logger.error(f"❌ Sentinel-2 data fetch error: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "code": "FETCH_ERROR"
            }
    
    @classmethod
    def fetch_dem_data(
        cls,
        latitude: float,
        longitude: float,
        radius_m: int = 5000
    ) -> Dict[str, Any]:
        """
        Fetch Digital Elevation Model (DEM) data using USGS 3DEP.
        
        Returns:
            {success: bool, data: {...}, error: str}
        """
        try:
            if not cls._initialized:
                init_result = cls.initialize()
                if not init_result.get("success"):
                    return init_result
            
            logger.info(f"📐 Fetching DEM data for ({latitude}, {longitude})")
            
            point = ee.Geometry.Point([longitude, latitude])
            roi = point.buffer(radius_m)
            
            # Load USGS 3DEP/NED DEM
            dem = ee.Image("USGS/3DEP/10m").clip(roi)
            
            # Get elevation statistics
            stats = dem.reduceRegion(
                reducer=ee.Reducer.stats(),
                geometry=roi,
                scale=10,
                maxPixels=1e6
            ).getInfo()
            
            logger.info(f"✓ Retrieved DEM: min={stats.get('elevation_min')}m, max={stats.get('elevation_max')}m")
            
            return {
                "success": True,
                "data": {
                    "elevation": stats,
                    "metadata": {
                        "dataset": "USGS 3DEP 10m",
                        "resolution_m": 10,
                        "crs": "EPSG:4326"
                    }
                }
            }
            
        except Exception as e:
            logger.error(f"❌ DEM fetch error: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "code": "DEM_ERROR"
            }
    
    @classmethod
    def calculate_spectral_indices(
        cls,
        image_id: str,
        roi_geometry: Dict
    ) -> Dict[str, Any]:
        """
        Calculate spectral indices for mineral detection.
        
        Indices:
        - NDVI: Normalized Difference Vegetation Index
        - NDMI: Normalized Difference Moisture Index
        - NDII: Normalized Difference Iron Index (mineral detection)
        - SR: Spectral Ratio (geological features)
        
        Returns:
            {success: bool, indices: {...}, error: str}
        """
        try:
            if not cls._initialized:
                init_result = cls.initialize()
                if not init_result.get("success"):
                    return init_result
            
            logger.info(f"🔬 Calculating spectral indices")
            
            # Load image
            image = ee.Image(image_id)
            
            # Extract bands
            red = image.select('B4')
            nir = image.select('B8')
            swir1 = image.select('B11')
            swir2 = image.select('B12')
            
            # Calculate indices
            ndvi = nir.subtract(red).divide(nir.add(red)).rename('ndvi')
            ndii = nir.subtract(swir1).divide(nir.add(swir1)).rename('ndii')
            sr = nir.divide(red).rename('sr')
            
            # Combine indices
            indices_image = ndvi.addBands(ndii).addBands(sr)
            
            # Get statistics
            stats = indices_image.reduceRegion(
                reducer=ee.Reducer.mean(),
                geometry=ee.Geometry(roi_geometry),
                scale=10,
                maxPixels=1e6
            ).getInfo()
            
            logger.info(f"✓ Calculated spectral indices: {list(stats.keys())}")
            
            return {
                "success": True,
                "indices": stats
            }
            
        except Exception as e:
            logger.error(f"❌ Spectral index calculation error: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "code": "INDEX_ERROR"
            }


# Module-level convenience functions
def initialize_gee(credentials_path: Optional[str] = None) -> Dict[str, Any]:
    """Initialize GEE globally"""
    return GEEIntegration.initialize(credentials_path)


def fetch_satellite_data(
    latitude: float,
    longitude: float,
    **kwargs
) -> Dict[str, Any]:
    """Fetch Sentinel-2 data for a location"""
    return GEEIntegration.fetch_sentinel2_data(latitude, longitude, **kwargs)


def fetch_elevation_data(
    latitude: float,
    longitude: float,
    **kwargs
) -> Dict[str, Any]:
    """Fetch DEM data for a location"""
    return GEEIntegration.fetch_dem_data(latitude, longitude, **kwargs)


def calculate_indices(
    image_id: str,
    roi_geometry: Dict
) -> Dict[str, Any]:
    """Calculate spectral indices"""
    return GEEIntegration.calculate_spectral_indices(image_id, roi_geometry)
