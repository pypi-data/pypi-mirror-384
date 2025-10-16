import numpy as np
import pytest
from pdevisualizer.solver import (
    PDESolver, EquationType, BoundaryType, BoundaryCondition, InitialConditions
)


class TestBoundaryCondition:
    """Test boundary condition creation and types."""
    
    def test_dirichlet_creation(self):
        bc = BoundaryCondition.dirichlet(5.0)
        assert bc.type == BoundaryType.DIRICHLET
        assert bc.value == 5.0
    
    def test_neumann_creation(self):
        bc = BoundaryCondition.neumann(2.0)
        assert bc.type == BoundaryType.NEUMANN
        assert bc.value == 2.0
    
    def test_periodic_creation(self):
        bc = BoundaryCondition.periodic()
        assert bc.type == BoundaryType.PERIODIC
    
    def test_absorbing_creation(self):
        bc = BoundaryCondition.absorbing()
        assert bc.type == BoundaryType.ABSORBING


class TestInitialConditions:
    """Test initial condition generation functions."""
    
    def test_zeros(self):
        u0 = InitialConditions.zeros((10, 10))
        assert u0.shape == (10, 10)
        assert np.allclose(u0, 0.0)
    
    def test_constant(self):
        u0 = InitialConditions.constant((10, 10), 5.0)
        assert u0.shape == (10, 10)
        assert np.allclose(u0, 5.0)
    
    def test_gaussian_pulse(self):
        u0 = InitialConditions.gaussian_pulse((20, 20), center=(10, 10), sigma=2, amplitude=1.0)
        assert u0.shape == (20, 20)
        assert u0[10, 10] == pytest.approx(1.0, abs=1e-10)
        assert u0[0, 0] < 0.1  # Should be small at corners
    
    def test_circular_wave(self):
        u0 = InitialConditions.circular_wave((20, 20), center=(10, 10), radius=5, amplitude=1.0)
        assert u0.shape == (20, 20)
        assert np.max(u0) > 0.1  # Should have some amplitude
    
    def test_multiple_sources(self):
        sources = [(5, 5, 10.0), (15, 15, 20.0)]
        u0 = InitialConditions.multiple_sources((20, 20), sources)
        assert u0.shape == (20, 20)
        assert u0[5, 5] == 10.0
        assert u0[15, 15] == 20.0
        assert u0[0, 0] == 0.0
    
    def test_sine_wave_x(self):
        u0 = InitialConditions.sine_wave((20, 20), wavelength=10, amplitude=2.0, direction='x')
        assert u0.shape == (20, 20)
        assert np.max(np.abs(u0)) == pytest.approx(2.0, abs=0.1)  # Relaxed tolerance for discrete sampling
    
    def test_sine_wave_y(self):
        u0 = InitialConditions.sine_wave((20, 20), wavelength=10, amplitude=2.0, direction='y')
        assert u0.shape == (20, 20)
        assert np.max(np.abs(u0)) == pytest.approx(2.0, abs=0.1)  # Relaxed tolerance for discrete sampling
    
    def test_sine_wave_diagonal(self):
        u0 = InitialConditions.sine_wave((20, 20), wavelength=10, amplitude=2.0, direction='diagonal')
        assert u0.shape == (20, 20)
        assert np.max(np.abs(u0)) == pytest.approx(2.0, abs=0.1)  # Relaxed tolerance for discrete sampling
    
    def test_sine_wave_invalid_direction(self):
        with pytest.raises(ValueError, match="direction must be"):
            InitialConditions.sine_wave((20, 20), wavelength=10, direction='invalid')


class TestPDESolverInitialization:
    """Test PDESolver initialization and configuration."""
    
    def test_heat_solver_initialization(self):
        solver = PDESolver('heat', grid_shape=(50, 50))
        assert solver.equation == EquationType.HEAT
        assert solver.grid_shape == (50, 50)
        assert solver.dx == 1.0
        assert solver.dy == 1.0
        assert 'alpha' in solver.parameters
        assert 'dt' in solver.parameters
    
    def test_wave_solver_initialization(self):
        solver = PDESolver(EquationType.WAVE, grid_shape=(30, 40))
        assert solver.equation == EquationType.WAVE
        assert solver.grid_shape == (30, 40)
        assert 'c' in solver.parameters
        assert 'dt' in solver.parameters
    
    def test_custom_spacing(self):
        solver = PDESolver('heat', spacing=(0.5, 2.0))
        assert solver.dx == 0.5
        assert solver.dy == 2.0
    
    def test_custom_boundary_condition(self):
        bc = BoundaryCondition.dirichlet(10.0)
        solver = PDESolver('heat', boundary=bc)
        assert solver.boundary.type == BoundaryType.DIRICHLET
        assert solver.boundary.value == 10.0


