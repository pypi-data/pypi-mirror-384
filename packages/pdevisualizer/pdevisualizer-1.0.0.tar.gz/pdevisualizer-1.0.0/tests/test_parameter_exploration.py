import numpy as np
import pytest
import matplotlib.pyplot as plt
from pdevisualizer.parameter_exploration import (
    ParameterExplorer, ParameterVisualizer, ParameterSweepResult
)
from pdevisualizer.solver import BoundaryCondition, InitialConditions


class TestParameterExplorer:
    """Test ParameterExplorer class functionality."""
    
    def test_explorer_initialization_heat(self):
        explorer = ParameterExplorer('heat', grid_shape=(20, 20))
        assert explorer.equation == 'heat'
        assert explorer.grid_shape == (20, 20)
        assert 'alpha' in explorer.default_params
        assert 'dt' in explorer.default_params
        assert 'steps' in explorer.default_params
    
    def test_explorer_initialization_wave(self):
        explorer = ParameterExplorer('wave', grid_shape=(30, 30))
        assert explorer.equation == 'wave'
        assert explorer.grid_shape == (30, 30)
        assert 'c' in explorer.default_params
        assert 'dt' in explorer.default_params
        assert 'steps' in explorer.default_params
    
    def test_explorer_invalid_equation(self):
        with pytest.raises(ValueError, match="Unknown equation type"):
            ParameterExplorer('invalid')
    
    def test_set_initial_conditions(self):
        explorer = ParameterExplorer('heat', grid_shape=(10, 10))
        u0 = np.random.rand(10, 10)
        explorer.set_initial_conditions(u0)
        
        # Check that initial conditions are set and not None
        assert explorer.initial_conditions is not None
        assert np.array_equal(explorer.initial_conditions, u0)
    
    def test_set_initial_conditions_with_velocity(self):
        explorer = ParameterExplorer('wave', grid_shape=(10, 10))
        u0 = np.random.rand(10, 10)
        v0 = np.random.rand(10, 10)
        explorer.set_initial_conditions(u0, v0)
        
        # Check that both initial conditions and velocity are set and not None
        assert explorer.initial_conditions is not None
        assert explorer.initial_velocity is not None
        assert np.array_equal(explorer.initial_conditions, u0)
        assert np.array_equal(explorer.initial_velocity, v0)


class TestParameterSweep:
    """Test parameter sweep functionality."""
    
    def test_heat_alpha_sweep(self):
        explorer = ParameterExplorer('heat', grid_shape=(20, 20))
        
        # Set initial conditions
        u0 = InitialConditions.gaussian_pulse((20, 20), center=(10, 10), sigma=3)
        explorer.set_initial_conditions(u0)
        
        # Run parameter sweep
        alpha_values = np.linspace(0.1, 0.5, 3)
        result = explorer.parameter_sweep('alpha', alpha_values)
        
        # Verify results
        assert isinstance(result, ParameterSweepResult)
        assert result.parameter_name == 'alpha'
        assert len(result.solutions) == 3
        assert len(result.parameter_values) == 3
        assert np.array_equal(result.parameter_values, alpha_values)
        
        # Check metrics
        assert 'max_value' in result.metrics
        assert 'min_value' in result.metrics
        assert 'total_energy' in result.metrics
        assert 'center_value' in result.metrics
        
        # All solutions should have correct shape
        for solution in result.solutions:
            assert solution.shape == (20, 20)
    
    def test_wave_c_sweep(self):
        explorer = ParameterExplorer('wave', grid_shape=(15, 15))
        
        # Set initial conditions
        u0 = InitialConditions.circular_wave((15, 15), center=(7, 7), radius=3)
        explorer.set_initial_conditions(u0)
        
        # Run parameter sweep
        c_values = np.array([0.5, 1.0, 1.5])
        result = explorer.parameter_sweep('c', c_values,
                                        custom_params={'steps': 50})
        
        # Verify results
        assert result.parameter_name == 'c'
        assert len(result.solutions) == 3
        assert result.solver_config['steps'] == 50
        
        # Check that different wave speeds produce different results
        assert not np.array_equal(result.solutions[0], result.solutions[1])
        assert not np.array_equal(result.solutions[1], result.solutions[2])
    
    def test_parameter_sweep_no_initial_conditions(self):
        explorer = ParameterExplorer('heat')
        with pytest.raises(ValueError, match="Initial conditions not set"):
            explorer.parameter_sweep('alpha', np.array([0.1, 0.2]))
    
    def test_parameter_sweep_invalid_parameter(self):
        explorer = ParameterExplorer('heat', grid_shape=(10, 10))  # Match initial conditions shape
        u0 = InitialConditions.zeros((10, 10))
        explorer.set_initial_conditions(u0)
        
        # This should not raise an error during sweep setup,
        # but might fail during individual solver runs
        result = explorer.parameter_sweep('invalid_param', np.array([0.1, 0.2]))
        
        # The sweep should complete but solutions might be zeros due to solver failures
        assert len(result.solutions) == 2


