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
            
            # Try to authenticate with service account if credentials available
            service_account_file = os.getenv("GEE_SERVICE_ACCOUNT_FILE")
            service_account_json = os.getenv("GEE_SERVICE_ACCOUNT_JSON")
            
            if service_account_file and os.path.exists(service_account_file):
                logger.info(f"📡 Initializing GEE with service account file: {service_account_file}")
                ee.Authenticate(filename=service_account_file)
                ee.Initialize(project=os.getenv("GEE_PROJECT_ID", "aurora-osi-gee"))
                logger.info("✅ GEE initialized with service account file")
            elif service_account_json:
                logger.info("📡 Initializing GEE with service account JSON from environment")
                # Parse JSON from environment variable
                creds = json.loads(service_account_json)
                # Write to temporary file for authentication
                temp_creds_path = "/tmp/gee_service_account.json"
                with open(temp_creds_path, 'w') as f:
                    json.dump(creds, f)
                ee.Authenticate(filename=temp_creds_path)
                ee.Initialize(project=creds.get("project_id", os.getenv("GEE_PROJECT_ID", "aurora-osi-gee")))
                logger.info("✅ GEE initialized with service account JSON")
            else:
                # Try default initialization (may use Application Default Credentials)
                logger.warning("⚠️ No GEE service account credentials found. Attempting default initialization...")
                ee.Initialize()
                logger.info("GEE initialized with default credentials")
                
        except Exception as e:
            logger.error(f"❌ GEE initialization failed: {str(e)}")
            import traceback
            traceback.print_exc()
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


def get_gee_fetcher() -> GEEDataFetcher:
    """Get or create GEE data fetcher instance"""
    return GEEDataFetcher()
