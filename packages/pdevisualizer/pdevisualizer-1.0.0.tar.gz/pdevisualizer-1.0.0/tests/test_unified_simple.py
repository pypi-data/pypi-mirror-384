#!/usr/bin/env python3
"""
Simple test script for the unified API to verify it works.
Run this after creating the solver.py file.
"""

def test_imports():
    """Test that we can import everything."""
    print("Testing imports...")
    try:
        from pdevisualizer import PDESolver, InitialConditions, BoundaryCondition
        print("✅ Imports successful!")
        return True
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False

def test_heat_solver():
    """Test basic heat solver functionality."""
    print("Testing heat solver...")
    try:
        from pdevisualizer import PDESolver, InitialConditions
        
        # Create solver
        solver = PDESolver('heat', grid_shape=(20, 20))
        solver.set_parameters(alpha=0.25, dt=0.1)
        
        # Create initial conditions
        u0 = InitialConditions.gaussian_pulse((20, 20), center=(10, 10), sigma=3)
        solver.set_initial_conditions(u0)
        
        # Test stability info
        stability = solver.get_stability_info()
        print(f"  Stability factor: {stability['current_factor']:.3f}")
        
        # Solve
        result = solver.solve(steps=10)
        print(f"  Result shape: {result.shape}")
        print("✅ Heat solver works!")
        return True
    except Exception as e:
        print(f"❌ Heat solver failed: {e}")
        return False

def test_wave_solver():
    """Test basic wave solver functionality."""
    print("Testing wave solver...")
    try:
        from pdevisualizer import PDESolver, InitialConditions
        
        # Create solver
        solver = PDESolver('wave', grid_shape=(20, 20))
        solver.set_parameters(c=1.0, dt=0.05)
        
        # Create initial conditions
        u0 = InitialConditions.circular_wave((20, 20), center=(10, 10), radius=5)
        solver.set_initial_conditions(u0)
        
        # Test stability info
        stability = solver.get_stability_info()
        print(f"  Stability factor: {stability['current_factor']:.3f}")
        
        # Solve
        result = solver.solve(steps=10)
        print(f"  Result shape: {result.shape}")
        print("✅ Wave solver works!")
        return True
    except Exception as e:
        print(f"❌ Wave solver failed: {e}")
        return False

def test_initial_conditions():
    """Test initial condition generation."""
    print("Testing initial conditions...")
    try:
        from pdevisualizer import InitialConditions
        
        # Test different types
        u1 = InitialConditions.zeros((10, 10))
        u2 = InitialConditions.constant((10, 10), 5.0)
        u3 = InitialConditions.gaussian_pulse((10, 10), center=(5, 5), sigma=2)
        u4 = InitialConditions.sine_wave((10, 10), wavelength=5, direction='x')
        u5 = InitialConditions.multiple_sources((10, 10), [(3, 3, 1.0), (7, 7, 2.0)])
        
        print(f"  Zeros: {u1.shape}, max={u1.max()}")
        print(f"  Constant: {u2.shape}, max={u2.max()}")
        print(f"  Gaussian: {u3.shape}, max={u3.max():.2f}")
        print(f"  Sine wave: {u4.shape}, max={u4.max():.2f}")
        print(f"  Multiple sources: {u5.shape}, max={u5.max()}")
        print("✅ Initial conditions work!")
        return True
    except Exception as e:
        print(f"❌ Initial conditions failed: {e}")
        return False

def main():
    """Run all tests."""
    print("🚀 Testing Unified PDEVisualizer API")
    print("=" * 40)
    
    tests = [
        test_imports,
        test_initial_conditions,
        test_heat_solver,
        test_wave_solver,
    ]
    
    passed = 0
    for test in tests:
        if test():
            passed += 1
        print()
    
    print(f"Results: {passed}/{len(tests)} tests passed")
    
    if passed == len(tests):
        print("🎉 All tests passed! Unified API is working!")
        print("\nTry creating an animation:")
        print("  solver = PDESolver('heat')")
        print("  solver.set_initial_conditions(u0)")
        print("  solver.animate(frames=50, save_path='test.gif')")
    else:
        print("❌ Some tests failed. Check the error messages above.")

if __name__ == "__main__":
    main()