class TestParameterComparison:
    """Test parameter comparison functionality."""
    
    def test_compare_heat_parameters(self):
        explorer = ParameterExplorer('heat', grid_shape=(15, 15))
        
        # Set initial conditions
        u0 = InitialConditions.gaussian_pulse((15, 15), center=(7, 7), sigma=2)
        explorer.set_initial_conditions(u0)
        
        # Define parameter configurations
        configs = [
            {'alpha': 0.1, 'dt': 0.1, 'steps': 50},
            {'alpha': 0.3, 'dt': 0.1, 'steps': 50},
            {'alpha': 0.5, 'dt': 0.1, 'steps': 50}
        ]
        labels = ['Low α', 'Medium α', 'High α']
        
        # Compare configurations
        results = explorer.compare_parameters(configs, labels)
        
        # Verify results
        assert len(results) == 3
        assert 'Low α' in results
        assert 'Medium α' in results
        assert 'High α' in results
        
        # All solutions should have correct shape
        for solution in results.values():
            assert solution.shape == (15, 15)
        
        # Different alphas should produce different results
        assert not np.array_equal(results['Low α'], results['High α'])
    
    def test_compare_wave_parameters(self):
        explorer = ParameterExplorer('wave', grid_shape=(20, 20))
        
        # Set initial conditions
        u0 = InitialConditions.gaussian_pulse((20, 20), center=(10, 10), sigma=3)
        explorer.set_initial_conditions(u0)
        
        # Define parameter configurations
        configs = [
            {'c': 0.5, 'dt': 0.05, 'steps': 100},
            {'c': 1.5, 'dt': 0.05, 'steps': 100}
        ]
        
        # Compare configurations (no labels provided)
        results = explorer.compare_parameters(configs)
        
        # Verify results
        assert len(results) == 2
        assert 'Config 1' in results
        assert 'Config 2' in results
        
        # Different wave speeds should produce different results
        assert not np.array_equal(results['Config 1'], results['Config 2'])
    
    def test_compare_parameters_no_initial_conditions(self):
        explorer = ParameterExplorer('heat')
        configs = [{'alpha': 0.1}]
        
        with pytest.raises(ValueError, match="Initial conditions not set"):
            explorer.compare_parameters(configs)


