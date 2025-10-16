"""
PDEVisualizer: A lightweight Python library for 2D PDE visualization.
This package provides tools for solving and visualizing partial differential
equations including heat diffusion and wave propagation.
"""

__version__ = "0.2.2"  # Updated version
__author__ = "Your Name"
__email__ = "your.email@example.com"

# Import main classes and functions for easy access
from .solver import (
    PDESolver,
    EquationType,
    BoundaryType,
    BoundaryCondition,
    InitialConditions
)

# Import parameter exploration tools
from .parameter_exploration import (
    ParameterExplorer,
    ParameterVisualizer,
    ParameterSweepResult
)

# Import enhanced visualizations
from .enhanced_visualizations import EnhancedVisualizer

# Import original solvers for backward compatibility
from .heat2d import solve_heat, animate_heat, step_heat
from .wave2d import (
    solve_wave, animate_wave, step_wave, step_wave_first,
    create_gaussian_pulse, create_circular_wave
)

# Define what gets imported with "from pdevisualizer import *"
__all__ = [
    # Main unified API
    'PDESolver',
    'EquationType',
    'BoundaryType',
    'BoundaryCondition',
    'InitialConditions',
    
    # Parameter exploration
    'ParameterExplorer',
    'ParameterVisualizer',
    'ParameterSweepResult',
    
    # Enhanced visualizations
    'EnhancedVisualizer',
    
    # Heat equation functions
    'solve_heat',
    'animate_heat',
    'step_heat',
    
    # Wave equation functions
    'solve_wave',
    'animate_wave',
    'step_wave',
    'step_wave_first',
    'create_gaussian_pulse',
    'create_circular_wave',
]