class TestPDESolverConfiguration:
    """Test solver parameter setting and validation."""
    
    def test_set_parameters_heat(self):
        solver = PDESolver('heat')
        solver.set_parameters(alpha=0.5, dt=0.05)
        assert solver.parameters['alpha'] == 0.5
        assert solver.parameters['dt'] == 0.05
    
    def test_set_parameters_wave(self):
        solver = PDESolver('wave')
        solver.set_parameters(c=2.0, dt=0.02)
        assert solver.parameters['c'] == 2.0
        assert solver.parameters['dt'] == 0.02
    
    def test_set_invalid_parameter(self):
        solver = PDESolver('heat')
        with pytest.raises(ValueError, match="Unknown parameter"):
            solver.set_parameters(invalid_param=1.0)
    
    def test_set_initial_conditions(self):
        solver = PDESolver('heat', grid_shape=(10, 10))
        u0 = np.random.rand(10, 10)
        solver.set_initial_conditions(u0)
        assert solver._initial_conditions is not None
        assert np.array_equal(solver._initial_conditions, u0)
    
    def test_set_initial_conditions_wrong_shape(self):
        solver = PDESolver('heat', grid_shape=(10, 10))
        u0 = np.random.rand(5, 5)  # Wrong shape
        with pytest.raises(ValueError, match="doesn't match grid shape"):
            solver.set_initial_conditions(u0)
    
    def test_set_initial_velocity_wave(self):
        solver = PDESolver('wave', grid_shape=(10, 10))
        u0 = np.zeros((10, 10))
        v0 = np.ones((10, 10))
        solver.set_initial_conditions(u0, v0)
        assert solver._initial_velocity is not None
        assert np.array_equal(solver._initial_velocity, v0)
    
    def test_set_initial_velocity_wrong_shape(self):
        solver = PDESolver('wave', grid_shape=(10, 10))
        u0 = np.zeros((10, 10))
        v0 = np.ones((5, 5))  # Wrong shape
        with pytest.raises(ValueError, match="doesn't match grid shape"):
            solver.set_initial_conditions(u0, v0)


class TestStabilityValidation:
    """Test stability condition validation."""
    
    def test_heat_stability_info(self):
        solver = PDESolver('heat')
        solver.set_parameters(alpha=0.1, dt=0.1)
        info = solver.get_stability_info()
        
        assert 'condition' in info
        assert 'current_factor' in info
        assert 'limit' in info
        assert 'is_stable' in info
        assert info['limit'] == 0.5
    
    def test_wave_stability_info(self):
        solver = PDESolver('wave')
        solver.set_parameters(c=1.0, dt=0.05)
        info = solver.get_stability_info()
        
        assert 'condition' in info
        assert 'current_factor' in info
        assert 'limit' in info
        assert 'is_stable' in info
        assert info['limit'] == 1.0
    
    def test_heat_stable_parameters(self):
        solver = PDESolver('heat')
        solver.set_parameters(alpha=0.1, dt=0.1)  # Should be stable
        # Should not raise an error
        solver.validate_stability()
    
    def test_heat_unstable_parameters(self):
        solver = PDESolver('heat')
        solver.set_parameters(alpha=1.0, dt=1.0)  # Definitely unstable
        with pytest.raises(ValueError, match="Stability condition violated"):
            solver.validate_stability()
    
    def test_wave_stable_parameters(self):
        solver = PDESolver('wave')
        solver.set_parameters(c=1.0, dt=0.05)  # Should be stable
        # Should not raise an error
        solver.validate_stability()
    
    def test_wave_unstable_parameters(self):
        solver = PDESolver('wave')
        solver.set_parameters(c=2.0, dt=1.0)  # Definitely unstable
        with pytest.raises(ValueError, match="Stability condition violated"):
            solver.validate_stability()