class TestSensitivityAnalysis:
    """Test sensitivity analysis functionality."""
    
    def test_sensitivity_analysis_heat(self):
        explorer = ParameterExplorer('heat', grid_shape=(15, 15))
        
        # Set initial conditions
        u0 = InitialConditions.gaussian_pulse((15, 15), center=(7, 7), sigma=2)
        explorer.set_initial_conditions(u0)
        
        # Run sensitivity analysis
        result = explorer.sensitivity_analysis('alpha', base_value=0.25,
                                             perturbation_percent=20.0,
                                             n_samples=5)
        
        # Verify results
        assert result['parameter_name'] == 'alpha'
        assert result['base_value'] == 0.25
        assert result['perturbation_percent'] == 20.0
        assert len(result['parameter_values']) == 5
        
        # Check that parameter values are around base value
        param_values = result['parameter_values']
        assert np.min(param_values) < 0.25
        assert np.max(param_values) > 0.25
        
        # Check sweep result
        sweep_result = result['sweep_result']
        assert isinstance(sweep_result, ParameterSweepResult)
        assert len(sweep_result.solutions) == 5
        
        # Check sensitivity metrics
        sensitivity_metrics = result['sensitivity_metrics']
        assert isinstance(sensitivity_metrics, dict)
        assert 'max_value' in sensitivity_metrics
        assert 'total_energy' in sensitivity_metrics
    
    def test_sensitivity_analysis_single_sample(self):
        explorer = ParameterExplorer('heat', grid_shape=(10, 10))
        
        # Set initial conditions
        u0 = InitialConditions.zeros((10, 10))
        u0[5, 5] = 1.0
        explorer.set_initial_conditions(u0)
        
        # Run sensitivity analysis with single sample
        result = explorer.sensitivity_analysis('alpha', base_value=0.2,
                                             n_samples=1)
        
        # Should handle single sample gracefully
        assert len(result['parameter_values']) == 1
        assert result['parameter_values'][0] == 0.2


class TestParameterVisualizer:
    """Test visualization functionality."""
    
    def test_plot_parameter_sweep(self):
        # Create mock sweep result
        param_values = np.array([0.1, 0.2, 0.3])
        solutions = [np.random.rand(10, 10) for _ in range(3)]
        metrics = {
            'max_value': np.array([1.0, 1.5, 2.0]),
            'min_value': np.array([0.0, 0.1, 0.2]),
            'total_energy': np.array([50.0, 75.0, 100.0])
        }
        
        sweep_result = ParameterSweepResult(
            parameter_name='alpha',
            parameter_values=param_values,
            solutions=solutions,
            metrics=metrics,
            solver_config={'steps': 100},
            execution_time=1.0
        )
        
        # Test plotting
        fig = ParameterVisualizer.plot_parameter_sweep(sweep_result)
        assert fig is not None
        
        # Check that figure has correct number of subplots
        axes = fig.get_axes()
        assert len(axes) == 3  # One for each metric
        
        plt.close(fig)  # Clean up
    
    def test_plot_solution_comparison(self):
        # Create mock solutions
        solutions = {
            'Config 1': np.random.rand(10, 10),
            'Config 2': np.random.rand(10, 10),
            'Config 3': np.random.rand(10, 10)
        }
        
        # Test plotting
        fig = ParameterVisualizer.plot_solution_comparison(solutions)
        assert fig is not None
        
        # Check that figure has correct number of subplots
        axes = fig.get_axes()
        assert len(axes) == 4  # 3 solutions + 1 colorbar
        
        plt.close(fig)  # Clean up
    
    def test_plot_sensitivity_analysis(self):
        # Create mock sensitivity result
        param_values = np.array([0.2, 0.25, 0.3])
        solutions = [np.random.rand(10, 10) for _ in range(3)]
        metrics = {
            'max_value': np.array([1.0, 1.2, 1.4]),
            'total_energy': np.array([50.0, 60.0, 70.0])
        }
        
        sweep_result = ParameterSweepResult(
            parameter_name='alpha',
            parameter_values=param_values,
            solutions=solutions,
            metrics=metrics,
            solver_config={'steps': 100},
            execution_time=1.0
        )
        
        sensitivity_result = {
            'parameter_name': 'alpha',
            'base_value': 0.25,
            'perturbation_percent': 20.0,
            'parameter_values': param_values,
            'sweep_result': sweep_result,
            'sensitivity_metrics': {
                'max_value': 0.5,
                'total_energy': 0.3
            }
        }
        
        # Test plotting
        fig = ParameterVisualizer.plot_sensitivity_analysis(sensitivity_result)
        assert fig is not None
        
        # Check that figure has 2 subplots
        axes = fig.get_axes()
        assert len(axes) == 2
        
        plt.close(fig)  # Clean up
    
    def test_plot_parameter_grid(self):
        # Create explorer with initial conditions
        explorer = ParameterExplorer('heat', grid_shape=(10, 10))
        u0 = InitialConditions.gaussian_pulse((10, 10), center=(5, 5), sigma=2)
        explorer.set_initial_conditions(u0)
        
        # Test small parameter grid
        param1_values = np.array([0.1, 0.2])
        param2_values = np.array([0.05, 0.1])
        
        fig = ParameterVisualizer.plot_parameter_grid(
            explorer, 'alpha', param1_values, 'dt', param2_values,
            figsize=(8, 6)
        )
        
        assert fig is not None
        
        # Check that figure has correct number of subplots (2x2 grid + colorbar)
        axes = fig.get_axes()
        assert len(axes) == 5  # 4 subplots + 1 colorbar
        
        plt.close(fig)  # Clean up


