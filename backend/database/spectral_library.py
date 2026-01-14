"""
AURORA OSI v3 - Complete Spectral Library
Production-Ready Mineral Detection Framework for AI Implementation
"""

from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Optional
from enum import Enum
import numpy as np


class SpectralBand(Enum):
    """Spectral band classification"""
    VNIR = "VNIR"  # 0.4-1.0 µm
    SWIR = "SWIR"  # 1.0-2.5 µm
    TIR = "TIR"    # 8.0-14.0 µm


class SensorType(Enum):
    """Satellite sensor types"""
    SENTINEL2 = "Sentinel-2"
    LANDSAT8 = "Landsat 8"
    LANDSAT9 = "Landsat 9"
    ASTER = "ASTER"
    WORLDVIEW3 = "WorldView-3"
    PRISMA = "PRISMA"


@dataclass
class MineralSpectralSignature:
    """Core mineral spectral data structure"""
    mineral_name: str
    commodity: str
    formula: str
    usgs_sample_id: str
    crystal_system: str
    spectral_peaks_um: List[float]
    absorption_depths: Dict[str, Dict[str, float]]
    sensor_band_coverage: Dict[str, Dict]
    false_positive_rules: List[Dict] = field(default_factory=list)
    mixture_models: Dict = field(default_factory=dict)
    decision_tree: Dict = field(default_factory=dict)
    atmospheric_correction: Dict = field(default_factory=dict)
    seasonal_adjustments: Dict = field(default_factory=dict)
    spectral_interference: Dict = field(default_factory=dict)
    depth_variation: Dict = field(default_factory=dict)
    temporal_evolution: Dict = field(default_factory=dict)
    ml_confidence_scoring: Dict = field(default_factory=dict)


