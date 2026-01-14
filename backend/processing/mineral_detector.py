"""
Aurora OSI v3 - Mineral Detection Processor
Spectral mineral identification from satellite data
"""

import logging
from typing import Dict, List, Optional, Tuple
import numpy as np
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class MineralMatch:
    """Represents a mineral match result"""
    mineral: str
    confidence: float
    tier: str
    spectral_distance: float
    wavelengths_matched: List[float]
    depth_estimate_m: Optional[float] = None


class SpectralLibrary:
    """Spectral library for mineral identification"""

    def __init__(self):
        """Initialize spectral library with reference spectra"""
        self.minerals = self._load_reference_spectra()
        logger.info(f"Loaded {len(self.minerals)} reference mineral spectra")

    def _load_reference_spectra(self) -> Dict:
        """Load reference spectral signatures for minerals"""
        return {
            "Limonite": {
                "wavelengths": [0.4, 0.5, 0.6, 0.7, 0.9, 1.1, 1.3, 1.6, 2.0, 2.2],
                "reflectance": [0.15, 0.18, 0.25, 0.30, 0.35, 0.32, 0.28, 0.22, 0.18, 0.15],
                "features": ["absorption_0.9um", "broad_peak_2.1um"],
                "confidence_base": 0.85
            },
            "Goethite": {
                "wavelengths": [0.4, 0.5, 0.6, 0.7, 0.9, 1.1, 1.3, 1.6, 2.0, 2.2],
                "reflectance": [0.10, 0.12, 0.18, 0.22, 0.25, 0.23, 0.20, 0.16, 0.13, 0.11],
                "features": ["strong_0.9um_absorption", "narrow_2.26um"],
                "confidence_base": 0.90
            },
            "Hematite": {
                "wavelengths": [0.4, 0.5, 0.6, 0.7, 0.9, 1.1, 1.3, 1.6, 2.0, 2.2],
                "reflectance": [0.12, 0.14, 0.20, 0.25, 0.28, 0.26, 0.23, 0.18, 0.14, 0.12],
                "features": ["fe3+_absorption_0.86um", "broad_absorption_0.5um"],
                "confidence_base": 0.88
            },
            "Jarosite": {
                "wavelengths": [0.4, 0.5, 0.6, 0.7, 0.9, 1.1, 1.3, 1.6, 2.0, 2.2],
                "reflectance": [0.18, 0.20, 0.25, 0.28, 0.32, 0.30, 0.27, 0.22, 0.18, 0.16],
                "features": ["so4_absorption_1.48um", "so4_absorption_1.94um"],
                "confidence_base": 0.82
            },
            "Calcite": {
                "wavelengths": [0.4, 0.5, 0.6, 0.7, 0.9, 1.1, 1.3, 1.6, 2.0, 2.2],
                "reflectance": [0.40, 0.42, 0.43, 0.44, 0.45, 0.46, 0.44, 0.40, 0.35, 0.30],
                "features": ["co3_absorption_2.0um", "co3_absorption_2.5um"],
                "confidence_base": 0.80
            },
            "Gypsum": {
                "wavelengths": [0.4, 0.5, 0.6, 0.7, 0.9, 1.1, 1.3, 1.6, 2.0, 2.2],
                "reflectance": [0.38, 0.40, 0.41, 0.42, 0.43, 0.44, 0.42, 0.38, 0.33, 0.28],
                "features": ["h2o_absorption_1.45um", "h2o_absorption_1.95um"],
                "confidence_base": 0.78
            },
            "Muscovite": {
                "wavelengths": [0.4, 0.5, 0.6, 0.7, 0.9, 1.1, 1.3, 1.6, 2.0, 2.2],
                "reflectance": [0.28, 0.30, 0.32, 0.35, 0.38, 0.40, 0.38, 0.32, 0.26, 0.22],
                "features": ["al-oh_absorption_2.2um", "si-o_absorption_9um"],
                "confidence_base": 0.83
            },
            "Montmorillonite": {
                "wavelengths": [0.4, 0.5, 0.6, 0.7, 0.9, 1.1, 1.3, 1.6, 2.0, 2.2],
                "reflectance": [0.25, 0.27, 0.29, 0.32, 0.35, 0.37, 0.35, 0.29, 0.23, 0.19],
                "features": ["al-oh_absorption_2.31um", "h2o_absorption"],
                "confidence_base": 0.81
            },
            "Chlorite": {
                "wavelengths": [0.4, 0.5, 0.6, 0.7, 0.9, 1.1, 1.3, 1.6, 2.0, 2.2],
                "reflectance": [0.22, 0.24, 0.26, 0.29, 0.32, 0.34, 0.32, 0.26, 0.20, 0.16],
                "features": ["mg-oh_absorption_2.38um", "h2o_absorption"],
                "confidence_base": 0.79
            },
            "Azurite": {
                "wavelengths": [0.4, 0.5, 0.6, 0.7, 0.9, 1.1, 1.3, 1.6, 2.0, 2.2],
                "reflectance": [0.08, 0.10, 0.12, 0.14, 0.16, 0.14, 0.12, 0.10, 0.08, 0.07],
                "features": ["cu2+_absorption_0.7um", "cu2+_absorption_1.4um"],
                "confidence_base": 0.92
            }
        }

    def detect_mineral(
        self,
        wavelengths: np.ndarray,
        reflectance: np.ndarray,
        threshold: float = 0.65
    ) -> List[MineralMatch]:
        """
        Detect minerals from spectral data
        
        Args:
            wavelengths: Wavelength values (micrometers)
            reflectance: Reflectance values (0-1)
            threshold: Minimum confidence threshold
        
        Returns:
            List of mineral matches sorted by confidence
        """
        matches = []
        
        try:
            for mineral_name, mineral_spec in self.minerals.items():
                # Calculate spectral distance (Euclidean)
                ref_wl = np.array(mineral_spec["wavelengths"])
                ref_refl = np.array(mineral_spec["reflectance"])
                
                # Interpolate if necessary
                interp_refl = np.interp(ref_wl, wavelengths, reflectance, left=0, right=0)
                
                distance = np.sqrt(np.mean((interp_refl - ref_refl) ** 2))
                
                # Calculate confidence
                confidence = mineral_spec["confidence_base"] * (1.0 - np.tanh(distance))
                
                if confidence >= threshold:
                    # Estimate depth using Gardner's equation
                    vp_avg = 5000  # m/s (average)
                    depth_estimate = vp_avg / (2 * 100)  # Simplified
                    
                    matches.append(MineralMatch(
                        mineral=mineral_name,
                        confidence=confidence,
                        tier=self._get_tier(confidence),
                        spectral_distance=distance,
                        wavelengths_matched=ref_wl.tolist(),
                        depth_estimate_m=depth_estimate
                    ))
            
            # Sort by confidence descending
            matches.sort(key=lambda m: m.confidence, reverse=True)
            
            logger.info(f"Detected {len(matches)} minerals")
            return matches
        
        except Exception as e:
            logger.error(f"Mineral detection failed: {e}")
            return []

    @staticmethod
    def _get_tier(confidence: float) -> str:
        """Get detection tier based on confidence"""
        if confidence >= 0.90:
            return "TIER_3"  # Drill-ready
        elif confidence >= 0.80:
            return "TIER_2"  # Exploration target
        elif confidence >= 0.70:
            return "TIER_1"  # Reconnaissance
        else:
            return "TIER_0"  # Low confidence