class TestIntegrationExamples:
    """Test complete parameter exploration workflows."""
    
    def test_complete_heat_exploration_workflow(self):
        # Create explorer
        explorer = ParameterExplorer('heat', grid_shape=(15, 15))
        
        # Set initial conditions with multiple heat sources
        u0 = InitialConditions.multiple_sources(
            (15, 15),
            [(5, 5, 100.0), (10, 10, 80.0)]
        )
        explorer.set_initial_conditions(u0)
        
        # Run parameter sweep
        alpha_values = np.linspace(0.1, 0.3, 3)
        sweep_result = explorer.parameter_sweep('alpha', alpha_values,
                                              custom_params={'steps': 50})
        
        # Verify sweep worked
        assert len(sweep_result.solutions) == 3
        assert sweep_result.execution_time >= 0
        
        # Run parameter comparison
        configs = [
            {'alpha': 0.1, 'dt': 0.1},
            {'alpha': 0.3, 'dt': 0.1}
        ]
        comparison_results = explorer.compare_parameters(configs,
                                                       ['Low α', 'High α'])
        
        # Verify comparison worked
        assert len(comparison_results) == 2
        assert 'Low α' in comparison_results
        assert 'High α' in comparison_results
        
        # Run sensitivity analysis
        sensitivity_result = explorer.sensitivity_analysis('alpha', 0.2,
                                                          perturbation_percent=10)
        
        # Verify sensitivity analysis worked
        assert sensitivity_result['parameter_name'] == 'alpha'
        assert sensitivity_result['base_value'] == 0.2
        
        # Test visualization
        fig1 = ParameterVisualizer.plot_parameter_sweep(sweep_result)
        fig2 = ParameterVisualizer.plot_solution_comparison(comparison_results)
        fig3 = ParameterVisualizer.plot_sensitivity_analysis(sensitivity_result)
        
        assert fig1 is not None
        assert fig2 is not None
        assert fig3 is not None
        
        plt.close(fig1)
        plt.close(fig2)
        plt.close(fig3)
    
    def test_complete_wave_exploration_workflow(self):
        # Create explorer
        explorer = ParameterExplorer('wave', grid_shape=(20, 20))
        
        # Set initial conditions
        u0 = InitialConditions.gaussian_pulse((20, 20), center=(10, 10), sigma=3)
        explorer.set_initial_conditions(u0)
        
        # Run parameter sweep for wave speed
        c_values = np.array([0.5, 1.0, 1.5])
        sweep_result = explorer.parameter_sweep('c', c_values,
                                              custom_params={'steps': 100})
        
        # Verify sweep worked
        assert len(sweep_result.solutions) == 3
        assert sweep_result.parameter_name == 'c'
        
        # Run parameter comparison with different time steps
        configs = [
            {'c': 1.0, 'dt': 0.02},
            {'c': 1.0, 'dt': 0.05},
            {'c': 1.0, 'dt': 0.08}
        ]
        comparison_results = explorer.compare_parameters(configs,
                                                       ['Fine dt', 'Medium dt', 'Coarse dt'])
        
        # Verify comparison worked
        assert len(comparison_results) == 3
        
        # Different time steps should produce different results
        assert not np.array_equal(comparison_results['Fine dt'], comparison_results['Coarse dt'])
        
        # Test visualization
        fig1 = ParameterVisualizer.plot_parameter_sweep(sweep_result,
                                                       metric_names=['max_value', 'total_energy'])
        fig2 = ParameterVisualizer.plot_solution_comparison(comparison_results)
        
        assert fig1 is not None
        assert fig2 is not None
        
        plt.close(fig1)
        plt.close(fig2)
    
    def test_boundary_condition_parameter_exploration(self):
        # Test parameter exploration with different boundary conditions
        boundary_conditions = [
            BoundaryCondition.dirichlet(0.0),
            BoundaryCondition.neumann(0.0),
            BoundaryCondition.periodic()
        ]
        
        for boundary in boundary_conditions:
            explorer = ParameterExplorer('heat', grid_shape=(15, 15), boundary=boundary)
            
            # Set initial conditions
            u0 = InitialConditions.gaussian_pulse((15, 15), center=(7, 7), sigma=2)
            explorer.set_initial_conditions(u0)
            
            # Run small parameter sweep
            alpha_values = np.array([0.1, 0.2])
            sweep_result = explorer.parameter_sweep('alpha', alpha_values,
                                                  custom_params={'steps': 30})
            
            # Should work with all boundary conditions
            assert len(sweep_result.solutions) == 2
            
            # Solutions should be different for different alphas
            assert not np.array_equal(sweep_result.solutions[0], sweep_result.solutions[1])


