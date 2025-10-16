# PDEVisualizer

A lightweight Python library for prototyping and visualizing 2D partial differential equations (PDEs). Built for scientific computing applications with performance optimization and beautiful visualizations.

## 🚀 Features

- **2D Heat Equation Solver**: Finite difference implementation with stability validation
- **2D Wave Equation Solver**: Leapfrog scheme with CFL condition enforcement  
- **Numba JIT Compilation**: Near-C++ performance for numerical computations
- **Beautiful Animations**: Publication-quality visualizations with matplotlib
- **Comprehensive Testing**: 23 test cases ensuring mathematical correctness
- **Professional Packaging**: Easy installation and distribution

## 📊 Supported Equations

### Heat Equation (Parabolic PDE)
```
∂u/∂t = α∇²u
```
Models heat diffusion, chemical concentration, and other diffusive processes.

### Wave Equation (Hyperbolic PDE)  
```
∂²u/∂t² = c²∇²u
```
Models sound waves, electromagnetic waves, and mechanical vibrations.

## 🛠️ Installation

### Prerequisites
- Python 3.8+
- NumPy, Matplotlib, Numba, SciPy

### Install from Source
```bash
git clone https://github.com/yourusername/pdevisualizer.git
cd pdevisualizer
pip install -e .
```

### Verify Installation
```bash
pytest tests/ -v
```
Expected: `23 tests passed`

## 📖 Quick Start

### Heat Diffusion
```python
import numpy as np
from pdevisualizer.heat2d import solve_heat, animate_heat

# Create initial temperature field with hot spot
grid_size = 100
u0 = np.zeros((grid_size, grid_size))
u0[50, 50] = 100  # Hot spot at center

# Solve heat equation
u_final = solve_heat(u0, α=0.25, dt=0.1, dx=1.0, dy=1.0, steps=100)

# Create animation
anim = animate_heat(u0, α=0.25, dt=0.1, frames=200)
anim.save("heat_diffusion.gif", writer="pillow")
```

### Wave Propagation
```python
from pdevisualizer.wave2d import solve_wave, animate_wave, create_gaussian_pulse

# Create Gaussian pulse initial condition
grid_size = 100
u0 = create_gaussian_pulse(grid_size, center=(50, 50), sigma=5, amplitude=2.0)

# Solve wave equation
u_final = solve_wave(u0, c=1.0, dt=0.05, dx=1.0, dy=1.0, steps=200)

# Create animation
anim = animate_wave(u0, c=1.0, dt=0.05, frames=200)
anim.save("wave_propagation.gif", writer="pillow")
```

## 🔬 Example Visualizations

### Heat Diffusion
Heat spreads smoothly from a central hot spot, demonstrating diffusive behavior characteristic of parabolic PDEs.

*[Heat diffusion animation would be embedded here]*

### Wave Propagation - Gaussian Pulse
A Gaussian pulse propagates outward with sharp wave fronts, showing the oscillatory nature of hyperbolic PDEs.

*[Gaussian wave animation would be embedded here]*

### Wave Propagation - Circular Wave
Circular wave fronts expand outward, demonstrating wave interference and propagation patterns.

*[Circular wave animation would be embedded here]*

## 🧪 Testing

Run the comprehensive test suite:

```bash
# Run all tests
pytest tests/ -v

# Run specific equation tests
pytest tests/test_heat2d.py -v    # 9 tests for heat equation
pytest tests/test_wave2d.py -v    # 14 tests for wave equation

# Run with coverage
pytest tests/ --cov=pdevisualizer
```

### Test Coverage
- **Mathematical Correctness**: Validates PDE solutions against known behaviors
- **Numerical Stability**: Ensures stability conditions are enforced
- **Boundary Conditions**: Verifies proper boundary handling
- **Physical Properties**: Tests energy conservation and wave propagation
- **Performance**: Validates Numba compilation and optimization

## ⚡ Performance

### Optimization Features
- **Numba JIT**: Just-in-time compilation for computational kernels
- **Vectorized Operations**: NumPy array operations for efficiency
- **Memory Management**: Efficient array copying and reuse
- **Stability Validation**: Prevents numerical instabilities

### Benchmarks
- **100×100 grid**: ~0.1s per 100 time steps
- **500×500 grid**: ~2s per 100 time steps  
- **1000×1000 grid**: ~15s per 100 time steps

*Benchmarks on Apple M2 MacBook Air with Python 3.12*

## 🔧 API Reference

### Heat Equation
```python
solve_heat(u0, α=1.0, dt=0.1, dx=1.0, dy=1.0, steps=100)
animate_heat(u0, α=1.0, dt=0.1, dx=1.0, dy=1.0, frames=100, interval=50)
```

### Wave Equation
```python
solve_wave(u0, v0=None, c=1.0, dt=0.1, dx=1.0, dy=1.0, steps=100)
animate_wave(u0, v0=None, c=1.0, dt=0.1, dx=1.0, dy=1.0, frames=100, interval=50)

# Helper functions
create_gaussian_pulse(grid_size, center, sigma, amplitude=1.0)
create_circular_wave(grid_size, center, radius, amplitude=1.0)
```

### Parameters
- **u0**: Initial field (2D numpy array)
- **v0**: Initial velocity for wave equation (2D numpy array, optional)
- **α**: Thermal diffusivity for heat equation
- **c**: Wave speed for wave equation
- **dt**: Time step size
- **dx, dy**: Spatial grid spacing
- **steps**: Number of time steps to solve
- **frames**: Number of animation frames

## 🛡️ Stability Conditions

### Heat Equation
For numerical stability: `α * dt * (1/dx² + 1/dy²) ≤ 0.5`

### Wave Equation  
For numerical stability (CFL condition): `c * dt * √(1/dx² + 1/dy²) ≤ 1.0`

Both solvers automatically validate these conditions and raise errors for unstable parameters.

## 🗺️ Roadmap

### Phase 1: Core Solvers ✅
- [x] Heat equation implementation
- [x] Wave equation implementation  
- [x] Comprehensive testing
- [x] Performance optimization
- [x] Basic visualizations

### Phase 2: Advanced Features (In Progress)
- [ ] Flexible boundary conditions (Dirichlet, Neumann, periodic)
- [ ] Multiple initial condition types
- [ ] Interactive parameter exploration
- [ ] Jupyter notebook demos
- [ ] Enhanced documentation

### Phase 3: Extended Capabilities (Future)
- [ ] 3D equation support
- [ ] Additional PDE types (Schrödinger, diffusion-reaction)
- [ ] GPU acceleration with CuPy
- [ ] Interactive web interface
- [ ] Real-time parameter adjustment

## 🤝 Contributing

Contributions are welcome! Please feel free to submit issues, feature requests, or pull requests.

### Development Setup
```bash
git clone https://github.com/yourusername/pdevisualizer.git
cd pdevisualizer
pip install -e ".[dev]"
pytest tests/
```

### Code Style
- Follow PEP 8 guidelines
- Use type hints where appropriate
- Add comprehensive tests for new features
- Document all public functions

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🏆 Acknowledgments

- **NumPy/SciPy**: Foundation for numerical computing
- **Numba**: JIT compilation for performance
- **Matplotlib**: Beautiful scientific visualizations
- **Pytest**: Comprehensive testing framework

## 📧 Contact

For questions, suggestions, or collaboration opportunities, please open an issue on GitHub.

---

**Built with ❤️ for the scientific computing community**