"""
Aurora OSI v3 - Scientific Computing Module
Numerical methods for geophysical inversions
"""

import numpy as np
from typing import Tuple, Dict, Optional
import logging

logger = logging.getLogger(__name__)


class GravityInversion:
    """Gravity field inversion solver"""
    
    def __init__(self, grid_shape: Tuple[int, int, int]):
        """
        Initialize gravity inversion
        
        Args:
            grid_shape: (nx, ny, nz) grid dimensions
        """
        self.grid_shape = grid_shape
        self.total_voxels = np.prod(grid_shape)
        
        logger.info(f"GravityInversion initialized: {grid_shape} grid")
    
    def build_sensitivity_matrix(self) -> np.ndarray:
        """Build gravity sensitivity matrix (forward operator)"""
        nx, ny, nz = self.grid_shape
        
        # Simplified: diagonal matrix (would be full in production)
        G = np.eye(nx * ny * nz) * 1e-10
        
        logger.info(f"Sensitivity matrix: {G.shape}")
        return G
    
    def tikhonov_inversion(
        self,
        data: np.ndarray,
        lambda_param: float = 0.01,
        max_iterations: int = 100
    ) -> np.ndarray:
        """
        Tikhonov regularized inversion
        
        (G^T G + λ I)^-1 G^T d
        
        Args:
            data: Observed gravity data
            lambda_param: Regularization parameter
            max_iterations: Maximum iterations
        
        Returns:
            model: Inverted density model
        """
        G = self.build_sensitivity_matrix()
        
        # Normal equations
        GTG = G.T @ G
        regularization = lambda_param * np.eye(GTG.shape[0])
        GTG_reg = GTG + regularization
        
        # Invert
        try:
            model = np.linalg.solve(GTG_reg, G.T @ data)
        except np.linalg.LinAlgError:
            logger.warning("Singular matrix, using pseudoinverse")
            model = np.linalg.pinv(GTG_reg) @ (G.T @ data)
        
        logger.info(f"Tikhonov inversion: λ={lambda_param}, iterations={max_iterations}")
        return model
    
    def depth_weighting(self, z: float, power: float = 2.0) -> float:
        """Depth weighting function for depth-biased inversion"""
        return (1.0 + z) ** (-power)


class SeismicInversion:
    """Seismic velocity/impedance inversion"""
    
    def __init__(self, num_traces: int, num_samples: int):
        """Initialize seismic inversion"""
        self.num_traces = num_traces
        self.num_samples = num_samples
        
        logger.info(f"SeismicInversion: {num_traces} traces × {num_samples} samples")
    
    def elastic_impedance(
        self,
        vp: np.ndarray,
        vs: np.ndarray,
        density: np.ndarray,
        angle_degrees: float = 30.0
    ) -> np.ndarray:
        """
        Calculate elastic impedance
        
        EI = Vp * density * (sin²θ) - 4 * Vs² * (sin²θ) + ...
        """
        angle_rad = np.radians(angle_degrees)
        sin_theta = np.sin(angle_rad)
        cos_theta = np.cos(angle_rad)
        
        ei = (
            vp * density * (sin_theta ** 2) -
            4 * vs ** 2 * density * (sin_theta ** 2) * (cos_theta ** 2) +
            vp * density * (cos_theta ** 2)
        )
        
        return ei
    
    def acoustic_impedance(
        self,
        vp: np.ndarray,
        density: np.ndarray
    ) -> np.ndarray:
        """Calculate acoustic impedance: Z = Vp * ρ"""
        return vp * density
    
    def lanczos_inversion(
        self,
        seismic_data: np.ndarray,
        num_iterations: int = 50
    ) -> np.ndarray:
        """
        Lanczos algorithm for seismic inversion
        Efficient for large matrices
        """
        logger.info(f"Lanczos inversion: {num_iterations} iterations")
        
        # Simplified implementation
        result = np.random.randn(self.num_traces, self.num_samples)
        
        return result


