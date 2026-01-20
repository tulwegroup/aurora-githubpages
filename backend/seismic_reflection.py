"""
Aurora OSI v3 - Seismic Reflection Processor
2D/3D seismic interpretation for HC exploration (onshore sedimentary basins)
Integrates with Ground Truth Vault for Voltaian Basin analysis
"""

import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class SeismicReflectionSignature:
    """2D seismic reflection signature for HC systems"""
    line_id: str
    location: Tuple[float, float]  # (latitude, longitude)
    seismic_attributes: Dict
    interpreted_horizons: List[Dict]
    amplitude_anomalies: List[Dict]
    velocity_inversion_zones: List[Dict]
    predicted_hc_system: Optional[Dict] = None


class SeismicReflectionLibrary:
    """Seismic reflection signatures for onshore basin HC systems"""
    
    def __init__(self):
        self.voltaian_basin_signatures = self._build_voltaian_signatures()
        logger.info(f"Loaded Voltaian Basin seismic library: {len(self.voltaian_basin_signatures)} patterns")
    
    def _build_voltaian_signatures(self) -> Dict:
        """Build seismic reflection patterns for Voltaian Basin onshore HC"""
        return {
            "bright_spot_shallow": {
                "description": "Bright amplitude anomaly in shallow syn-rift sequences",
                "depth_range_m": (500, 2000),
                "amplitude_threshold": 0.5,  # Normalized amplitude
                "frequency_range_hz": (5, 15),
                "hc_probability": 0.75,
                "hydrocarbon_type": ["crude_oil", "natural_gas_shallow"],
                "geological_context": "Shallow terrigenous sand bodies in permian sequences"
            },
            "dim_spot_mid_depth": {
                "description": "Dim amplitude zone in mid-depth reflection",
                "depth_range_m": (2000, 3500),
                "amplitude_threshold": 0.2,
                "frequency_range_hz": (8, 25),
                "hc_probability": 0.65,
                "hydrocarbon_type": ["crude_oil_moderate"],
                "geological_context": "Fractured basement or dolomite reservoirs"
            },
            "velocity_pull_down": {
                "description": "Vertical velocity decrease below low-impedance zone",
                "depth_range_m": (1500, 3000),
                "velocity_anomaly_percent": (-5, -15),  # % decrease
                "hc_probability": 0.80,
                "hydrocarbon_type": ["natural_gas", "crude_oil"],
                "geological_context": "Gas-filled pore spaces causing velocity reduction"
            },
            "flat_spot": {
                "description": "Horizontal termination of dipping reflections",
                "depth_range_m": (1000, 3500),
                "dip_angle_degrees": 15,  # Dip angle of surrounding reflections
                "flatspot_sharpness": 0.8,  # 0-1 scale
                "hc_probability": 0.85,
                "hydrocarbon_type": ["crude_oil", "brine"],
                "geological_context": "Fluid contact - oil-water or gas-oil interface"
            },
            "push_down_effect": {
                "description": "Deepening of reflections below low-velocity zone",
                "depth_range_m": (800, 2500),
                "reflection_depth_increase_percent": 5,
                "hc_probability": 0.70,
                "hydrocarbon_type": ["natural_gas"],
                "geological_context": "Gas-charged sand above seal layer"
            },
            "anticline_crest": {
                "description": "Structural closure in upwarped reflections",
                "depth_range_m": (1500, 4000),
                "closure_area_km2": (50, 500),
                "relief_m": (100, 1000),
                "hc_probability": 0.75,
                "hydrocarbon_type": ["crude_oil", "natural_gas"],
                "geological_context": "Structural trap - primary HC accumulation mechanism"
            }
        }
    
    def interpret_seismic_line(
        self,
        line_id: str,
        location: Tuple[float, float],
        seismic_data: Dict,
        rp_start: int,
        rp_end: int,
        line_length_km: float
    ) -> SeismicReflectionSignature:
        """
        Interpret a seismic reflection line for HC potential
        
        Args:
            line_id: GNPC line identifier (e.g., 'VB-101A')
            location: (lat, lon) of line midpoint
            seismic_data: Processed seismic cube data
            rp_start, rp_end: Record point range
            line_length_km: Total line length
        
        Returns:
            SeismicReflectionSignature with HC interpretation
        """
        signature = SeismicReflectionSignature(
            line_id=line_id,
            location=location,
            seismic_attributes=self._calculate_seismic_attributes(seismic_data),
            interpreted_horizons=self._interpret_horizons(seismic_data),
            amplitude_anomalies=self._detect_amplitude_anomalies(seismic_data),
            velocity_inversion_zones=self._detect_velocity_inversions(seismic_data)
        )
        
        # Predict HC system from detected patterns
        signature.predicted_hc_system = self._predict_hc_system(signature)
        
        logger.info(
            f"Line {line_id}: {len(signature.amplitude_anomalies)} amplitude anomalies, "
            f"HC probability: {signature.predicted_hc_system['overall_probability']:.2%}"
        )
        
        return signature
    
    def _calculate_seismic_attributes(self, seismic_data: Dict) -> Dict:
        """Calculate seismic attributes for interpretation"""
        return {
            "mean_amplitude": seismic_data.get("mean_amplitude", 0.0),
            "rms_amplitude": seismic_data.get("rms_amplitude", 0.0),
            "dominant_frequency_hz": seismic_data.get("dominant_frequency", 15),
            "average_velocity_m_per_s": seismic_data.get("velocity", 3000),
            "impedance_contrast": seismic_data.get("impedance_contrast", 0.0),
            "signal_to_noise_ratio": seismic_data.get("snr", 8.0)
        }
    
    def _interpret_horizons(self, seismic_data: Dict) -> List[Dict]:
        """Interpret key stratigraphic horizons"""
        horizons = []
        
        # Common Voltaian Basin horizons
        horizon_names = [
            {"name": "Recent", "depth_m": 0},
            {"name": "Quaternary", "depth_m": 100},
            {"name": "Permian Top", "depth_m": 500},
            {"name": "Permian Mid", "depth_m": 1500},
            {"name": "Permian Base", "depth_m": 2500},
            {"name": "Basement Reflections", "depth_m": 3500}
        ]
        
        for horizon in horizon_names:
            horizons.append({
                "name": horizon["name"],
                "depth_m": horizon["depth_m"],
                "amplitude_strength": np.random.uniform(0.3, 0.9),
                "continuity": np.random.uniform(0.7, 0.95),
                "interpretation_confidence": np.random.uniform(0.75, 0.95)
            })
        
        return horizons
    
    def _detect_amplitude_anomalies(self, seismic_data: Dict) -> List[Dict]:
        """Detect bright/dim spot and other amplitude anomalies"""
        anomalies = []
        
        # Simulate detection of HC-related amplitude anomalies
        mean_amp = seismic_data.get("mean_amplitude", 0.5)
        
        for pattern_name, pattern_spec in self.voltaian_basin_signatures.items():
            if pattern_name in ["bright_spot_shallow", "dim_spot_mid_depth"]:
                # Generate synthetic anomalies
                detected_amplitude = np.random.normal(mean_amp, 0.15)
                
                if abs(detected_amplitude - pattern_spec["amplitude_threshold"]) < 0.3:
                    anomalies.append({
                        "pattern": pattern_name,
                        "depth_m": np.random.randint(*pattern_spec["depth_range_m"]),
                        "amplitude": detected_amplitude,
                        "lateral_extent_m": np.random.randint(50, 500),
                        "hc_probability": pattern_spec["hc_probability"],
                        "geological_interpretation": pattern_spec["geological_context"]
                    })
        
        return anomalies
    
    def _detect_velocity_inversions(self, seismic_data: Dict) -> List[Dict]:
        """Detect velocity pull-down and other velocity anomalies"""
        inversions = []
        
        # Velocity inversions typically indicate gas-charged zones
        base_velocity = seismic_data.get("velocity", 3000)
        
        # Simulate velocity inversion zones
        for i in range(2):
            anomaly_depth = 1500 + (i * 1000)
            anomaly_velocity = base_velocity * np.random.uniform(0.90, 0.98)
            
            inversions.append({
                "depth_m": anomaly_depth,
                "base_velocity_m_per_s": base_velocity,
                "anomaly_velocity_m_per_s": anomaly_velocity,
                "velocity_reduction_percent": ((base_velocity - anomaly_velocity) / base_velocity) * 100,
                "lateral_extent_m": np.random.randint(200, 2000),
                "hc_probability": 0.75,
                "interpreted_fluid": "natural_gas"
            })
        
        return inversions
    
    def _predict_hc_system(self, signature: SeismicReflectionSignature) -> Dict:
        """Predict HC system from seismic signatures"""
        probabilities = []
        hc_types_detected = set()
        
        # Source rock indicators
        for horizon in signature.interpreted_horizons:
            if "Permian" in horizon["name"]:
                probabilities.append(0.60)  # Permian typically HC-rich in Voltaian
        
        # Structural trap indicators
        if len(signature.amplitude_anomalies) > 0:
            avg_anomaly_prob = np.mean([a["hc_probability"] for a in signature.amplitude_anomalies])
            probabilities.append(avg_anomaly_prob)
            
            for anomaly in signature.amplitude_anomalies:
                hc_types_detected.update(anomaly.get("geology_context", ["crude_oil"]))
        
        # Velocity inversion indicators
        if len(signature.velocity_inversion_zones) > 0:
            velocity_prob = 0.70  # Velocity inversions = gas presence
            probabilities.append(velocity_prob)
            hc_types_detected.add("natural_gas")
        
        overall_prob = np.mean(probabilities) if probabilities else 0.30
        
        return {
            "overall_probability": overall_prob,
            "confidence_level": "HIGH" if overall_prob > 0.70 else "MODERATE" if overall_prob > 0.50 else "LOW",
            "hc_types": list(hc_types_detected) or ["crude_oil", "natural_gas"],
            "primary_hc_system": "Oil and Gas" if overall_prob > 0.65 else "Gas-prone" if "natural_gas" in hc_types_detected else "Oil-prone",
            "structural_traps": len([a for a in signature.amplitude_anomalies if "bright" in a.get("pattern", "")]),
            "stratigraphic_traps": len([a for a in signature.amplitude_anomalies if "dim" in a.get("pattern", "")]),
            "recommendation": "DRILL" if overall_prob > 0.70 else "ACQUIRE_MORE_DATA" if overall_prob > 0.50 else "NOT_RECOMMENDED"
        }


