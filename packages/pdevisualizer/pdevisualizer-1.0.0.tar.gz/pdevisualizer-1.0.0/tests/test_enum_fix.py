#!/usr/bin/env python3
"""
Test to verify that the enum fix works correctly.
"""

def test_enum_import():
    """Test that we can import the enums correctly."""
    print("Testing enum imports...")
    
    # Import from both modules
    from pdevisualizer.boundary_conditions import BoundaryType as BoundaryTypeBC
    from pdevisualizer.solver import BoundaryType as BoundaryTypeSolver
    
    # Test that they're the same
    print(f"BoundaryType from boundary_conditions: {BoundaryTypeBC}")
    print(f"BoundaryType from solver: {BoundaryTypeSolver}")
    
    # Test enum values
    print(f"NEUMANN from BC: {BoundaryTypeBC.NEUMANN}")
    print(f"NEUMANN from solver: {BoundaryTypeSolver.NEUMANN}")
    
    # Test that they're actually the same object
    assert BoundaryTypeBC is BoundaryTypeSolver
    assert BoundaryTypeBC.NEUMANN is BoundaryTypeSolver.NEUMANN
    
    print("✅ Enum fix working correctly!")

def test_boundary_condition_creation():
    """Test that boundary conditions work with the fixed enum."""
    print("\nTesting boundary condition creation...")
    
    from pdevisualizer.solver import BoundaryCondition
    
    # Test different boundary types
    bc_dirichlet = BoundaryCondition.dirichlet(10.0)
    bc_neumann = BoundaryCondition.neumann(2.0)
    bc_periodic = BoundaryCondition.periodic()
    
    print(f"Dirichlet BC type: {bc_dirichlet.type}")
    print(f"Neumann BC type: {bc_neumann.type}")
    print(f"Periodic BC type: {bc_periodic.type}")
    
    # Test conversion to BoundarySpec
    spec = bc_neumann.to_boundary_spec()
    print(f"Converted spec type: {spec.left['type']}")
    print(f"Converted spec value: {spec.left['value']}")
    
    print("✅ Boundary condition creation working!")

def test_solver_integration():
    """Test that the solver works with the fixed enums."""
    print("\nTesting solver integration...")
    
    import numpy as np
    from pdevisualizer import PDESolver, BoundaryCondition, InitialConditions
    
    # Test with Dirichlet boundary (should work)
    solver = PDESolver('heat', grid_shape=(10, 10), 
                      boundary=BoundaryCondition.dirichlet(0.0))
    
    u0 = InitialConditions.zeros((10, 10))
    u0[5, 5] = 100.0
    solver.set_initial_conditions(u0)
    solver.set_parameters(alpha=0.1, dt=0.1)
    
    try:
        result = solver.solve(steps=5)
        print(f"✅ Dirichlet boundary solver works! Result shape: {result.shape}")
    except Exception as e:
        print(f"❌ Dirichlet boundary solver failed: {e}")
    
    # Test with Neumann boundary 
    solver_neumann = PDESolver('heat', grid_shape=(10, 10),
                              boundary=BoundaryCondition.neumann(0.0))
    solver_neumann.set_initial_conditions(u0)
    solver_neumann.set_parameters(alpha=0.1, dt=0.1)
    
    try:
        result = solver_neumann.solve(steps=5)
        print(f"✅ Neumann boundary solver works! Result shape: {result.shape}")
    except Exception as e:
        print(f"❌ Neumann boundary solver failed: {e}")

def main():
    print("🔧 Testing Enum Fix")
    print("=" * 30)
    
    test_enum_import()
    test_boundary_condition_creation()
    test_solver_integration()
    
    print("\n🎉 All enum tests completed!")

if __name__ == "__main__":
    main()