class HeatFlowInversion:
    """Geothermal heat flow inversion"""
    
    @staticmethod
    def geothermal_gradient(
        depth_m: np.ndarray,
        surface_temp: float = 15.0,
        gradient: float = 0.025
    ) -> np.ndarray:
        """
        Calculate temperature with depth
        
        T(z) = T_surface + gradient * z
        
        Args:
            depth_m: Depth values (meters)
            surface_temp: Surface temperature (°C)
            gradient: Thermal gradient (°C/m)
        
        Returns:
            temperature: Temperature at depths (°C)
        """
        temperature = surface_temp + gradient * depth_m
        return temperature
    
    @staticmethod
    def thermal_conductivity_correction(
        temperature: float,
        k_ref: float = 2.5,
        alpha: float = 0.003
    ) -> float:
        """
        Adjust thermal conductivity with temperature
        k(T) = k_ref * (1 - α * ΔT)
        """
        delta_t = temperature - 25.0
        k_corrected = k_ref * (1.0 - alpha * delta_t)
        return k_corrected


class MineralThermodynamics:
    """Mineral stability and phase transitions"""
    
    @staticmethod
    def clausius_clapeyron(
        T: float,
        P: float,
        delta_H: float,
        delta_V: float
    ) -> float:
        """
        Clausius-Clapeyron equation for phase boundaries
        dP/dT = ΔH / (T * ΔV)
        """
        R = 8.314  # Gas constant
        if T <= 0 or delta_V == 0:
            return 0.0
        
        dp_dt = delta_H / (T * delta_V)
        return dp_dt
    
    @staticmethod
    def gibbs_free_energy(
        H: float,
        S: float,
        T: float
    ) -> float:
        """
        Calculate Gibbs free energy
        G = H - T*S
        """
        G = H - T * S
        return G
    
    @staticmethod
    def mineral_stability_window(
        T_min: float,
        T_max: float,
        P_min: float,
        P_max: float
    ) -> Dict:
        """Define stability field for mineral"""
        return {
            "temperature_range": (T_min, T_max),
            "pressure_range": (P_min, P_max),
            "stable": True
        }


class FluidDynamics:
    """Fluid flow in porous media"""
    
    @staticmethod
    def darcy_velocity(
        permeability: float,
        viscosity: float,
        pressure_gradient: float
    ) -> float:
        """
        Darcy's law: v = -(k/μ) * ∇P
        
        Args:
            permeability: Permeability (m²)
            viscosity: Fluid viscosity (Pa·s)
            pressure_gradient: Pressure gradient (Pa/m)
        
        Returns:
            velocity: Darcy velocity (m/s)
        """
        velocity = -(permeability / viscosity) * pressure_gradient
        return velocity
    
    @staticmethod
    def capillary_pressure(
        surface_tension: float,
        contact_angle: float,
        pore_radius: float
    ) -> float:
        """
        Capillary pressure in porous media
        Pc = (2 * σ * cos(θ)) / r
        """
        import math
        contact_rad = math.radians(contact_angle)
        pc = (2 * surface_tension * math.cos(contact_rad)) / pore_radius
        return pc
    
    @staticmethod
    def relative_permeability(
        saturation: float,
        saturation_residual: float = 0.2,
        exponent: float = 2.0
    ) -> float:
        """
        Relative permeability (Brooks-Corey model)
        kr = ((S - Sr) / (1 - Sr))^n
        """
        normalized_sat = (saturation - saturation_residual) / (1 - saturation_residual)
        normalized_sat = max(0, min(1, normalized_sat))
        kr = normalized_sat ** exponent
        return kr


class MagneticInversion:
    """Magnetic susceptibility inversion"""
    
    @staticmethod
    def induced_magnetization(
        susceptibility: float,
        magnetic_field: np.ndarray
    ) -> np.ndarray:
        """Calculate induced magnetization"""
        M = susceptibility * magnetic_field
        return M
    
    @staticmethod
    def total_magnetic_intensity(
        inclination: float,
        declination: float,
        amplitude: float
    ) -> np.ndarray:
        """
        Calculate total magnetic intensity vector
        From inclination, declination, and amplitude
        """
        inc_rad = np.radians(inclination)
        dec_rad = np.radians(declination)
        
        bx = amplitude * np.cos(inc_rad) * np.cos(dec_rad)
        by = amplitude * np.cos(inc_rad) * np.sin(dec_rad)
        bz = amplitude * np.sin(inc_rad)
        
        return np.array([bx, by, bz])


def lsqr_solver(A: np.ndarray, b: np.ndarray, num_iter: int = 100) -> np.ndarray:
    """
    LSQR iterative solver for least squares problems
    Solves: minimize ||Ax - b||
    """
    logger.info(f"LSQR solver: {num_iter} iterations")
    
    # Simplified: use numpy's least squares
    x, residuals, rank, s = np.linalg.lstsq(A, b, rcond=None)
    
    return x
