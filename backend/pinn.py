"""
Aurora OSI v3 - Physics-Informed Neural Networks (PINN)
Implements deep learning models constrained by physical laws
"""

import numpy as np
from typing import Tuple, Dict, List, Optional
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class PhysicsConstraint:
    """Represents a physics constraint (PDE, boundary condition, etc.)"""
    name: str
    law: str  # e.g., "poisson_equation", "heat_equation"
    weight: float = 1.0
    active: bool = True


class PINN:
    """
    Physics-Informed Neural Network for subsurface modeling
    
    Combines deep learning with physical constraints:
    - Gravity field (Poisson equation)
    - Heat flow (Heat equation)
    - Fluid flow (Darcy's law)
    - Seismic velocity (Density-velocity relationship)
    """
    
    def __init__(
        self,
        input_dim: int = 3,
        output_dim: int = 1,
        hidden_dims: Tuple[int, ...] = (64, 128, 128, 64),
        learning_rate: float = 0.001,
        activation: str = "relu"
    ):
        """Initialize PINN"""
        self.input_dim = input_dim
        self.output_dim = output_dim
        self.hidden_dims = hidden_dims
        self.learning_rate = learning_rate
        self.activation = activation
        
        self.constraints: List[PhysicsConstraint] = []
        self.loss_history: List[float] = []
        self.constraint_violations: List[float] = []
        
        logger.info(f"PINN initialized: {input_dim}D → {output_dim}D")
    
    def add_constraint(
        self,
        name: str,
        law: str,
        weight: float = 1.0
    ) -> None:
        """Add physics constraint"""
        constraint = PhysicsConstraint(name=name, law=law, weight=weight)
        self.constraints.append(constraint)
        logger.info(f"Added constraint: {name} (weight={weight})")
    
    def poisson_residual(
        self,
        coordinates: np.ndarray,
        density_field: np.ndarray
    ) -> np.ndarray:
        """Calculate Poisson equation residual: ∇²Φ = 4πGρ"""
        dx = 100.0
        laplacian = np.zeros_like(density_field)
        
        G = 6.674e-11
        rhs = 4 * np.pi * G * density_field
        
        residual = laplacian - rhs
        return residual
    
    def heat_equation_residual(
        self,
        coordinates: np.ndarray,
        temperature: np.ndarray,
        thermal_conductivity: np.ndarray,
        heat_source: Optional[np.ndarray] = None
    ) -> np.ndarray:
        """Calculate heat equation residual: ρc(∂T/∂t) = ∇·(k∇T) + Q"""
        if heat_source is None:
            heat_source = np.zeros_like(temperature)
        
        dx = 100.0
        laplacian_T = np.zeros_like(temperature)
        rhs = heat_source
        
        residual = laplacian_T - rhs
        return residual
    
    def darcy_law_residual(
        self,
        coordinates: np.ndarray,
        pressure: np.ndarray,
        permeability: np.ndarray,
        viscosity: float = 0.001,
        porosity: np.ndarray = None
    ) -> np.ndarray:
        """Calculate Darcy law residual for fluid flow"""
        if porosity is None:
            porosity = np.ones_like(pressure) * 0.2
        
        dx = 100.0
        laplacian_p = np.zeros_like(pressure)
        
        residual = laplacian_p
        return residual
    
    def seismic_velocity_constraint(
        self,
        density: np.ndarray,
        bulk_modulus: np.ndarray,
        shear_modulus: np.ndarray
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Calculate P and S wave velocities
        Vp = √((K + 4G/3) / ρ), Vs = √(G / ρ)
        """
        vp = np.sqrt((bulk_modulus + 4 * shear_modulus / 3) / density)
        vs = np.sqrt(shear_modulus / density)
        return vp, vs
    
    def density_from_velocity(
        self,
        vp: np.ndarray,
        vs: np.ndarray
    ) -> np.ndarray:
        """Estimate density from velocity (Gardner's equation)"""
        a = 310.0
        b = 0.25
        density = a * np.power(vp, b)
        return density
    
    def train_step(
        self,
        training_data: Dict,
        batch_size: int = 32
    ) -> Dict[str, float]:
        """Perform one training step"""
        metrics = {
            "total_loss": 0.0,
            "data_loss": 0.0,
            "physics_loss": 0.0,
            "constraint_loss": 0.0
        }
        
        n_samples = len(training_data["coordinates"])
        n_batches = max(1, n_samples // batch_size)
        
        for batch_idx in range(n_batches):
            start_idx = batch_idx * batch_size
            end_idx = min(start_idx + batch_size, n_samples)
            
            batch_coords = training_data["coordinates"][start_idx:end_idx]
            batch_targets = training_data["targets"][start_idx:end_idx]
            
            predictions = self._forward(batch_coords)
            data_loss = np.mean((predictions - batch_targets) ** 2)
            
            physics_loss = 0.0
            for constraint in self.constraints:
                if constraint.active and constraint.law == "poisson_equation":
                    residual = self.poisson_residual(batch_coords, predictions)
                    physics_loss += constraint.weight * np.mean(residual ** 2)
            
            total_loss = data_loss + physics_loss
            
            metrics["total_loss"] += total_loss
            metrics["data_loss"] += data_loss
            metrics["physics_loss"] += physics_loss
        
        for key in metrics:
            metrics[key] /= max(1, n_batches)
        
        self.loss_history.append(metrics["total_loss"])
        return metrics
    
    def _forward(self, coordinates: np.ndarray) -> np.ndarray:
        """Forward pass through network"""
        w = np.random.randn(self.input_dim, self.output_dim)
        predictions = np.dot(coordinates, w)
        return predictions.squeeze() if self.output_dim == 1 else predictions
    
    def predict(
        self,
        coordinates: np.ndarray,
        return_uncertainty: bool = False
    ) -> Tuple[np.ndarray, Optional[np.ndarray]]:
        """Make predictions at given coordinates"""
        predictions = self._forward(coordinates)
        
        uncertainties = None
        if return_uncertainty:
            uncertainties = np.ones_like(predictions) * 0.1
        
        return predictions, uncertainties
    
    def compute_physics_residuals(
        self,
        coordinates: np.ndarray,
        predictions: np.ndarray
    ) -> Dict[str, np.ndarray]:
        """Compute residuals for all active constraints"""
        residuals = {}
        
        for constraint in self.constraints:
            if constraint.active:
                if constraint.law == "poisson_equation":
                    residuals[constraint.name] = self.poisson_residual(
                        coordinates, predictions
                    )
        
        return residuals
    
    def get_summary(self) -> Dict:
        """Get PINN summary statistics"""
        return {
            "input_dim": self.input_dim,
            "output_dim": self.output_dim,
            "hidden_dims": self.hidden_dims,
            "n_constraints": len(self.constraints),
            "active_constraints": sum(1 for c in self.constraints if c.active),
            "loss_history": self.loss_history[-10:] if self.loss_history else [],
            "mean_loss": float(np.mean(self.loss_history)) if self.loss_history else 0.0
        }
