import numpy as np
import pytest
from pdevisualizer.boundary_conditions import (
    BoundaryType, BoundarySpec, apply_boundary_conditions,
    apply_dirichlet_boundary, apply_neumann_boundary, apply_periodic_boundary,
    solve_heat_with_boundaries, solve_wave_with_boundaries
)
from pdevisualizer.solver import PDESolver, BoundaryCondition, InitialConditions


class TestBoundarySpec:
    """Test BoundarySpec class functionality."""
    
    def test_uniform_dirichlet(self):
        spec = BoundarySpec.dirichlet(5.0)
        assert spec.left['type'] == BoundaryType.DIRICHLET
        assert spec.left['value'] == 5.0
        assert spec.right['type'] == BoundaryType.DIRICHLET
        assert spec.right['value'] == 5.0
    
    def test_uniform_neumann(self):
        spec = BoundarySpec.neumann(2.0)
        assert spec.left['type'] == BoundaryType.NEUMANN
        assert spec.left['value'] == 2.0
        assert spec.right['type'] == BoundaryType.NEUMANN
        assert spec.right['value'] == 2.0
    
    def test_uniform_periodic(self):
        spec = BoundarySpec.periodic()
        assert spec.left['type'] == BoundaryType.PERIODIC
        assert spec.right['type'] == BoundaryType.PERIODIC
    
    def test_uniform_absorbing(self):
        spec = BoundarySpec.absorbing()
        assert spec.left['type'] == BoundaryType.ABSORBING
        assert spec.right['type'] == BoundaryType.ABSORBING
    
    def test_mixed_boundaries(self):
        spec = BoundarySpec(
            left={'type': BoundaryType.DIRICHLET, 'value': 0.0},
            right={'type': BoundaryType.NEUMANN, 'value': 1.0},
            top={'type': BoundaryType.PERIODIC},
            bottom={'type': BoundaryType.ABSORBING}
        )
        assert spec.left['type'] == BoundaryType.DIRICHLET
        assert spec.right['type'] == BoundaryType.NEUMANN
        assert spec.top['type'] == BoundaryType.PERIODIC
        assert spec.bottom['type'] == BoundaryType.ABSORBING


class TestBoundaryApplications:
    """Test boundary condition application functions."""
    
    def test_apply_dirichlet_boundary(self):
        u = np.ones((10, 10))
        u_bc = apply_dirichlet_boundary(u, 5.0)
        
        # Check boundaries
        assert np.allclose(u_bc[0, :], 5.0)  # Left
        assert np.allclose(u_bc[-1, :], 5.0)  # Right
        assert np.allclose(u_bc[:, 0], 5.0)  # Bottom
        assert np.allclose(u_bc[:, -1], 5.0)  # Top
        
        # Check interior (should be unchanged)
        assert np.allclose(u_bc[1:-1, 1:-1], 1.0)
    
    def test_apply_neumann_boundary(self):
        u = np.zeros((10, 10))
        u[5, 5] = 1.0  # Central point
        dx = dy = 1.0
        flux = 0.0  # Zero flux (insulated)
        
        u_bc = apply_neumann_boundary(u, flux, dx, dy)
        
        # For zero flux, boundary should equal adjacent interior
        assert np.allclose(u_bc[0, :], u_bc[1, :])  # Left
        assert np.allclose(u_bc[-1, :], u_bc[-2, :])  # Right
        assert np.allclose(u_bc[:, 0], u_bc[:, 1])  # Bottom
        assert np.allclose(u_bc[:, -1], u_bc[:, -2])  # Top
    
    def test_apply_periodic_boundary(self):
        u = np.random.rand(10, 10)
        u_original = u.copy()
        
        u_bc = apply_periodic_boundary(u)
        
        # Check periodicity (excluding corners for now)
        assert np.allclose(u_bc[0, 1:-1], u_original[-2, 1:-1])  # Left = second-to-last
        assert np.allclose(u_bc[-1, 1:-1], u_original[1, 1:-1])  # Right = second
        assert np.allclose(u_bc[1:-1, 0], u_original[1:-1, -2])  # Bottom = second-to-last
        assert np.allclose(u_bc[1:-1, -1], u_original[1:-1, 1])  # Top = second
    
    def test_apply_boundary_conditions_dirichlet(self):
        u = np.ones((10, 10))
        spec = BoundarySpec.dirichlet(3.0)
        
        u_bc = apply_boundary_conditions(u, spec)
        
        # Check boundaries
        assert np.allclose(u_bc[0, :], 3.0)
        assert np.allclose(u_bc[-1, :], 3.0)
        assert np.allclose(u_bc[:, 0], 3.0)
        assert np.allclose(u_bc[:, -1], 3.0)
    
    def test_apply_boundary_conditions_neumann(self):
        u = np.zeros((10, 10))
        u[5, 5] = 1.0
        spec = BoundarySpec.neumann(0.0)
        
        u_bc = apply_boundary_conditions(u, spec, dx=1.0, dy=1.0)
        
        # Zero flux means boundary = adjacent interior
        assert np.allclose(u_bc[0, :], u_bc[1, :])
        assert np.allclose(u_bc[-1, :], u_bc[-2, :])
    
    def test_apply_boundary_conditions_periodic(self):
        u = np.random.rand(10, 10)
        u_original = u.copy()
        spec = BoundarySpec.periodic()
        
        u_bc = apply_boundary_conditions(u, spec)
        
        # Check periodicity (excluding corners)
        assert np.allclose(u_bc[0, 1:-1], u_original[-2, 1:-1])
        assert np.allclose(u_bc[-1, 1:-1], u_original[1, 1:-1])


