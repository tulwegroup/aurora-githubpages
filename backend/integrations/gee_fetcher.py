"""
Aurora OSI v3 - Google Earth Engine Data Fetcher
Satellite data acquisition and preprocessing
"""

import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import numpy as np
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class SatelliteData:
    """Container for satellite imagery data"""
    date: datetime
    sensor: str
    latitude: float
    longitude: float
    bands: Dict[str, np.ndarray]
    cloud_coverage: float
    resolution_m: int


class GEEDataFetcher:
    """Fetch satellite data from Google Earth Engine"""

    def __init__(self):
        """Initialize GEE data fetcher with service account credentials"""
        try:
            import ee
            import json
            import os
            
            # Don't initialize here - use gee_integration module instead
            logger.info("📡 GEE Data Fetcher initialized (using gee_integration module)")
            
        except Exception as e:
            logger.error(f"❌ GEE Data Fetcher initialization failed: {str(e)}")
            raise

    def fetch_sentinel2(
        self,
        latitude: float,
        longitude: float,
        date_start: str,
        date_end: str,
        radius_m: int = 1000
    ) -> Optional[SatelliteData]:
        """
        Fetch Sentinel-2 data for location and date range
        
        Args:
            latitude: Latitude in degrees
            longitude: Longitude in degrees
            date_start: Start date (YYYY-MM-DD)
            date_end: End date (YYYY-MM-DD)
            radius_m: Search radius in meters
        
        Returns:
            SatelliteData object with bands and metadata
        """
        try:
            import ee
            
            # Create point geometry
            point = ee.Geometry.Point([longitude, latitude])
            
            # Define bands to extract
            bands = {
                "B2": "blue",
                "B3": "green",
                "B4": "red",
                "B5": "red_edge_1",
                "B6": "red_edge_2",
                "B7": "red_edge_3",
                "B8": "nir",
                "B8A": "red_edge_4",
                "B11": "swir_1",
                "B12": "swir_2"
            }
            
            # Query Sentinel-2 collection
            collection = (
                ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
                .filterBounds(point)
                .filterDate(date_start, date_end)
                .sort("CLOUD_COVERAGE_ASSESSMENT")
            )
            
            if collection.size().getInfo() == 0:
                logger.warning(f"No Sentinel-2 data found for {latitude}, {longitude}")
                return None
            
            # Get first (least cloudy) image
            image = ee.Image(collection.first())
            
            # Sample pixel values
            sample = image.sample(point, scale=10)
            data = sample.getInfo()
            
            if not data.get("features"):
                return None
            
            properties = data["features"][0]["properties"]
            
            # Extract bands
            band_data = {name: float(properties.get(band_id, 0)) for band_id, name in bands.items()}
            
            # Get cloud coverage
            cloud_coverage = image.get("CLOUD_COVERAGE_ASSESSMENT").getInfo() or 0
            
            return SatelliteData(
                date=datetime.now(),
                sensor="Sentinel-2",
                latitude=latitude,
                longitude=longitude,
                bands=band_data,
                cloud_coverage=float(cloud_coverage),
                resolution_m=10
            )
        
        except Exception as e:
            logger.error(f"Sentinel-2 fetch failed: {e}")
            return None

    def fetch_landsat8(
        self,
        latitude: float,
        longitude: float,
        date_start: str,
        date_end: str,
        radius_m: int = 1000
    ) -> Optional[SatelliteData]:
        """Fetch Landsat-8 data for location and date range"""
        try:
            import ee
            
            point = ee.Geometry.Point([longitude, latitude])
            
            bands = {
                "SR_B1": "coastal_aerosol",
                "SR_B2": "blue",
                "SR_B3": "green",
                "SR_B4": "red",
                "SR_B5": "nir",
                "SR_B6": "swir_1",
                "SR_B7": "swir_2"
            }
            
            collection = (
                ee.ImageCollection("LANDSAT/LC09/C02/T1_L2")
                .filterBounds(point)
                .filterDate(date_start, date_end)
                .sort("CLOUD_COVER")
            )
            
            if collection.size().getInfo() == 0:
                logger.warning(f"No Landsat-8 data found for {latitude}, {longitude}")
                return None
            
            image = ee.Image(collection.first())
            sample = image.sample(point, scale=30)
            data = sample.getInfo()
            
            if not data.get("features"):
                return None
            
            properties = data["features"][0]["properties"]
            band_data = {name: float(properties.get(band_id, 0)) for band_id, name in bands.items()}
            cloud_coverage = image.get("CLOUD_COVER").getInfo() or 0
            
            return SatelliteData(
                date=datetime.now(),
                sensor="Landsat-8",
                latitude=latitude,
                longitude=longitude,
                bands=band_data,
                cloud_coverage=float(cloud_coverage),
                resolution_m=30
            )
        
        except Exception as e:
            logger.error(f"Landsat-8 fetch failed: {e}")
            return None

    def fetch_aster(
        self,
        latitude: float,
        longitude: float,
        date_start: str,
        date_end: str
    ) -> Optional[SatelliteData]:
        """Fetch ASTER hyperspectral data"""
        try:
            import ee
            
            point = ee.Geometry.Point([longitude, latitude])
            
            bands = {
                f"B{i:02d}": f"band_{i}" for i in range(1, 15)
            }
            
            collection = (
                ee.ImageCollection("ASTER/AST_L1T_EMISSIVE/003")
                .filterBounds(point)
                .filterDate(date_start, date_end)
            )
            
            if collection.size().getInfo() == 0:
                logger.warning(f"No ASTER data found for {latitude}, {longitude}")
                return None
            
            image = ee.Image(collection.first())
            sample = image.sample(point, scale=15)
            data = sample.getInfo()
            
            if not data.get("features"):
                return None
            
            properties = data["features"][0]["properties"]
            band_data = {name: float(properties.get(band_id, 0)) for band_id, name in bands.items()}
            
            return SatelliteData(
                date=datetime.now(),
                sensor="ASTER",
                latitude=latitude,
                longitude=longitude,
                bands=band_data,
                cloud_coverage=0.0,
                resolution_m=15
            )
        
        except Exception as e:
            logger.error(f"ASTER fetch failed: {e}")
            return None

    def calculate_indices(self, data: SatelliteData) -> Dict[str, float]:
        """Calculate spectral indices from satellite data"""
        indices = {}
        
        try:
            if data.sensor == "Sentinel-2":
                # NDVI = (NIR - RED) / (NIR + RED)
                nir = data.bands.get("nir", 0)
                red = data.bands.get("red", 0)
                if nir + red > 0:
                    indices["ndvi"] = (nir - red) / (nir + red)
                
                # NDMI = (NIR - SWIR1) / (NIR + SWIR1)
                swir1 = data.bands.get("swir_1", 0)
                if nir + swir1 > 0:
                    indices["ndmi"] = (nir - swir1) / (nir + swir1)
                
                # CMI = SWIR2 / SWIR1 (Clay minerals)
                swir2 = data.bands.get("swir_2", 0)
                if swir1 > 0:
                    indices["cmi"] = swir2 / swir1
            
            logger.info(f"Calculated {len(indices)} spectral indices")
        
        except Exception as e:
            logger.error(f"Index calculation failed: {e}")
        
        return indices


    def fetch_sentinel2_data(
        self,
        latitude: float,
        longitude: float,
        start_date: str = None,
        end_date: str = None,
        radius_m: int = 1000
    ) -> Dict:
        """
        Fetch real Sentinel-2 satellite data for Mission Control workflow.
        Returns formatted data or error object.
        
        Args:
            latitude: Location latitude
            longitude: Location longitude
            start_date: Start date (YYYY-MM-DD), defaults to 30 days ago
            end_date: End date (YYYY-MM-DD), defaults to today
            radius_m: Search radius in meters
        
        Returns:
            Dict with satellite data or error info
        """
        try:
            # Use GEE integration module instead for direct API access
            from backend.integrations.gee_integration import GEEIntegration
            
            # Set default dates if not provided
            if not end_date:
                end_date = datetime.now().isoformat()
            if not start_date:
                start_date = (datetime.now() - timedelta(days=30)).isoformat()
            
            # Use GEE integration directly (it handles initialization)
            result = GEEIntegration.fetch_sentinel2_data(
                latitude=latitude,
                longitude=longitude,
                start_date=start_date,
                end_date=end_date,
                radius_m=radius_m
            )
            
            if not result.get("success"):
                logger.error(f"GEE fetch failed: {result.get('error', 'Unknown error')}")
                return {
                    "error": result.get("error", "Unknown error"),
                    "code": result.get("code", "FETCH_ERROR")
                }
            
            satellite_data_dict = result.get("data", {})
            
            # Call the native fetch_sentinel2 method for compatibility
            satellite_data = self.fetch_sentinel2(
                latitude=latitude,
                longitude=longitude,
                date_start=start_date.split('T')[0],
                date_end=end_date.split('T')[0],
                radius_m=radius_m
            )
            
            if satellite_data is None:
                return {
                    "error": f"No Sentinel-2 data available for location ({latitude}, {longitude}) in timeframe {start_date} to {end_date}",
                    "code": "NO_DATA"
                }
            
            # Calculate spectral indices
            indices = self.calculate_indices(satellite_data)
            
            # Return formatted data
            return {
                "status": "success",
                "sensor": satellite_data.sensor,
                "date": satellite_data.date.isoformat() if hasattr(satellite_data.date, 'isoformat') else str(satellite_data.date),
                "latitude": satellite_data.latitude,
                "longitude": satellite_data.longitude,
                "cloud_coverage": satellite_data.cloud_coverage,
                "resolution_m": satellite_data.resolution_m,
                "bands": {k: v.tolist() if isinstance(v, np.ndarray) else v for k, v in satellite_data.bands.items()},
                "indices": indices,
                "metadata": {
                    "start_date": start_date,
                    "end_date": end_date,
                    "search_radius_m": radius_m
                }
            }
            
        except Exception as e:
            logger.error(f"Sentinel-2 data fetch failed: {str(e)}")
            import traceback
            traceback.print_exc()
            return {
                "error": f"Failed to fetch Sentinel-2 data: {str(e)}",
                "code": "FETCH_ERROR"
            }


def get_gee_fetcher() -> GEEDataFetcher:
    """Get or create GEE data fetcher instance"""
    return GEEDataFetcher()
