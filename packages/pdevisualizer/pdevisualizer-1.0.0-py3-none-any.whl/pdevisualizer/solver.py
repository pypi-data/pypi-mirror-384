"""
Unified API for PDE solving and visualization.

This module provides a clean, professional interface for solving different types
of PDEs with flexible boundary conditions and initial conditions.
"""

import numpy as np
from typing import Optional, Union, Dict, Any, Tuple, List, Sequence
from enum import Enum
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation

# Import our existing solvers
from .heat2d import solve_heat, animate_heat, step_heat
from .wave2d import solve_wave, animate_wave, step_wave, step_wave_first
from .wave2d import create_gaussian_pulse, create_circular_wave
from .boundary_conditions import (
    BoundarySpec, solve_heat_with_boundaries, solve_wave_with_boundaries,
    BoundaryType  # Use the enum from boundary_conditions
)


class EquationType(Enum):
    """Supported PDE types."""
    HEAT = "heat"
    WAVE = "wave"

# BoundaryType is imported from boundary_conditions module (for wave equation)


class BoundaryCondition:
    """Boundary condition specification - Enhanced version."""
    
    def __init__(self, boundary_type: BoundaryType, value: float = 0.0):
        self.type = boundary_type
        self.value = value
    
    @classmethod
    def dirichlet(cls, value: float = 0.0):
        """Fixed value boundary condition."""
        return cls(BoundaryType.DIRICHLET, value)
    
    @classmethod
    def neumann(cls, flux: float = 0.0):
        """Fixed flux boundary condition (insulated if flux=0)."""
        return cls(BoundaryType.NEUMANN, flux)
    
    @classmethod
    def periodic(cls):
        """Periodic boundary condition."""
        return cls(BoundaryType.PERIODIC)
    
    @classmethod
    def absorbing(cls):
        """Absorbing boundary condition (for waves)."""
        return cls(BoundaryType.ABSORBING)
    
    def to_boundary_spec(self):
        """Convert to BoundarySpec for the boundary_conditions module."""
        return BoundarySpec.uniform(self.type, self.value)


class InitialConditions:
    """Helper class for creating common initial conditions."""
    
    @staticmethod
    def zeros(shape: Tuple[int, int]) -> np.ndarray:
        """Zero initial condition."""
        return np.zeros(shape)
    
    @staticmethod
    def constant(shape: Tuple[int, int], value: float) -> np.ndarray:
        """Constant field initial condition."""
        return np.full(shape, value)
    
    @staticmethod
    def gaussian_pulse(shape: Tuple[int, int], center: Tuple[float, float], 
                      sigma: float, amplitude: float = 1.0) -> np.ndarray:
        """Gaussian pulse initial condition."""
        if isinstance(shape, int):
            nx = ny = shape
        else:
            nx, ny = shape
        return create_gaussian_pulse((nx, ny), center, sigma, amplitude)
    
    @staticmethod
    def circular_wave(shape: Tuple[int, int], center: Tuple[float, float],
                     radius: float, amplitude: float = 1.0) -> np.ndarray:
        """Circular wave initial condition."""
        if isinstance(shape, int):
            nx = ny = shape
        else:
            nx, ny = shape
        return create_circular_wave((nx, ny), center, radius, amplitude)
    
    @staticmethod
    def multiple_sources(shape: Tuple[int, int], sources) -> np.ndarray:
        """Multiple point sources initial condition.
        
        Parameters:
        -----------
        shape : tuple
            Grid shape (nx, ny)
        sources : list
            List of (x, y, amplitude) tuples for source locations
        """
        u0 = np.zeros(shape)
        for x, y, amplitude in sources:
            if 0 <= x < shape[0] and 0 <= y < shape[1]:
                u0[int(x), int(y)] = amplitude
        return u0
    
    @staticmethod
    def sine_wave(shape: Tuple[int, int], wavelength: float, 
                  amplitude: float = 1.0, direction: str = 'x') -> np.ndarray:
        """Sinusoidal wave initial condition.
        
        Parameters:
        -----------
        shape : tuple
            Grid shape (nx, ny)
        wavelength : float
            Wavelength in grid units
        amplitude : float
            Wave amplitude
        direction : str
            Wave direction ('x', 'y', or 'diagonal')
        """
        nx, ny = shape
        x = np.linspace(0, nx-1, nx)
        y = np.linspace(0, ny-1, ny)
        X, Y = np.meshgrid(x, y, indexing='ij')
        
        if direction == 'x':
            return amplitude * np.sin(2 * np.pi * X / wavelength)
        elif direction == 'y':
            return amplitude * np.sin(2 * np.pi * Y / wavelength)
        elif direction == 'diagonal':
            return amplitude * np.sin(2 * np.pi * (X + Y) / (wavelength * np.sqrt(2)))
        else:
            raise ValueError("direction must be 'x', 'y', or 'diagonal'")