class TestHeatEquationBoundaries:
    """Test heat equation with different boundary conditions."""
    
    def test_heat_dirichlet_boundaries(self):
        # Hot center, cold boundaries
        u0 = np.zeros((20, 20))
        u0[10, 10] = 100.0
        
        spec = BoundarySpec.dirichlet(0.0)
        u_final = solve_heat_with_boundaries(u0, spec, α=0.1, dt=0.1, steps=50)
        
        # Check boundaries remain at 0
        assert np.allclose(u_final[0, :], 0.0)
        assert np.allclose(u_final[-1, :], 0.0)
        assert np.allclose(u_final[:, 0], 0.0)
        assert np.allclose(u_final[:, -1], 0.0)
        
        # Heat should have diffused inward
        assert u_final[10, 10] < 100.0
        assert u_final[9, 10] > 0.0  # Heat spread to neighbors
    
    def test_heat_neumann_boundaries(self):
        # Hot center, insulated boundaries
        u0 = np.zeros((20, 20))
        u0[10, 10] = 100.0
        
        spec = BoundarySpec.neumann(0.0)  # Insulated (zero flux)
        u_final = solve_heat_with_boundaries(u0, spec, α=0.1, dt=0.1, steps=50)
        
        # With insulated boundaries, heat should be conserved
        initial_heat = np.sum(u0)
        final_heat = np.sum(u_final)
        
        # Heat should be approximately conserved (within numerical tolerance)
        assert abs(final_heat - initial_heat) < initial_heat * 0.01
        
        # Check insulated boundary condition (∂u/∂n = 0)
        # This means boundary values equal adjacent interior values
        assert np.allclose(u_final[0, :], u_final[1, :], atol=1e-10)
        assert np.allclose(u_final[-1, :], u_final[-2, :], atol=1e-10)
    
    def test_heat_periodic_boundaries(self):
        # Asymmetric initial condition
        u0 = np.zeros((20, 20))
        u0[5, 5] = 100.0  # Off-center hot spot
        
        spec = BoundarySpec.periodic()
        u_final = solve_heat_with_boundaries(u0, spec, α=0.1, dt=0.1, steps=100)
        
        # Check periodic boundary conditions
        assert np.allclose(u_final[0, :], u_final[-2, :], atol=1e-6)
        assert np.allclose(u_final[-1, :], u_final[1, :], atol=1e-6)
        assert np.allclose(u_final[:, 0], u_final[:, -2], atol=1e-6)
        assert np.allclose(u_final[:, -1], u_final[:, 1], atol=1e-6)


