# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2025-10-15

### Added
- **Unified PDE Solver** (`PDESolver` class in `solver.py`)
  - Heat equation solver with finite difference method
  - Wave equation solver with explicit time-stepping
  - Support for 2D domains with customizable grid sizes
  - Numba JIT compilation for performance optimization
  
- **Comprehensive Boundary Conditions** (`boundary_conditions.py`)
  - Dirichlet (fixed value) boundaries
  - Neumann (zero flux/insulated) boundaries
  - Periodic (wraparound) boundaries
  - `BoundaryCondition` factory class for easy configuration
  
- **Initial Condition Generators**
  - Gaussian pulse generator for heat simulations
  - Circular wave generator for wave propagation
  - Ring pattern generator
  - Checkerboard pattern generator
  - Support for custom initial conditions via NumPy arrays
  
- **Enhanced Visualization Tools** (`enhanced_visualizations.py`)
  - 3D surface plots with rotation and perspective
  - 2D heatmap animations
  - Time-series slice visualization
  - Comparison plots for multiple solutions
  - Customizable colormaps and plot styles
  - High-quality export (GIF, MP4, PNG)
  
- **Parameter Exploration Framework** (`parameter_exploration.py`)
  - Parameter sweep analysis across ranges
  - Multi-parameter grid exploration
  - Sensitivity analysis tools
  - Automated metric tracking (energy, max/min, center values)
  - Publication-quality visualization of parameter effects
  - CFL stability checking
  
- **Original Equation Modules** (maintained for backwards compatibility)
  - `heat2d.py` - Original heat equation implementation
  - `wave2d.py` - Original wave equation implementation
  
- **Comprehensive Testing**
  - 25+ test cases covering all functionality
  - Integration tests for complete workflows
  - Edge case handling and validation
  - Test coverage > 85%
  
- **Demo Scripts**
  - `demo_boundary_conditions.py` - Showcase boundary types
  - `demo_parameter_exploration.py` - Parameter study examples
  - `enhanced_visualizations_demo.py` - Visualization gallery
  
- **Documentation**
  - README with quick start examples
  - Docstrings throughout codebase
  - Type hints for better IDE support

### Technical Details
- Python 3.10+ support
- Dependencies: numpy, matplotlib, numba, scipy
- MIT License
- Modular architecture for easy extension

### Performance
- Numba JIT compilation provides 10-100x speedup over pure Python
- Efficient memory management for large grids
- Optimized animation generation

## [Unreleased]

### Planned Features
- 3D domain support for all equations
- 2D Schrödinger equation solver (quantum mechanics)
- Nonlinear PDEs (Burgers, Allen-Cahn, reaction-diffusion)
- Adaptive time-stepping for improved stability
- GPU acceleration support via CuPy
- Interactive Streamlit/Dash web dashboard
- Implicit solvers for stiff equations
- Spectral methods (FFT-based solvers)
- Advanced boundary conditions (Robin, mixed)

---

[1.0.0]: https://github.com/AdityaAnoop3/pdevisualizer/releases/tag/v1.0.0