# GNPC Voltaian Basin 2D Seismic Survey Data
GNPC_VOLTAIAN_SEISMIC_SURVEY = {
    "survey_name": "GNPC Voltaian Basin 2D Seismic Survey",
    "year_acquired": 2015,
    "total_length_km": 1871.2,
    "basin": "Voltaian Basin",
    "country": "Ghana",
    "lines": {
        "VB-101A": {"rp_start": 40002, "rp_end": 60208, "length_km": 252.650, "lat": 9.25, "lon": -1.55},
        "VB-101B": {"rp_start": 30002, "rp_end": 33828, "length_km": 47.900, "lat": 9.24, "lon": -1.53},
        "VB-101C": {"rp_start": 20002, "rp_end": 24864, "length_km": 60.850, "lat": 9.23, "lon": -1.51},
        "VB-102": {"rp_start": 20002, "rp_end": 33780, "length_km": 172.300, "lat": 9.18, "lon": -1.48},
        "VB-103A": {"rp_start": 40002, "rp_end": 55020, "length_km": 187.800, "lat": 9.17, "lon": -1.50},
        "VB-103B": {"rp_start": 20002, "rp_end": 35636, "length_km": 195.500, "lat": 9.16, "lon": -1.49},
        "VB-106": {"rp_start": 20002, "rp_end": 30968, "length_km": 137.150, "lat": 9.14, "lon": -1.52},
        "VB-108": {"rp_start": 20002, "rp_end": 35988, "length_km": 199.900, "lat": 9.13, "lon": -1.50},
        "VB-110": {"rp_start": 20002, "rp_end": 35032, "length_km": 187.950, "lat": 9.12, "lon": -1.51},
        "VB-104": {"rp_start": 20002, "rp_end": 26126, "length_km": 76.600, "lat": 9.15, "lon": -1.49},
        "VB-106-E": {"rp_start": 30906, "rp_end": 30968, "length_km": 0.8, "lat": 9.14, "lon": -1.52},
        "VB-101B-N": {"rp_start": 33830, "rp_end": 33896, "length_km": 0.850, "lat": 9.24, "lon": -1.53},
        "VB-110-E": {"rp_start": 35034, "rp_end": 35580, "length_km": 6.850, "lat": 9.12, "lon": -1.51},
        "VB-105": {"rp_start": 15622, "rp_end": 26748, "length_km": 136.300, "lat": 9.14, "lon": -1.48},
        "VB-107": {"rp_start": 20002, "rp_end": 27708, "length_km": 96.400, "lat": 9.13, "lon": -1.49},
        "VB-112": {"rp_start": 20002, "rp_end": 29036, "length_km": 113.000, "lat": 9.11, "lon": -1.50},
    }
}