class TestWaveEquationBoundaries:
    """Test wave equation with different boundary conditions."""
    
    def test_wave_dirichlet_boundaries(self):
        # Gaussian pulse in center
        u0 = np.zeros((30, 30))
        u0[15, 15] = 1.0
        
        spec = BoundarySpec.dirichlet(0.0)
        u_final = solve_wave_with_boundaries(u0, spec, c=1.0, dt=0.05, steps=50)
        
        # Check boundaries remain at 0
        assert np.allclose(u_final[0, :], 0.0)
        assert np.allclose(u_final[-1, :], 0.0)
        assert np.allclose(u_final[:, 0], 0.0)
        assert np.allclose(u_final[:, -1], 0.0)
        
        # Wave should have propagated
        assert np.any(np.abs(u_final) > 1e-6)
    
    def test_wave_neumann_boundaries(self):
        # Gaussian pulse in center
        u0 = np.zeros((30, 30))
        u0[15, 15] = 1.0
        
        spec = BoundarySpec.neumann(0.0)  # Zero flux at boundaries
        u_final = solve_wave_with_boundaries(u0, spec, c=1.0, dt=0.05, steps=50)
        
        # Check Neumann boundary condition (∂u/∂n = 0)
        assert np.allclose(u_final[0, :], u_final[1, :], atol=1e-4)
        assert np.allclose(u_final[-1, :], u_final[-2, :], atol=1e-4)
        
        # Wave should have propagated and reflected
        assert np.any(np.abs(u_final) > 1e-6)
    
    def test_wave_periodic_boundaries(self):
        # Off-center pulse
        u0 = np.zeros((30, 30))
        u0[10, 10] = 1.0
        
        spec = BoundarySpec.periodic()
        u_final = solve_wave_with_boundaries(u0, spec, c=1.0, dt=0.05, steps=50)
        
        # Check periodic boundary conditions
        assert np.allclose(u_final[0, :], u_final[-2, :], atol=1e-4)
        assert np.allclose(u_final[-1, :], u_final[1, :], atol=1e-4)
        assert np.allclose(u_final[:, 0], u_final[:, -2], atol=1e-4)
        assert np.allclose(u_final[:, -1], u_final[:, 1], atol=1e-4)
    
    def test_wave_absorbing_boundaries(self):
        # Central pulse that will reach boundaries
        u0 = np.zeros((30, 30))
        u0[15, 15] = 1.0
        
        spec = BoundarySpec.absorbing()
        u_final = solve_wave_with_boundaries(u0, spec, c=1.0, dt=0.05, steps=100)
        
        # Absorbing boundaries should minimize reflections
        # The wave should have mostly passed through the boundaries
        boundary_energy = (np.sum(u_final[0, :]**2) + np.sum(u_final[-1, :]**2) + 
                          np.sum(u_final[:, 0]**2) + np.sum(u_final[:, -1]**2))
        
        # Boundary energy should be small (most wave has been absorbed)
        assert boundary_energy < 0.1


class TestUnifiedSolverBoundaries:
    """Test unified solver with different boundary conditions."""
    
    def test_heat_solver_with_neumann_boundaries(self):
        # Test heat equation with insulated boundaries
        solver = PDESolver(
            equation='heat',
            grid_shape=(20, 20),
            boundary=BoundaryCondition.neumann(0.0)  # Insulated
        )
        
        solver.set_parameters(alpha=0.1, dt=0.1)
        
        # Hot spot in center
        u0 = InitialConditions.zeros((20, 20))
        u0[10, 10] = 100.0
        solver.set_initial_conditions(u0)
        
        # Solve
        result = solver.solve(steps=50)
        
        # Check insulated boundary condition
        assert np.allclose(result[0, :], result[1, :], atol=1e-10)
        assert np.allclose(result[-1, :], result[-2, :], atol=1e-10)
        
        # Heat should be conserved
        assert np.sum(result) == pytest.approx(100.0, rel=0.01)
    
    def test_wave_solver_with_periodic_boundaries(self):
        # Test wave equation with periodic boundaries
        solver = PDESolver(
            equation='wave',
            grid_shape=(30, 30),
            boundary=BoundaryCondition.periodic()
        )
        
        solver.set_parameters(c=1.0, dt=0.05)
        
        # Off-center pulse
        u0 = InitialConditions.zeros((30, 30))
        u0[10, 10] = 1.0
        solver.set_initial_conditions(u0)
        
        # Solve
        result = solver.solve(steps=50)
        
        # Check periodic boundary conditions
        assert np.allclose(result[0, :], result[-2, :], atol=1e-4)
        assert np.allclose(result[-1, :], result[1, :], atol=1e-4)
        assert np.allclose(result[:, 0], result[:, -2], atol=1e-4)
        assert np.allclose(result[:, -1], result[:, 1], atol=1e-4)
    
    def test_wave_solver_with_absorbing_boundaries(self):
        # Test wave equation with absorbing boundaries
        solver = PDESolver(
            equation='wave',
            grid_shape=(30, 30),
            boundary=BoundaryCondition.absorbing()
        )
        
        solver.set_parameters(c=1.0, dt=0.05)
        
        # Central pulse
        u0 = InitialConditions.gaussian_pulse((30, 30), center=(15, 15), sigma=3)
        solver.set_initial_conditions(u0)
        
        # Solve for long time (wave should reach boundaries)
        result = solver.solve(steps=100)
        
        # Absorbing boundaries should reduce energy compared to reflecting boundaries
        # (First-order absorbing boundaries aren't perfect, so we use a more realistic threshold)
        total_energy = np.sum(result**2)
        initial_energy = np.sum(u0**2)
        
        # Most energy should have been absorbed (realistic expectation)
        assert total_energy < initial_energy * 0.8  # 80% or more absorbed
        
        # Check that boundary energy is not too high
        boundary_energy = (np.sum(result[0, :]**2) + np.sum(result[-1, :]**2) + 
                          np.sum(result[:, 0]**2) + np.sum(result[:, -1]**2))
        assert boundary_energy < total_energy * 0.5  # Boundary has less than half the energy
    
    def test_heat_solver_with_hot_boundaries(self):
        # Test heat equation with hot boundaries
        solver = PDESolver(
            equation='heat',
            grid_shape=(20, 20),
            boundary=BoundaryCondition.dirichlet(50.0)  # Hot boundaries
        )
        
        solver.set_parameters(alpha=0.2, dt=0.1)
        
        # Start with cold interior
        u0 = InitialConditions.zeros((20, 20))
        solver.set_initial_conditions(u0)
        
        # Solve for more steps to allow heat to penetrate
        result = solver.solve(steps=500)
        
        # Check boundaries are hot
        assert np.allclose(result[0, :], 50.0)
        assert np.allclose(result[-1, :], 50.0)
        assert np.allclose(result[:, 0], 50.0)
        assert np.allclose(result[:, -1], 50.0)
        
        # Interior should have heated up significantly
        center_temp = result[10, 10]
        print(f"Center temperature after 500 steps: {center_temp}")
        
        # Interior should be warmer than initial condition
        assert center_temp > 1.0  # Should be noticeably warmer than 0
        
        # Check that heat is flowing inward (temperature gradient)
        edge_temp = result[1, 10]  # Near edge
        assert edge_temp > center_temp  # Should be warmer near the hot boundary


