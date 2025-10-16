#!/usr/bin/env python3
"""
Quick test script to validate boundary condition fixes.
"""

import numpy as np
from pdevisualizer import PDESolver, BoundaryCondition, InitialConditions

def test_basic_boundaries():
    """Test basic boundary conditions work."""
    print("Testing basic boundary conditions...")
    
    grid_shape = (20, 20)
    u0 = InitialConditions.zeros(grid_shape)
    u0[10, 10] = 100.0
    
    # Test each boundary type
    boundary_types = [
        ("Dirichlet", BoundaryCondition.dirichlet(0.0)),
        ("Neumann", BoundaryCondition.neumann(0.0)),
        ("Periodic", BoundaryCondition.periodic())
    ]
    
    for name, boundary in boundary_types:
        print(f"  Testing {name}...")
        
        try:
            solver = PDESolver('heat', grid_shape=grid_shape, boundary=boundary)
            solver.set_parameters(alpha=0.1, dt=0.1)
            solver.set_initial_conditions(u0)
            result = solver.solve(steps=10)
            
            print(f"    ✅ {name} boundary works! Result shape: {result.shape}")
            print(f"    Heat total: {np.sum(result):.2f}")
            
        except Exception as e:
            print(f"    ❌ {name} boundary failed: {e}")
    
    print("✅ Basic boundary test complete!")

def test_wave_boundaries():
    """Test wave equation boundaries."""
    print("\nTesting wave equation boundaries...")
    
    grid_shape = (20, 20)
    u0 = InitialConditions.gaussian_pulse(grid_shape, center=(10, 10), sigma=3)
    
    # Test wave boundaries (excluding absorbing for now)
    boundary_types = [
        ("Dirichlet", BoundaryCondition.dirichlet(0.0)),
        ("Neumann", BoundaryCondition.neumann(0.0)),
        ("Periodic", BoundaryCondition.periodic())
    ]
    
    for name, boundary in boundary_types:
        print(f"  Testing {name}...")
        
        try:
            solver = PDESolver('wave', grid_shape=grid_shape, boundary=boundary)
            solver.set_parameters(c=1.0, dt=0.05)
            solver.set_initial_conditions(u0)
            result = solver.solve(steps=10)
            
            print(f"    ✅ {name} boundary works! Result shape: {result.shape}")
            print(f"    Wave energy: {np.sum(result**2):.4f}")
            
        except Exception as e:
            print(f"    ❌ {name} boundary failed: {e}")
    
    print("✅ Wave boundary test complete!")

def main():
    print("🔧 Testing Boundary Condition Fixes")
    print("=" * 40)
    
    test_basic_boundaries()
    test_wave_boundaries()
    
    print("\n🎉 All basic tests completed!")
    print("Run 'pytest tests/test_boundary_conditions.py -v' for full test suite")

if __name__ == "__main__":
    main()