class TestPDESolverSolving:
    """Test actual PDE solving functionality."""
    
    def test_heat_solve_requires_initial_conditions(self):
        solver = PDESolver('heat')
        with pytest.raises(ValueError, match="Initial conditions not set"):
            solver.solve(steps=10)
    
    def test_wave_solve_requires_initial_conditions(self):
        solver = PDESolver('wave')
        with pytest.raises(ValueError, match="Initial conditions not set"):
            solver.solve(steps=10)
    
    def test_heat_solve_with_initial_conditions(self):
        solver = PDESolver('heat', grid_shape=(10, 10))
        solver.set_parameters(alpha=0.1, dt=0.1)
        u0 = InitialConditions.constant((10, 10), 5.0)
        solver.set_initial_conditions(u0)
        
        result = solver.solve(steps=10)
        assert result.shape == (10, 10)
        # Constant field should remain approximately constant
        assert np.allclose(result, 5.0, atol=1e-10)
    
    def test_wave_solve_with_initial_conditions(self):
        solver = PDESolver('wave', grid_shape=(10, 10))
        solver.set_parameters(c=1.0, dt=0.05)
        u0 = InitialConditions.gaussian_pulse((10, 10), center=(5, 5), sigma=1)
        solver.set_initial_conditions(u0)
        
        result = solver.solve(steps=10)
        assert result.shape == (10, 10)
        assert np.all(np.isfinite(result))
    
    def test_heat_animation_creation(self):
        solver = PDESolver('heat', grid_shape=(10, 10))
        solver.set_parameters(alpha=0.1, dt=0.1)
        u0 = InitialConditions.gaussian_pulse((10, 10), center=(5, 5), sigma=1)
        solver.set_initial_conditions(u0)
        
        anim = solver.animate(frames=5)
        assert anim is not None
    
    def test_wave_animation_creation(self):
        solver = PDESolver('wave', grid_shape=(10, 10))
        solver.set_parameters(c=1.0, dt=0.05)
        u0 = InitialConditions.gaussian_pulse((10, 10), center=(5, 5), sigma=1)
        solver.set_initial_conditions(u0)
        
        anim = solver.animate(frames=5)
        assert anim is not None


class TestPDESolverInfo:
    """Test solver information and summary methods."""
    
    def test_info_method(self):
        solver = PDESolver('heat', grid_shape=(20, 30))
        solver.set_parameters(alpha=0.2, dt=0.05)
        u0 = InitialConditions.zeros((20, 30))
        solver.set_initial_conditions(u0)
        
        info = solver.info()
        assert isinstance(info, str)
        assert 'Heat' in info
        assert '(20, 30)' in info
        assert 'alpha: 0.2' in info
        assert 'dt: 0.05' in info


class TestIntegrationExamples:
    """Test complete usage examples."""
    
    def test_complete_heat_workflow(self):
        # Create solver
        solver = PDESolver(
            equation='heat',
            grid_shape=(20, 20),
            spacing=(1.0, 1.0),
            boundary=BoundaryCondition.dirichlet(0.0)
        )
        
        # Set parameters
        solver.set_parameters(alpha=0.25, dt=0.1)
        
        # Create initial conditions
        u0 = InitialConditions.multiple_sources(
            (20, 20), 
            [(10, 10, 100.0), (5, 15, 50.0)]
        )
        solver.set_initial_conditions(u0)
        
        # Solve
        result = solver.solve(steps=50)
        assert result.shape == (20, 20)
        assert np.all(np.isfinite(result))
        
        # Create animation
        anim = solver.animate(frames=10)
        assert anim is not None
    
    def test_complete_wave_workflow(self):
        # Create solver
        solver = PDESolver(
            equation='wave',
            grid_shape=(30, 30),
            spacing=(1.0, 1.0)
        )
        
        # Set parameters
        solver.set_parameters(c=1.0, dt=0.05)
        
        # Create initial conditions
        u0 = InitialConditions.gaussian_pulse((30, 30), center=(15, 15), sigma=3)
        v0 = InitialConditions.zeros((30, 30))
        solver.set_initial_conditions(u0, v0)
        
        # Solve
        result = solver.solve(steps=100)
        assert result.shape == (30, 30)
        assert np.all(np.isfinite(result))
        
        # Create animation
        anim = solver.animate(frames=20)
        assert anim is not None