class MineralDetector:
    """Main mineral detection processor"""

    def __init__(self):
        """Initialize mineral detector"""
        self.library = SpectralLibrary()

    def process_satellite_data(
        self,
        wavelengths: np.ndarray,
        reflectance: np.ndarray,
        location: Tuple[float, float],
        date: datetime
    ) -> Dict:
        """
        Process satellite data for mineral detection
        
        Args:
            wavelengths: Wavelength values
            reflectance: Reflectance values
            location: (latitude, longitude)
            date: Observation date
        
        Returns:
            Detection results dictionary
        """
        try:
            matches = self.library.detect_mineral(wavelengths, reflectance)
            
            return {
                "location": {"lat": location[0], "lon": location[1]},
                "date": date.isoformat(),
                "matches": [
                    {
                        "mineral": m.mineral,
                        "confidence": float(m.confidence),
                        "tier": m.tier,
                        "distance": float(m.spectral_distance),
                        "depth_m": float(m.depth_estimate_m) if m.depth_estimate_m else None
                    }
                    for m in matches
                ],
                "top_match": matches[0].mineral if matches else None
            }
        
        except Exception as e:
            logger.error(f"Processing failed: {e}")
            return {"error": str(e)}


def get_mineral_detector() -> MineralDetector:
    """Get or create mineral detector instance"""
    return MineralDetector()