class TestParameterExplorationEdgeCases:
    """Test edge cases and error conditions."""
    
    def test_empty_parameter_values(self):
        explorer = ParameterExplorer('heat', grid_shape=(10, 10))
        u0 = InitialConditions.zeros((10, 10))
        explorer.set_initial_conditions(u0)
        
        # Empty parameter array
        result = explorer.parameter_sweep('alpha', np.array([]))
        assert len(result.solutions) == 0
        assert len(result.parameter_values) == 0
    
    def test_single_parameter_value(self):
        explorer = ParameterExplorer('heat', grid_shape=(10, 10))
        u0 = InitialConditions.zeros((10, 10))
        explorer.set_initial_conditions(u0)
        
        # Single parameter value
        result = explorer.parameter_sweep('alpha', np.array([0.25]))
        assert len(result.solutions) == 1
        assert len(result.parameter_values) == 1
        assert result.parameter_values[0] == 0.25
    
    def test_very_small_grid(self):
        explorer = ParameterExplorer('heat', grid_shape=(3, 3))
        u0 = InitialConditions.zeros((3, 3))
        u0[1, 1] = 1.0
        explorer.set_initial_conditions(u0)
        
        # Should work with very small grids
        result = explorer.parameter_sweep('alpha', np.array([0.1, 0.2]))
        assert len(result.solutions) == 2
        for solution in result.solutions:
            assert solution.shape == (3, 3)
    
    def test_compare_empty_configs(self):
        explorer = ParameterExplorer('heat', grid_shape=(10, 10))
        u0 = InitialConditions.zeros((10, 10))
        explorer.set_initial_conditions(u0)
        
        # Empty configuration list
        result = explorer.compare_parameters([])
        assert len(result) == 0
    
    def test_compare_single_config(self):
        explorer = ParameterExplorer('heat', grid_shape=(10, 10))
        u0 = InitialConditions.zeros((10, 10))
        explorer.set_initial_conditions(u0)
        
        # Single configuration
        result = explorer.compare_parameters([{'alpha': 0.25}])
        assert len(result) == 1
        assert 'Config 1' in result
    
    def test_initial_conditions_none_check(self):
        """Test that we properly handle None initial conditions."""
        explorer = ParameterExplorer('heat', grid_shape=(10, 10))
        
        # Initially, initial_conditions should be None
        assert explorer.initial_conditions is None
        assert explorer.initial_velocity is None
        
        # After setting, they should not be None
        u0 = np.ones((10, 10))
        explorer.set_initial_conditions(u0)
        assert explorer.initial_conditions is not None
        
        # For wave equation with velocity
        wave_explorer = ParameterExplorer('wave', grid_shape=(10, 10))
        v0 = np.zeros((10, 10))
        wave_explorer.set_initial_conditions(u0, v0)
        assert wave_explorer.initial_conditions is not None
        assert wave_explorer.initial_velocity is not None