class PDESolver:
    """
    Unified interface for solving 2D partial differential equations.
    
    This class provides a clean, professional API for solving heat and wave
    equations with flexible boundary conditions and initial conditions.
    """
    
    def __init__(self, equation: Union[str, EquationType], 
                 grid_shape: Tuple[int, int] = (100, 100),
                 spacing: Tuple[float, float] = (1.0, 1.0),
                 boundary: Optional[BoundaryCondition] = None):
        """
        Initialize the PDE solver.
        
        Parameters:
        -----------
        equation : str or EquationType
            Type of PDE to solve ('heat' or 'wave')
        grid_shape : tuple
            Grid dimensions (nx, ny)
        spacing : tuple
            Grid spacing (dx, dy)
        boundary : BoundaryCondition, optional
            Boundary condition (default: Dirichlet with value=0)
        """
        # Handle string input
        if isinstance(equation, str):
            equation = EquationType(equation.lower())
        
        self.equation = equation
        self.grid_shape = grid_shape
        self.dx, self.dy = spacing
        
        # Default boundary condition
        if boundary is None:
            boundary = BoundaryCondition.dirichlet(0.0)
        self.boundary = boundary
        
        # PDE-specific parameters
        self.parameters = {}
        self._initial_conditions = None
        self._initial_velocity = None
        
        # Set default parameters
        if self.equation == EquationType.HEAT:
            self.parameters = {'alpha': 1.0, 'dt': 0.1}
        elif self.equation == EquationType.WAVE:
            self.parameters = {'c': 1.0, 'dt': 0.05}
    
    def set_initial_conditions(self, u0: np.ndarray, v0: Optional[np.ndarray] = None):
        """
        Set initial conditions for the PDE.
        
        Parameters:
        -----------
        u0 : numpy.ndarray
            Initial field (temperature for heat, amplitude for wave)
        v0 : numpy.ndarray, optional
            Initial velocity (for wave equation only)
        """
        if u0.shape != self.grid_shape:
            raise ValueError(f"Initial condition shape {u0.shape} doesn't match "
                           f"grid shape {self.grid_shape}")
        
        self._initial_conditions = u0.copy()
        
        if self.equation == EquationType.WAVE and v0 is not None:
            if v0.shape != self.grid_shape:
                raise ValueError(f"Initial velocity shape {v0.shape} doesn't match "
                               f"grid shape {self.grid_shape}")
            self._initial_velocity = v0.copy()
        else:
            self._initial_velocity = None
    
    def set_parameters(self, **params):
        """
        Set equation-specific parameters.
        
        For heat equation: alpha (thermal diffusivity), dt (time step)
        For wave equation: c (wave speed), dt (time step)
        """
        for key, value in params.items():
            if key in ['alpha', 'c', 'dt', 'dx', 'dy']:
                self.parameters[key] = value
            else:
                raise ValueError(f"Unknown parameter: {key}")
        
        # Update spacing if provided
        if 'dx' in params:
            self.dx = params['dx']
        if 'dy' in params:
            self.dy = params['dy']
    
    def get_stability_info(self) -> Dict[str, Any]:
        """
        Get stability condition information for current parameters.
        
        Returns:
        --------
        dict
            Information about stability conditions and current factor
        """
        dt = self.parameters.get('dt', 0.1)
        
        if self.equation == EquationType.HEAT:
            alpha = self.parameters.get('alpha', 1.0)
            factor = alpha * dt * (1/self.dx**2 + 1/self.dy**2)
            limit = 0.5
            condition = f"α * dt * (1/dx² + 1/dy²) ≤ {limit}"
            
        elif self.equation == EquationType.WAVE:
            c = self.parameters.get('c', 1.0)
            factor = c * dt * np.sqrt(1/self.dx**2 + 1/self.dy**2)
            limit = 1.0
            condition = f"c * dt * √(1/dx² + 1/dy²) ≤ {limit}"
        else:
            # This should never happen, but we need to handle it for type checking
            factor = 0.0
            limit = 1.0
            condition = "Unknown equation type"
        
        return {
            'condition': condition,
            'current_factor': factor,
            'limit': limit,
            'is_stable': factor <= limit,
            'safety_margin': limit - factor
        }
    
    def validate_stability(self):
        """Validate that current parameters satisfy stability conditions."""
        info = self.get_stability_info()
        
        if not info['is_stable']:
            raise ValueError(
                f"Stability condition violated for {self.equation.value} equation!\n"
                f"Condition: {info['condition']}\n"
                f"Current factor: {info['current_factor']:.4f} > {info['limit']}\n"
                f"Reduce dt or increase dx/dy."
            )
    
    def solve(self, steps: int = 100) -> np.ndarray:
        """
        Solve the PDE for the specified number of time steps.
        
        Parameters:
        -----------
        steps : int
            Number of time steps to solve
            
        Returns:
        --------
        numpy.ndarray
            Final solution field
        """
        if self._initial_conditions is None:
            raise ValueError("Initial conditions not set. Use set_initial_conditions().")
        
        # Validate stability
        self.validate_stability()
        
        # Get parameters
        dt = self.parameters.get('dt', 0.1)
        
        # Convert boundary condition to BoundarySpec
        boundary_spec = self.boundary.to_boundary_spec()
        
        if self.equation == EquationType.HEAT:
            alpha = self.parameters.get('alpha', 1.0)
            
            # Always use flexible boundary conditions for non-default boundaries
            # Only use original solver for default Dirichlet(0.0)
            if (self.boundary.type == BoundaryType.DIRICHLET and 
                self.boundary.value == 0.0):
                # Use original solver for default case (better performance)
                return solve_heat(self._initial_conditions, α=alpha, dt=dt,
                                dx=self.dx, dy=self.dy, steps=steps)
            else:
                # Use flexible boundary conditions for all other cases
                return solve_heat_with_boundaries(
                    self._initial_conditions, boundary_spec,
                    α=alpha, dt=dt, dx=self.dx, dy=self.dy, steps=steps
                )
            
        elif self.equation == EquationType.WAVE:
            c = self.parameters.get('c', 1.0)
            
            # Always use flexible boundary conditions for non-default boundaries
            # Only use original solver for default Dirichlet(0.0)
            if (self.boundary.type == BoundaryType.DIRICHLET and 
                self.boundary.value == 0.0):
                # Use original solver for default case (better performance)
                return solve_wave(self._initial_conditions, v0=self._initial_velocity,
                                c=c, dt=dt, dx=self.dx, dy=self.dy, steps=steps)
            else:
                # Use flexible boundary conditions for all other cases
                return solve_wave_with_boundaries(
                    self._initial_conditions, boundary_spec, 
                    v0=self._initial_velocity, c=c, dt=dt, 
                    dx=self.dx, dy=self.dy, steps=steps
                )
        else:
            raise ValueError(f"Unknown equation type: {self.equation}")
    
    def animate(self, frames: int = 100, interval: int = 50, 
                save_path: Optional[str] = None) -> FuncAnimation:
        """
        Create an animation of the PDE solution.
        
        Parameters:
        -----------
        frames : int
            Number of animation frames
        interval : int
            Time between frames in milliseconds
        save_path : str, optional
            Path to save animation (e.g., 'animation.gif')
            
        Returns:
        --------
        matplotlib.animation.FuncAnimation
            Animation object
        """
        if self._initial_conditions is None:
            raise ValueError("Initial conditions not set. Use set_initial_conditions().")
        
        # Validate stability
        self.validate_stability()
        
        # Get parameters
        dt = self.parameters.get('dt', 0.1)
        
        if self.equation == EquationType.HEAT:
            alpha = self.parameters.get('alpha', 1.0)
            anim = animate_heat(self._initial_conditions, α=alpha, dt=dt,
                              dx=self.dx, dy=self.dy, frames=frames, interval=interval)
            
        elif self.equation == EquationType.WAVE:
            c = self.parameters.get('c', 1.0)
            anim = animate_wave(self._initial_conditions, v0=self._initial_velocity,
                              c=c, dt=dt, dx=self.dx, dy=self.dy, 
                              frames=frames, interval=interval)
        else:
            raise ValueError(f"Unknown equation type: {self.equation}")
        
        # Save if path provided
        if save_path:
            anim.save(save_path, writer="pillow")
            print(f"Animation saved to {save_path}")
        
        return anim
    
    def info(self) -> str:
        """
        Get a summary of the current solver configuration.
        
        Returns:
        --------
        str
            Formatted summary of solver state
        """
        stability = self.get_stability_info()
        
        info_str = f"""
PDE Solver Configuration:
========================
Equation Type: {self.equation.value.title()}
Grid Shape: {self.grid_shape}
Grid Spacing: dx={self.dx}, dy={self.dy}
Boundary Condition: {self.boundary.type.value} (value={self.boundary.value})

Parameters:
{chr(10).join(f"  {k}: {v}" for k, v in self.parameters.items())}

Stability:
  Condition: {stability['condition']}
  Current Factor: {stability['current_factor']:.4f}
  Limit: {stability['limit']}
  Status: {'✅ STABLE' if stability['is_stable'] else '❌ UNSTABLE'}
  Safety Margin: {stability['safety_margin']:.4f}

Initial Conditions: {'✅ Set' if self._initial_conditions is not None else '❌ Not Set'}
"""
        
        if self.equation == EquationType.WAVE:
            info_str += f"Initial Velocity: {'✅ Set' if self._initial_velocity is not None else '❌ Not Set'}\n"
        
        return info_str