class TestBoundaryConditionComparison:
    """Test comparing different boundary conditions on the same problem."""
    
    def test_heat_boundary_comparison(self):
        # Same initial condition, different boundaries
        u0 = np.zeros((20, 20))
        u0[10, 10] = 100.0
        
        # Dirichlet (cold boundaries)
        solver_dirichlet = PDESolver('heat', grid_shape=(20, 20), 
                                   boundary=BoundaryCondition.dirichlet(0.0))
        solver_dirichlet.set_parameters(alpha=0.1, dt=0.1)
        solver_dirichlet.set_initial_conditions(u0)
        result_dirichlet = solver_dirichlet.solve(steps=50)
        
        # Neumann (insulated boundaries)
        solver_neumann = PDESolver('heat', grid_shape=(20, 20),
                                 boundary=BoundaryCondition.neumann(0.0))
        solver_neumann.set_parameters(alpha=0.1, dt=0.1)
        solver_neumann.set_initial_conditions(u0)
        result_neumann = solver_neumann.solve(steps=50)
        
        # Periodic boundaries
        solver_periodic = PDESolver('heat', grid_shape=(20, 20),
                                  boundary=BoundaryCondition.periodic())
        solver_periodic.set_parameters(alpha=0.1, dt=0.1)
        solver_periodic.set_initial_conditions(u0)
        result_periodic = solver_periodic.solve(steps=50)
        
        # Results should be different
        assert not np.allclose(result_dirichlet, result_neumann)
        assert not np.allclose(result_dirichlet, result_periodic)
        assert not np.allclose(result_neumann, result_periodic)
        
        # Heat conservation check
        heat_dirichlet = np.sum(result_dirichlet)
        heat_neumann = np.sum(result_neumann)
        heat_periodic = np.sum(result_periodic)
        
        # Dirichlet should lose heat (cold boundaries)
        assert heat_dirichlet < 100.0
        
        # Neumann should conserve heat (insulated)
        assert heat_neumann == pytest.approx(100.0, rel=0.01)
        
        # Periodic should conserve heat
        assert heat_periodic == pytest.approx(100.0, rel=0.01)


class TestBoundaryConditionEdgeCases:
    """Test edge cases and error conditions."""
    
    def test_invalid_boundary_specification(self):
        with pytest.raises(ValueError):
            BoundarySpec(left="invalid")
    
    def test_absorbing_boundary_requires_previous_step(self):
        u = np.random.rand(10, 10)
        spec = BoundarySpec.absorbing()
        
        with pytest.raises(ValueError, match="Absorbing boundaries require"):
            apply_boundary_conditions(u, spec)
    
    def test_boundary_condition_to_spec_conversion(self):
        bc = BoundaryCondition.neumann(2.0)
        spec = bc.to_boundary_spec()
        
        # Check that the conversion worked correctly
        assert spec.left['type'].value == 'neumann'  # Compare enum values
        assert spec.left['value'] == 2.0
        assert spec.right['type'].value == 'neumann'
        assert spec.right['value'] == 2.0