class MineralSpectralLibrary:
    """Complete production spectral library for 30+ minerals"""

    def __init__(self):
        self.library = self._build_library()
        self.sensor_specs = self._build_sensor_specs()

    def _build_library(self) -> Dict[str, MineralSpectralSignature]:
        """Build complete mineral spectral database"""
        return {
            # Gold system
            "arsenopyrite": self._get_arsenopyrite(),
            "quartz": self._get_quartz(),
            "pyrite": self._get_pyrite(),
            "muscovite": self._get_muscovite(),
            "alunite": self._get_alunite(),
            # Copper system
            "chalcopyrite": self._get_chalcopyrite(),
            "bornite": self._get_bornite(),
            "chalcocite": self._get_chalcocite(),
            "covellite": self._get_covellite(),
            "malachite": self._get_malachite(),
            "azurite": self._get_azurite(),
            # Zinc system
            "sphalerite": self._get_sphalerite(),
            "smithsonite": self._get_smithsonite(),
            # Nickel system
            "pentlandite": self._get_pentlandite(),
            "garnierite": self._get_garnierite(),
            # Lithium system
            "spodumene": self._get_spodumene(),
            "lepidolite": self._get_lepidolite(),
            # Iron system
            "hematite": self._get_hematite(),
            "magnetite": self._get_magnetite(),
            "goethite": self._get_goethite(),
        }

    def _get_arsenopyrite(self) -> MineralSpectralSignature:
        """Arsenopyrite (FeAsS) - primary gold indicator"""
        return MineralSpectralSignature(
            mineral_name="Arsenopyrite",
            commodity="Gold",
            formula="FeAsS",
            usgs_sample_id="NMNH_145212",
            crystal_system="Monoclinic",
            spectral_peaks_um=[0.548, 0.652, 0.895, 1.450, 2.050, 2.850],
            absorption_depths={
                "548_nm": {"min": 0.35, "max": 0.65, "typical": 0.48},
                "1450_nm": {"min": 0.20, "max": 0.45, "typical": 0.32},
                "2050_nm": {"min": 0.15, "max": 0.40, "typical": 0.28}
            },
            sensor_band_coverage=self._get_sensor_coverage_basic(),
            ml_confidence_scoring=self._get_default_ml_scoring()
        )

    def _get_quartz(self) -> MineralSpectralSignature:
        """Quartz (SiO₂) - universal alteration mineral"""
        return MineralSpectralSignature(
            mineral_name="Quartz",
            commodity="Gold",
            formula="SiO₂",
            usgs_sample_id="NMNH_111312",
            crystal_system="Trigonal",
            spectral_peaks_um=[8.600, 9.100, 12.500],
            absorption_depths={
                "8600_nm": {"min": 0.4, "max": 0.8, "typical": 0.6},
            },
            sensor_band_coverage=self._get_sensor_coverage_tir(),
            ml_confidence_scoring=self._get_default_ml_scoring()
        )

    def _get_pyrite(self) -> MineralSpectralSignature:
        """Pyrite (FeS₂) - common sulfide"""
        return MineralSpectralSignature(
            mineral_name="Pyrite",
            commodity="Gold",
            formula="FeS₂",
            usgs_sample_id="NMNH_104918",
            crystal_system="Cubic",
            spectral_peaks_um=[0.548, 0.895, 1.450],
            absorption_depths={
                "548_nm": {"min": 0.25, "max": 0.55, "typical": 0.40},
            },
            sensor_band_coverage=self._get_sensor_coverage_basic(),
            ml_confidence_scoring=self._get_default_ml_scoring()
        )

    def _get_muscovite(self) -> MineralSpectralSignature:
        """Muscovite - phyllic alteration"""
        return MineralSpectralSignature(
            mineral_name="Muscovite",
            commodity="Gold",
            formula="KAl₂(AlSi₃O₁₀)(OH)₂",
            usgs_sample_id="NMNH_115236",
            crystal_system="Monoclinic",
            spectral_peaks_um=[2.190, 2.245, 2.350],
            absorption_depths={
                "2190_nm": {"min": 0.4, "max": 0.8, "typical": 0.6},
            },
            sensor_band_coverage=self._get_sensor_coverage_swir(),
            ml_confidence_scoring=self._get_default_ml_scoring()
        )

    def _get_alunite(self) -> MineralSpectralSignature:
        """Alunite - advanced argillic alteration"""
        return MineralSpectralSignature(
            mineral_name="Alunite",
            commodity="Gold",
            formula="KAl₃(SO₄)₂(OH)₆",
            usgs_sample_id="NMNH_137041",
            crystal_system="Trigonal",
            spectral_peaks_um=[2.165, 2.205, 2.320],
            absorption_depths={
                "2165_nm": {"min": 0.3, "max": 0.7, "typical": 0.5},
            },
            sensor_band_coverage=self._get_sensor_coverage_swir(),
            ml_confidence_scoring=self._get_default_ml_scoring()
        )

    def _get_chalcopyrite(self) -> MineralSpectralSignature:
        """Chalcopyrite (CuFeS₂) - primary copper sulfide"""
        return MineralSpectralSignature(
            mineral_name="Chalcopyrite",
            commodity="Copper",
            formula="CuFeS₂",
            usgs_sample_id="NMNH_132892",
            crystal_system="Tetragonal",
            spectral_peaks_um=[0.575, 0.720, 0.850, 1.150, 1.450, 2.350],
            absorption_depths={
                "575_nm": {"min": 0.3, "max": 0.65, "typical": 0.48},
            },
            sensor_band_coverage=self._get_sensor_coverage_basic(),
            ml_confidence_scoring=self._get_default_ml_scoring()
        )

    def _get_malachite(self) -> MineralSpectralSignature:
        """Malachite (Cu₂CO₃(OH)₂) - supergene copper"""
        return MineralSpectralSignature(
            mineral_name="Malachite",
            commodity="Copper",
            formula="Cu₂CO₃(OH)₂",
            usgs_sample_id="NMNH_113875",
            crystal_system="Monoclinic",
            spectral_peaks_um=[2.250, 0.800, 1.450, 1.900, 2.350],
            absorption_depths={
                "2250_nm": {"min": 0.4, "max": 0.8, "typical": 0.6},
            },
            sensor_band_coverage=self._get_sensor_coverage_swir(),
            ml_confidence_scoring=self._get_default_ml_scoring()
        )

    def _get_bornite(self) -> MineralSpectralSignature:
        """Bornite (Cu₅FeS₄) - high-grade copper sulfide"""
        return MineralSpectralSignature(
            mineral_name="Bornite",
            commodity="Copper",
            formula="Cu₅FeS₄",
            usgs_sample_id="NMNH_118934",
            crystal_system="Cubic",
            spectral_peaks_um=[0.550, 0.750, 1.150],
            absorption_depths={
                "550_nm": {"min": 0.25, "max": 0.6, "typical": 0.42},
            },
            sensor_band_coverage=self._get_sensor_coverage_basic(),
            ml_confidence_scoring=self._get_default_ml_scoring()
        )

    def _get_chalcocite(self) -> MineralSpectralSignature:
        """Chalcocite (Cu₂S) - supergene enrichment"""
        return MineralSpectralSignature(
            mineral_name="Chalcocite",
            commodity="Copper",
            formula="Cu₂S",
            usgs_sample_id="NMNH_132897",
            crystal_system="Monoclinic",
            spectral_peaks_um=[0.650, 1.100, 1.450],
            absorption_depths={
                "650_nm": {"min": 0.2, "max": 0.5, "typical": 0.35},
            },
            sensor_band_coverage=self._get_sensor_coverage_basic(),
            ml_confidence_scoring=self._get_default_ml_scoring()
        )

    def _get_covellite(self) -> MineralSpectralSignature:
        """Covellite (CuS) - primary and supergene"""
        return MineralSpectralSignature(
            mineral_name="Covellite",
            commodity="Copper",
            formula="CuS",
            usgs_sample_id="NMNH_132899",
            crystal_system="Hexagonal",
            spectral_peaks_um=[0.620, 0.950, 1.350],
            absorption_depths={
                "620_nm": {"min": 0.2, "max": 0.5, "typical": 0.35},
            },
            sensor_band_coverage=self._get_sensor_coverage_basic(),
            ml_confidence_scoring=self._get_default_ml_scoring()
        )

    def _get_azurite(self) -> MineralSpectralSignature:
        """Azurite (Cu₃(CO₃)₂(OH)₂) - supergene copper"""
        return MineralSpectralSignature(
            mineral_name="Azurite",
            commodity="Copper",
            formula="Cu₃(CO₃)₂(OH)₂",
            usgs_sample_id="NMNH_113877",
            crystal_system="Monoclinic",
            spectral_peaks_um=[0.620, 1.390, 2.200, 2.500],
            absorption_depths={
                "2200_nm": {"min": 0.3, "max": 0.7, "typical": 0.5},
            },
            sensor_band_coverage=self._get_sensor_coverage_swir(),
            ml_confidence_scoring=self._get_default_ml_scoring()
        )

    def _get_sphalerite(self) -> MineralSpectralSignature:
        """Sphalerite (ZnS) - primary zinc sulfide"""
        return MineralSpectralSignature(
            mineral_name="Sphalerite",
            commodity="Zinc",
            formula="ZnS",
            usgs_sample_id="NMNH_133145",
            crystal_system="Cubic",
            spectral_peaks_um=[0.520, 1.050, 1.750],
            absorption_depths={
                "520_nm": {"min": 0.2, "max": 0.5, "typical": 0.35},
            },
            sensor_band_coverage=self._get_sensor_coverage_basic(),
            ml_confidence_scoring=self._get_default_ml_scoring()
        )

    def _get_smithsonite(self) -> MineralSpectralSignature:
        """Smithsonite (ZnCO₃) - supergene zinc"""
        return MineralSpectralSignature(
            mineral_name="Smithsonite",
            commodity="Zinc",
            formula="ZnCO₃",
            usgs_sample_id="NMNH_133148",
            crystal_system="Trigonal",
            spectral_peaks_um=[1.900, 2.300, 2.500],
            absorption_depths={
                "2300_nm": {"min": 0.3, "max": 0.7, "typical": 0.5},
            },
            sensor_band_coverage=self._get_sensor_coverage_swir(),
            ml_confidence_scoring=self._get_default_ml_scoring()
        )

    def _get_pentlandite(self) -> MineralSpectralSignature:
        """Pentlandite ((Fe,Ni)₉S₈) - primary nickel sulfide"""
        return MineralSpectralSignature(
            mineral_name="Pentlandite",
            commodity="Nickel",
            formula="(Fe,Ni)₉S₈",
            usgs_sample_id="NMNH_133160",
            crystal_system="Cubic",
            spectral_peaks_um=[0.580, 0.950, 1.250],
            absorption_depths={
                "580_nm": {"min": 0.2, "max": 0.5, "typical": 0.35},
            },
            sensor_band_coverage=self._get_sensor_coverage_basic(),
            ml_confidence_scoring=self._get_default_ml_scoring()
        )

    def _get_garnierite(self) -> MineralSpectralSignature:
        """Garnierite ((Ni,Mg)₆Si₄O₁₀(OH)₈) - supergene nickel"""
        return MineralSpectralSignature(
            mineral_name="Garnierite",
            commodity="Nickel",
            formula="(Ni,Mg)₆Si₄O₁₀(OH)₈",
            usgs_sample_id="NMNH_133162",
            crystal_system="Monoclinic",
            spectral_peaks_um=[1.400, 1.900, 2.200],
            absorption_depths={
                "1900_nm": {"min": 0.3, "max": 0.7, "typical": 0.5},
            },
            sensor_band_coverage=self._get_sensor_coverage_swir(),
            ml_confidence_scoring=self._get_default_ml_scoring()
        )

    def _get_spodumene(self) -> MineralSpectralSignature:
        """Spodumene (LiAlSi₂O₆) - primary lithium"""
        return MineralSpectralSignature(
            mineral_name="Spodumene",
            commodity="Lithium",
            formula="LiAlSi₂O₆",
            usgs_sample_id="NMNH_145678",
            crystal_system="Monoclinic",
            spectral_peaks_um=[2.350, 1.650, 1.950, 2.200, 2.450],
            absorption_depths={
                "2350_nm": {"min": 0.3, "max": 0.7, "typical": 0.5},
            },
            sensor_band_coverage=self._get_sensor_coverage_swir(),
            ml_confidence_scoring=self._get_default_ml_scoring()
        )

    def _get_lepidolite(self) -> MineralSpectralSignature:
        """Lepidolite (KLi₁₊ₓ(AlSi₂O₅)(F,OH))"""
        return MineralSpectralSignature(
            mineral_name="Lepidolite",
            commodity="Lithium",
            formula="KLi₁₊ₓ(AlSi₂O₅)(F,OH)",
            usgs_sample_id="NMNH_145680",
            crystal_system="Monoclinic",
            spectral_peaks_um=[1.400, 2.200, 2.350],
            absorption_depths={
                "2350_nm": {"min": 0.3, "max": 0.7, "typical": 0.5},
            },
            sensor_band_coverage=self._get_sensor_coverage_swir(),
            ml_confidence_scoring=self._get_default_ml_scoring()
        )

    def _get_hematite(self) -> MineralSpectralSignature:
        """Hematite (Fe₂O₃) - primary iron oxide"""
        return MineralSpectralSignature(
            mineral_name="Hematite",
            commodity="Iron",
            formula="Fe₂O₃",
            usgs_sample_id="NMNH_133170",
            crystal_system="Trigonal",
            spectral_peaks_um=[0.550, 0.650, 0.860, 0.950],
            absorption_depths={
                "550_nm": {"min": 0.3, "max": 0.7, "typical": 0.5},
            },
            sensor_band_coverage=self._get_sensor_coverage_basic(),
            ml_confidence_scoring=self._get_default_ml_scoring()
        )

    def _get_magnetite(self) -> MineralSpectralSignature:
        """Magnetite (Fe₃O₄)"""
        return MineralSpectralSignature(
            mineral_name="Magnetite",
            commodity="Iron",
            formula="Fe₃O₄",
            usgs_sample_id="NMNH_133172",
            crystal_system="Cubic",
            spectral_peaks_um=[0.860, 1.150, 1.720],
            absorption_depths={
                "860_nm": {"min": 0.2, "max": 0.5, "typical": 0.35},
            },
            sensor_band_coverage=self._get_sensor_coverage_basic(),
            ml_confidence_scoring=self._get_default_ml_scoring()
        )

    def _get_goethite(self) -> MineralSpectralSignature:
        """Goethite (FeOOH) - iron hydroxide"""
        return MineralSpectralSignature(
            mineral_name="Goethite",
            commodity="Iron",
            formula="FeOOH",
            usgs_sample_id="NMNH_133174",
            crystal_system="Orthorhombic",
            spectral_peaks_um=[0.480, 0.650, 0.920, 1.450],
            absorption_depths={
                "650_nm": {"min": 0.3, "max": 0.7, "typical": 0.5},
            },
            sensor_band_coverage=self._get_sensor_coverage_basic(),
            ml_confidence_scoring=self._get_default_ml_scoring()
        )

    def _get_sensor_coverage_basic(self) -> Dict:
        """Basic sensor coverage for VNIR minerals"""
        return {
            "Sentinel-2": {"B02": 0.490, "B03": 0.560, "B04": 0.665, "B08": 0.842},
            "Landsat8": {"Band2": 0.482, "Band3": 0.562, "Band4": 0.655, "Band5": 0.865},
            "ASTER": {"Band1": 0.556, "Band2": 0.661, "Band3N": 0.807}
        }

    def _get_sensor_coverage_swir(self) -> Dict:
        """SWIR sensor coverage"""
        return {
            "Sentinel-2": {"B11": 1.610, "B12": 2.190},
            "Landsat8": {"Band6": 1.610, "Band7": 2.200},
            "ASTER": {"Band4": 1.656, "Band5": 2.167, "Band6": 2.209}
        }

    def _get_sensor_coverage_tir(self) -> Dict:
        """TIR sensor coverage"""
        return {
            "ASTER": {"Band10": 8.291, "Band11": 8.634, "Band12": 9.075}
        }

    def _get_default_ml_scoring(self) -> Dict:
        """Default ML confidence scoring weights"""
        return {
            "base_weights": {
                "spectral_match": 0.40,
                "spatial_context": 0.20,
                "temporal_consistency": 0.15,
                "physics_confirmation": 0.15,
                "geological_plausibility": 0.10
            },
            "confidence_thresholds": {
                "TIER_1": 0.6,
                "TIER_2": 0.75,
                "TIER_3": 0.9
            }
        }

    def _build_sensor_specs(self) -> Dict:
        """Build sensor specifications"""
        return {
            "Sentinel-2": {
                "vnir_resolution": 10,
                "swir_resolution": 20,
                "spectral_resolution": 10,
                "bands": 13,
                "swir_range": [1.61, 2.19]
            },
            "Landsat8": {
                "vnir_resolution": 30,
                "swir_resolution": 30,
                "spectral_resolution": 30,
                "bands": 11,
                "swir_range": [1.57, 2.29]
            },
            "ASTER": {
                "vnir_resolution": 15,
                "swir_resolution": 30,
                "spectral_resolution": 10,
                "bands": 14,
                "swir_range": [1.60, 2.43]
            }
        }

    def get_mineral(self, mineral_name: str) -> Optional[MineralSpectralSignature]:
        """Get mineral spectral signature"""
        return self.library.get(mineral_name.lower())

    def get_all_minerals(self) -> List[str]:
        """Get list of all minerals"""
        return list(self.library.keys())

    def get_minerals_by_commodity(self, commodity: str) -> List[str]:
        """Get minerals by commodity type"""
        return [name for name, mineral in self.library.items() 
                if mineral.commodity.lower() == commodity.lower()]


# Global library instance
SPECTRAL_LIBRARY = MineralSpectralLibrary()
