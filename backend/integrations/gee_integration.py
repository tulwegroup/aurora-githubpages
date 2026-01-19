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
            
            # Check if file exists
            if not os.path.exists(creds_path):
                logger.error(f"❌ Credentials file not found: {creds_path}")
                return {
                    "success": False,
                    "error": f"Credentials file not found: {creds_path}",
                    "code": "FILE_NOT_FOUND"
                }
            
            # Authenticate with service account credentials
            credentials = ee.ServiceAccountCredentials.from_authorized_user_file(creds_path)
            ee.Initialize(credentials)
            
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
        max_cloud_cover: float = 0.5
    ) -> Dict[str, Any]:
        """
        Fetch ALL available satellite/geophysical data from GEE for a location.
        
        Queries COMPREHENSIVE data sources:
        - OPTICAL: Sentinel-2, Landsat 8/9, MODIS
        - RADAR: Sentinel-1 SAR (penetrates clouds)
        - TOPOGRAPHY: SRTM, GEBCO, ASTER
        - VEGETATION: NDVI, LAI, FPAR
        - LAND COVER: ESA WorldCover, Copernicus
        - CLIMATE: Temperature, precipitation
        - SOIL: SoilGrids data
        - WATER: Water indices, permanent water
        - Other: CHIRPS rainfall, etc.
        
        Works for every point on Earth - queries all available data regardless of date.
        
        Args:
            latitude: Target latitude
            longitude: Target longitude
            radius_m: Search radius in meters (default: 5km)
            start_date: Optional - only used for recent time-series queries
            end_date: Optional - only used for recent time-series queries
            max_cloud_cover: Maximum acceptable cloud cover (0-1, default: 50%)
        
        Returns:
            {
                success: bool,
                data: {
                    bands: {all available datasets},
                    metadata: {query info}
                },
                error: str (if failed)
            }
        """
        try:
            if not cls._initialized:
                init_result = cls.initialize()
                if not init_result.get("success"):
                    return init_result
            
            logger.info(f"🛰️ Fetching ALL available satellite data for ({latitude}, {longitude})")
            
            # Create point geometry
            point = ee.Geometry.Point([longitude, latitude])
            roi = point.buffer(radius_m)
            
            collected_data = {}
            
            # ===== OPTICAL IMAGERY =====
            
            # 1. Sentinel-2 (10m resolution, multispectral)
            try:
                logger.info("📡 Sentinel-2 (optical)...")
                s2_collection = ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED") \
                    .filterBounds(roi) \
                    .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", max_cloud_cover * 100)) \
                    .sort("CLOUDY_PIXEL_PERCENTAGE")
                
                count_s2 = s2_collection.size().getInfo()
                if count_s2 > 0:
                    s2_image = s2_collection.first()
                    s2_bands = s2_image.select(['B1', 'B2', 'B3', 'B4', 'B5', 'B6', 'B7', 'B8', 'B8A', 'B11', 'B12']).float().clip(roi)
                    s2_stats = s2_bands.reduceRegion(
                        reducer=ee.Reducer.mean(),
                        geometry=roi,
                        scale=10,
                        maxPixels=1e6
                    ).getInfo()
                    collected_data['sentinel2_bands'] = s2_stats
                    logger.info(f"✓ Sentinel-2: {count_s2} images")
            except Exception as e:
                logger.warning(f"⚠️ Sentinel-2: {str(e)[:50]}")
            
            # 2. Landsat 8/9 (30m resolution, multispectral)
            try:
                logger.info("📡 Landsat 8/9...")
                ls_collection = ee.ImageCollection("LANDSAT/LC09/C02/T1_L2") \
                    .filterBounds(roi) \
                    .filter(ee.Filter.lt("CLOUD_COVER", max_cloud_cover * 100)) \
                    .sort("CLOUD_COVER")
                
                count_ls = ls_collection.size().getInfo()
                if count_ls > 0:
                    ls_image = ls_collection.first()
                    ls_bands = ls_image.select(['SR_B1', 'SR_B2', 'SR_B3', 'SR_B4', 'SR_B5', 'SR_B6', 'SR_B7']).float().clip(roi)
                    ls_stats = ls_bands.reduceRegion(
                        reducer=ee.Reducer.mean(),
                        geometry=roi,
                        scale=30,
                        maxPixels=1e6
                    ).getInfo()
                    collected_data['landsat_bands'] = ls_stats
                    logger.info(f"✓ Landsat: {count_ls} images")
            except Exception as e:
                logger.warning(f"⚠️ Landsat: {str(e)[:50]}")
            
            # 3. MODIS (250m resolution, good temporal coverage)
            try:
                logger.info("📡 MODIS...")
                modis = ee.ImageCollection("MODIS/061/MOD09GA") \
                    .filterBounds(roi) \
                    .filter(ee.Filter.lt("CLOUD_COVER", max_cloud_cover * 100))
                
                count_modis = modis.size().getInfo()
                if count_modis > 0:
                    modis_img = modis.first()
                    modis_bands = modis_img.select(['sur_refl_b01', 'sur_refl_b02', 'sur_refl_b03', 'sur_refl_b04', 'sur_refl_b05', 'sur_refl_b06', 'sur_refl_b07']).float().clip(roi)
                    modis_stats = modis_bands.reduceRegion(
                        reducer=ee.Reducer.mean(),
                        geometry=roi,
                        scale=250,
                        maxPixels=1e6
                    ).getInfo()
                    collected_data['modis_bands'] = modis_stats
                    logger.info(f"✓ MODIS: {count_modis} images")
            except Exception as e:
                logger.warning(f"⚠️ MODIS: {str(e)[:50]}")
            
            # ===== RADAR DATA =====
            
            # 4. Sentinel-1 SAR (penetrates clouds, all-weather)
            try:
                logger.info("📡 Sentinel-1 SAR...")
                sar_collection = ee.ImageCollection("COPERNICUS/S1_GRD") \
                    .filterBounds(roi) \
                    .filter(ee.Filter.eq('instrumentMode', 'IW'))
                
                count_sar = sar_collection.size().getInfo()
                if count_sar > 0:
                    sar_image = sar_collection.first()
                    sar_bands = sar_image.select(['VV', 'VH']).clip(roi)
                    sar_stats = sar_bands.reduceRegion(
                        reducer=ee.Reducer.mean(),
                        geometry=roi,
                        scale=10,
                        maxPixels=1e6
                    ).getInfo()
                    collected_data['sar_vh_vv'] = sar_stats
                    logger.info(f"✓ Sentinel-1: {count_sar} images")
            except Exception as e:
                logger.warning(f"⚠️ Sentinel-1: {str(e)[:50]}")
            
            # 5. ALOS PALSAR (L-band SAR, penetrates vegetation)
            try:
                logger.info("📡 ALOS PALSAR...")
                palsar = ee.ImageCollection("JAXA/ALOS/PALSAR/YEARLY/SAR") \
                    .filterBounds(roi) \
                    .select(['HH', 'HV'])
                
                count_palsar = palsar.size().getInfo()
                if count_palsar > 0:
                    palsar_img = palsar.first()
                    palsar_stats = palsar_img.clip(roi).reduceRegion(
                        reducer=ee.Reducer.mean(),
                        geometry=roi,
                        scale=25,
                        maxPixels=1e6
                    ).getInfo()
                    collected_data['palsar_hh_hv'] = palsar_stats
                    logger.info(f"✓ ALOS PALSAR: {count_palsar} images")
            except Exception as e:
                logger.warning(f"⚠️ ALOS PALSAR: {str(e)[:50]}")
            
            # ===== TOPOGRAPHY & ELEVATION =====
            
            # 6. SRTM DEM (global 30m)
            try:
                logger.info("📡 SRTM DEM...")
                srtm = ee.Image("USGS/SRTMGL1_Ellip/SRTMGL1_Ellip_srtm")
                elevation = srtm.sample(point, scale=30).getInfo()
                if elevation.get("features"):
                    elev = elevation["features"][0]["properties"].get("elevation", None)
                    collected_data['srtm_elevation_m'] = float(elev) if elev is not None else None
                    # Also compute slope
                    slope = ee.Terrain.slope(srtm).sample(point, scale=30).getInfo()
                    if slope.get("features"):
                        slope_val = slope["features"][0]["properties"].get("slope", None)
                        collected_data['slope_degrees'] = float(slope_val) if slope_val is not None else None
                    logger.info(f"✓ SRTM DEM")
            except Exception as e:
                logger.warning(f"⚠️ SRTM DEM: {str(e)[:50]}")
            
            # 7. GEBCO Bathymetry/Topography (global)
            try:
                logger.info("📡 GEBCO...")
                gebco = ee.Image("GEBCO/2023")
                topo = gebco.sample(point, scale=100).getInfo()
                if topo.get("features"):
                    topo_val = topo["features"][0]["properties"].get("elevation", None)
                    collected_data['gebco_elevation_m'] = float(topo_val) if topo_val is not None else None
                    logger.info(f"✓ GEBCO")
            except Exception as e:
                logger.warning(f"⚠️ GEBCO: {str(e)[:50]}")
            
            # 8. ASTER DEM (15m resolution, global)
            try:
                logger.info("📡 ASTER DEM...")
                aster = ee.Image("ASTER/AST_L1T_003/003_01_20150101T000000")
                aster_dem = ee.Image("USGS/ASTGTM/V003")
                dem = aster_dem.select(['elevation']).sample(point, scale=30).getInfo()
                if dem.get("features"):
                    dem_val = dem["features"][0]["properties"].get("elevation", None)
                    collected_data['aster_dem_m'] = float(dem_val) if dem_val is not None else None
                    logger.info(f"✓ ASTER DEM")
            except Exception as e:
                logger.warning(f"⚠️ ASTER DEM: {str(e)[:50]}")
            
            # ===== VEGETATION & INDICES =====
            
            # 9. NDVI (Normalized Difference Vegetation Index)
            try:
                logger.info("📡 Vegetation indices...")
                s2_collection = ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED") \
                    .filterBounds(roi) \
                    .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", max_cloud_cover * 100))
                
                if s2_collection.size().getInfo() > 0:
                    img = s2_collection.first()
                    ndvi = img.normalizedDifference(['B8', 'B4'])
                    ndbi = img.normalizedDifference(['B11', 'B8'])  # Normalized Difference Built-up Index
                    ndmi = img.normalizedDifference(['B8', 'B11'])  # Normalized Difference Moisture Index
                    
                    ndvi_val = ndvi.sample(point, scale=10).getInfo()
                    ndbi_val = ndbi.sample(point, scale=10).getInfo()
                    ndmi_val = ndmi.sample(point, scale=10).getInfo()
                    
                    if ndvi_val.get("features"):
                        collected_data['ndvi'] = float(ndvi_val["features"][0]["properties"].get("nd", 0))
                    if ndbi_val.get("features"):
                        collected_data['ndbi'] = float(ndbi_val["features"][0]["properties"].get("nd", 0))
                    if ndmi_val.get("features"):
                        collected_data['ndmi'] = float(ndmi_val["features"][0]["properties"].get("nd", 0))
                    logger.info(f"✓ Vegetation indices")
            except Exception as e:
                logger.warning(f"⚠️ Vegetation indices: {str(e)[:50]}")
            
            # 10. MODIS LAI (Leaf Area Index)
            try:
                logger.info("📡 MODIS LAI...")
                lai = ee.ImageCollection("MODIS/061/MCD15A3H") \
                    .filterBounds(roi)
                
                if lai.size().getInfo() > 0:
                    lai_img = lai.first().select(['Lai'])
                    lai_val = lai_img.sample(point, scale=500).getInfo()
                    if lai_val.get("features"):
                        collected_data['modis_lai'] = float(lai_val["features"][0]["properties"].get("Lai", 0)) / 10.0
                    logger.info(f"✓ MODIS LAI")
            except Exception as e:
                logger.warning(f"⚠️ MODIS LAI: {str(e)[:50]}")
            
            # ===== LAND COVER =====
            
            # 11. ESA WorldCover (10m land cover classification)
            try:
                logger.info("📡 ESA WorldCover...")
                worldcover = ee.ImageCollection("ESA/WorldCover/v200") \
                    .filterBounds(roi)
                
                if worldcover.size().getInfo() > 0:
                    wc = worldcover.first()
                    lc_val = wc.sample(point, scale=10).getInfo()
                    if lc_val.get("features"):
                        lc_class = int(lc_val["features"][0]["properties"].get("Map", 0))
                        lc_names = {
                            10: "Tree cover",
                            20: "Shrubland",
                            30: "Herbaceous",
                            40: "Cropland",
                            50: "Built-up",
                            60: "Barren",
                            70: "Snow/ice",
                            80: "Open water",
                            90: "Herbaceous wetland",
                            95: "Mangroves",
                            100: "Moss/lichen"
                        }
                        collected_data['land_cover_class'] = lc_class
                        collected_data['land_cover_type'] = lc_names.get(lc_class, "Unknown")
                    logger.info(f"✓ ESA WorldCover")
            except Exception as e:
                logger.warning(f"⚠️ ESA WorldCover: {str(e)[:50]}")
            
            # 12. Copernicus Land Cover (100m)
            try:
                logger.info("📡 Copernicus LULC...")
                lulc = ee.ImageCollection("COPERNICUS/CORINE/V20/100m") \
                    .filterBounds(roi)
                
                if lulc.size().getInfo() > 0:
                    lulc_img = lulc.first()
                    lulc_val = lulc_img.sample(point, scale=100).getInfo()
                    if lulc_val.get("features"):
                        collected_data['copernicus_lulc'] = int(lulc_val["features"][0]["properties"].get("classification", 0))
                    logger.info(f"✓ Copernicus LULC")
            except Exception as e:
                logger.warning(f"⚠️ Copernicus LULC: {str(e)[:50]}")
            
            # ===== CLIMATE & WEATHER =====
            
            # 13. MODIS Land Surface Temperature
            try:
                logger.info("📡 MODIS Temperature...")
                lst = ee.ImageCollection("MODIS/061/MOD11A1") \
                    .filterBounds(roi)
                
                if lst.size().getInfo() > 0:
                    lst_img = lst.first().select(['LST_Day_1km'])
                    temp_val = lst_img.sample(point, scale=1000).getInfo()
                    if temp_val.get("features"):
                        # MODIS LST is in Kelvin * 0.02
                        collected_data['lst_kelvin'] = float(temp_val["features"][0]["properties"].get("LST_Day_1km", 0)) * 0.02
                    logger.info(f"✓ MODIS LST")
            except Exception as e:
                logger.warning(f"⚠️ MODIS LST: {str(e)[:50]}")
            
            # 14. ERA5 Climate Data (temperature, precipitation)
            try:
                logger.info("📡 ERA5 Climate...")
                era5 = ee.ImageCollection("ECMWF/ERA5_LAND/MONTHLY_AGGR") \
                    .filterBounds(roi)
                
                if era5.size().getInfo() > 0:
                    era5_img = era5.first()
                    climate_data = era5_img.sample(point, scale=11132).getInfo()
                    if climate_data.get("features"):
                        props = climate_data["features"][0]["properties"]
                        if 'temperature_2m' in props:
                            collected_data['era5_temp_2m_k'] = float(props['temperature_2m'])
                        if 'precipitation' in props:
                            collected_data['era5_precipitation_mm'] = float(props['precipitation'])
                    logger.info(f"✓ ERA5 Climate")
            except Exception as e:
                logger.warning(f"⚠️ ERA5: {str(e)[:50]}")
            
            # ===== SOIL & GEOLOGY =====
            
            # 15. SoilGrids data
            try:
                logger.info("📡 SoilGrids...")
                soilgrids = ee.Image("projects/soilgrids-isric/soilgrids2.0/prediction_mean/silt_mean_0-5cm_2017")
                soil_val = soilgrids.sample(point, scale=250).getInfo()
                if soil_val.get("features"):
                    collected_data['soil_silt_0_5cm_pct'] = float(soil_val["features"][0]["properties"].get("prediction_mean", 0))
                logger.info(f"✓ SoilGrids")
            except Exception as e:
                logger.warning(f"⚠️ SoilGrids: {str(e)[:50]}")
            
            # ===== WATER =====
            
            # 16. Permanent Water (JRC surface water)
            try:
                logger.info("📡 Water indices...")
                water = ee.Image("JRC/GSW1_3/GlobalSurfaceWater")
                occurrence = water.select(['occurrence']).sample(point, scale=30).getInfo()
                if occurrence.get("features"):
                    collected_data['water_occurrence_pct'] = float(occurrence["features"][0]["properties"].get("occurrence", 0))
                logger.info(f"✓ Water data")
            except Exception as e:
                logger.warning(f"⚠️ Water: {str(e)[:50]}")
            
            # ===== RAINFALL =====
            
            # 17. CHIRPS Rainfall
            try:
                logger.info("📡 CHIRPS rainfall...")
                chirps = ee.ImageCollection("UCSB-CHG/CHIRPS-DAILY") \
                    .filterBounds(roi) \
                    .select(['precipitation'])
                
                if chirps.size().getInfo() > 0:
                    chirps_mean = chirps.mean()
                    precip = chirps_mean.sample(point, scale=5000).getInfo()
                    if precip.get("features"):
                        collected_data['chirps_mean_precipitation_mm'] = float(precip["features"][0]["properties"].get("precipitation", 0))
                    logger.info(f"✓ CHIRPS")
            except Exception as e:
                logger.warning(f"⚠️ CHIRPS: {str(e)[:50]}")
            
            # Check if we got ANY data
            if not collected_data:
                logger.error("❌ No satellite data available from any source")
                return {
                    "success": False,
                    "error": "No satellite data available from any GEE source for this location",
                    "code": "NO_DATA_AVAILABLE"
                }
            
            logger.info(f"✓ Retrieved data from {len(collected_data)} parameters/sources")
            
            return {
                "success": True,
                "data": {
                    "bands": collected_data,
                    "metadata": {
                        "latitude": latitude,
                        "longitude": longitude,
                        "radius_m": radius_m,
                        "parameters_count": len(collected_data),
                        "parameters": list(collected_data.keys()),
                        "query_date": datetime.now().isoformat()
                    }
                }
            }
            
        except Exception as e:
            logger.error(f"❌ GEE data fetch error: {str(e)}")
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "error": str(e),
                "code": "GEE_ERROR"
            }
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
