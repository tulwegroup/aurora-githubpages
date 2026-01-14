"""
Aurora OSI v3 - Configuration Management
Environment variables and settings
"""

import os
from typing import Optional
from functools import lru_cache
import logging

logger = logging.getLogger(__name__)


class Settings:
    """Application settings from environment variables"""

    # API Configuration
    API_VERSION: str = "v3.0"
    API_TITLE: str = "Aurora OSI v3 API"
    API_DESCRIPTION: str = "Advanced Geophysical Intelligence Platform"
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")

    # Server Configuration
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", 8000))
    RELOAD: bool = DEBUG
    WORKERS: int = int(os.getenv("WORKERS", 4))
    TIMEOUT: int = int(os.getenv("TIMEOUT", 300))
    KEEP_ALIVE: int = int(os.getenv("KEEP_ALIVE", 65))

    # Database Configuration
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql://aurora_user:aurora_pass@localhost:5432/aurora_osi_v3"
    )
    DATABASE_POOL_SIZE: int = int(os.getenv("DATABASE_POOL_SIZE", "20"))
    DATABASE_MAX_OVERFLOW: int = int(os.getenv("DATABASE_MAX_OVERFLOW", "10"))
    DATABASE_POOL_RECYCLE: int = int(os.getenv("DATABASE_POOL_RECYCLE", "3600"))
    DATABASE_ECHO: bool = DEBUG

    # Redis Configuration
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    REDIS_CACHE_TTL: int = int(os.getenv("REDIS_CACHE_TTL", "3600"))
    REDIS_SESSION_TTL: int = int(os.getenv("REDIS_SESSION_TTL", "86400"))

    # Google Earth Engine Configuration
    GEE_SERVICE_ACCOUNT_FILE: Optional[str] = os.getenv("GEE_SERVICE_ACCOUNT_FILE")
    GEE_PROJECT_ID: str = os.getenv("GEE_PROJECT_ID", "aurora-osi-gee")
    GEE_REQUEST_TIMEOUT: int = int(os.getenv("GEE_REQUEST_TIMEOUT", "300"))
    GEE_BATCH_SIZE: int = int(os.getenv("GEE_BATCH_SIZE", "100"))

    # Authentication Configuration
    SECRET_KEY: str = os.getenv(
        "SECRET_KEY",
        "your-super-secret-key-change-in-production"
    )
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
    REFRESH_TOKEN_EXPIRE_DAYS: int = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))

    # CORS Configuration
    CORS_ORIGINS: list = [
        "http://localhost:3000",
        "http://localhost:5173",
        "https://aurora-osi-v4.up.railway.app",
        "https://aurora-osi-frontend.vercel.app",
        os.getenv("FRONTEND_URL", "")
    ]
    CORS_CREDENTIALS: bool = True
    CORS_METHODS: list = ["*"]
    CORS_HEADERS: list = ["*"]

    # Celery Configuration
    CELERY_BROKER_URL: str = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/1")
    CELERY_RESULT_BACKEND: str = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/2")
    CELERY_TASK_TIMEOUT: int = int(os.getenv("CELERY_TASK_TIMEOUT", "3600"))
    CELERY_TASK_RETRY_ATTEMPTS: int = int(os.getenv("CELERY_TASK_RETRY_ATTEMPTS", "3"))

    # Logging Configuration
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    LOG_FILE: str = os.getenv("LOG_FILE", "logs/aurora.log")

    # Feature Flags
    ENABLE_GEE_INTEGRATION: bool = os.getenv("ENABLE_GEE_INTEGRATION", "true").lower() == "true"
    ENABLE_QUANTUM_INVERSION: bool = os.getenv("ENABLE_QUANTUM_INVERSION", "false").lower() == "true"
    ENABLE_SEISMIC_PROCESSING: bool = os.getenv("ENABLE_SEISMIC_PROCESSING", "true").lower() == "true"
    ENABLE_DIGITAL_TWIN: bool = os.getenv("ENABLE_DIGITAL_TWIN", "true").lower() == "true"

    # API Rate Limiting
    RATE_LIMIT_REQUESTS: int = int(os.getenv("RATE_LIMIT_REQUESTS", "100"))
    RATE_LIMIT_PERIOD: int = int(os.getenv("RATE_LIMIT_PERIOD", "60"))

    # Satellite Configuration
    SATELLITE_BANDS: dict = {
        "Sentinel-2": {
            "resolution": 10,
            "bands": ["B2", "B3", "B4", "B5", "B6", "B7", "B8", "B8A", "B11", "B12"],
            "swath_width": 290
        },
        "Landsat-8": {
            "resolution": 30,
            "bands": ["B1", "B2", "B3", "B4", "B5", "B6", "B7", "B8", "B9", "B10", "B11"],
            "swath_width": 185
        },
        "ASTER": {
            "resolution": 15,
            "bands": ["B1", "B2", "B3", "B4", "B5", "B6", "B7", "B8", "B9", "B10", "B11", "B12", "B13", "B14"],
            "swath_width": 60
        }
    }

    # Mineral Detection Configuration
    MINERAL_CONFIDENCE_THRESHOLD: float = float(os.getenv("MINERAL_CONFIDENCE_THRESHOLD", "0.65"))
    MINERAL_SPECTRAL_TOLERANCE: float = float(os.getenv("MINERAL_SPECTRAL_TOLERANCE", "0.08"))
    MAX_DETECTION_RESULTS: int = int(os.getenv("MAX_DETECTION_RESULTS", "100"))

    # Inversion Configuration
    INVERSION_MAX_ITERATIONS: int = int(os.getenv("INVERSION_MAX_ITERATIONS", "1000"))
    INVERSION_CONVERGENCE_TOLERANCE: float = float(os.getenv("INVERSION_CONVERGENCE_TOLERANCE", "1e-6"))
    REGULARIZATION_PARAMETER: float = float(os.getenv("REGULARIZATION_PARAMETER", "0.01"))

    # Physical Constraints
    POISSON_GRAVITY_CONSTANT: float = 6.674e-11  # m³/kg·s²
    EARTH_DENSITY_MEAN: float = 5514.0  # kg/m³
    CRUSTAL_THICKNESS_KM: float = 35.0
    MANTLE_DENSITY: float = 3300.0  # kg/m³

    # Temporal Configuration
    TEMPORAL_WINDOW_DAYS: int = int(os.getenv("TEMPORAL_WINDOW_DAYS", "30"))
    HISTORICAL_DATA_RETENTION_DAYS: int = int(os.getenv("HISTORICAL_DATA_RETENTION_DAYS", "365"))
    CACHE_EXPIRY_HOURS: int = int(os.getenv("CACHE_EXPIRY_HOURS", "24"))

    # Output Configuration
    OUTPUT_DIR: str = os.getenv("OUTPUT_DIR", "output")
    EXPORT_FORMATS: list = ["GeoTIFF", "NetCDF", "JSON", "CSV", "Shapefile"]
    MAX_EXPORT_SIZE_MB: int = int(os.getenv("MAX_EXPORT_SIZE_MB", "500"))

    @classmethod
    def get_database_url(cls) -> str:
        """Get database URL with SSL requirement for production"""
        url = cls.DATABASE_URL
        if cls.ENVIRONMENT == "production" and "postgresql" in url:
            if "?" not in url:
                url += "?sslmode=require"
            elif "sslmode" not in url:
                url += "&sslmode=require"
        return url

    @classmethod
    def get_log_level(cls) -> int:
        """Convert LOG_LEVEL string to logging constant"""
        level_map = {
            "DEBUG": logging.DEBUG,
            "INFO": logging.INFO,
            "WARNING": logging.WARNING,
            "ERROR": logging.ERROR,
            "CRITICAL": logging.CRITICAL
        }
        return level_map.get(cls.LOG_LEVEL, logging.INFO)

    @classmethod
    def is_production(cls) -> bool:
        """Check if running in production"""
        return cls.ENVIRONMENT == "production"

    @classmethod
    def is_development(cls) -> bool:
        """Check if running in development"""
        return cls.ENVIRONMENT == "development"


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    logger.info(f"Loading settings for environment: {Settings.ENVIRONMENT}")
    return Settings()


# Export settings instance
settings = get_settings()
