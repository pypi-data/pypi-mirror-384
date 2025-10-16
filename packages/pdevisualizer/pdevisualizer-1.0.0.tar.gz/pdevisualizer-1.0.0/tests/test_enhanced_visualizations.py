import numpy as np
import pytest
import matplotlib.pyplot as plt
from pdevisualizer.enhanced_visualizations import EnhancedVisualizer
from pdevisualizer.parameter_exploration import ParameterExplorer, ParameterSweepResult
from pdevisualizer.solver import InitialConditions, BoundaryCondition, PDESolver


class TestEnhancedVisualizer:
    """Test EnhancedVisualizer class functionality."""
    
    def test_plot_contours_filled(self):
        """Test filled contour plot creation."""
        # Create test solution with some structure
        solution = np.random.rand(25, 25)
        
        fig = EnhancedVisualizer.plot_contours(solution, title="Test Contours", fill_contours=True)
        
        assert fig is not None
        axes = fig.get_axes()
        assert len(axes) == 2  # contour plot + colorbar
        
        plt.close(fig)
    
    def test_plot_contours_lines_only(self):
        """Test line-only contour plot creation."""
        solution = np.random.rand(20, 20)
        
        fig = EnhancedVisualizer.plot_contours(
            solution, 
            title="Line Contours",
            fill_contours=False,
            levels=10
        )
        
        assert fig is not None
        axes = fig.get_axes()
        assert len(axes) == 2  # contour plot + colorbar
        
        plt.close(fig)
    
    def test_plot_solution_evolution_heatmap(self):
        """Test solution evolution plot with heatmap visualization."""
        # Create test solutions at different time points
        solutions = []
        time_points = [0.0, 0.5, 1.0, 1.5]
        
        for t in time_points:
            solution = np.exp(-t) * np.random.rand(15, 15)
            solutions.append(solution)
        
        fig = EnhancedVisualizer.plot_solution_evolution(
            solutions, time_points, title="Evolution Test", plot_type='heatmap'
        )
        
        assert fig is not None
        axes = fig.get_axes()
        assert len(axes) >= 4  # 4 time points + colorbar
        
        plt.close(fig)
    
    def test_plot_solution_evolution_contour(self):
        """Test solution evolution plot with contour visualization."""
        solutions = []
        time_points = [0.0, 0.5, 1.0]
        
        for t in time_points:
            # Create structured solution
            solution = np.exp(-t) * np.random.rand(20, 20)
            solutions.append(solution)
        
        fig = EnhancedVisualizer.plot_solution_evolution(
            solutions, time_points, title="Contour Evolution", plot_type='contour'
        )
        
        assert fig is not None
        axes = fig.get_axes()
        assert len(axes) >= 3  # 3 time points + colorbar
        
        plt.close(fig)
    
    def test_plot_parameter_landscape_small(self):
        """Test parameter landscape visualization with small resolution."""
        # Create explorer with simple setup
        explorer = ParameterExplorer('heat', grid_shape=(10, 10))
        u0 = InitialConditions.gaussian_pulse((10, 10), center=(5, 5), sigma=2)
        explorer.set_initial_conditions(u0)
        
        # Test small parameter landscape (3x3 for speed)
        fig = EnhancedVisualizer.plot_parameter_landscape(
            explorer, 
            'alpha', (0.1, 0.3), 
            'dt', (0.05, 0.1),
            metric='max_value',
            resolution=3,
            figsize=(10, 8)
        )
        
        assert fig is not None
        axes = fig.get_axes()
        assert len(axes) == 5  # main plot + colorbar + 2 marginals + empty
        
        plt.close(fig)
    
    def test_plot_solution_comparison_enhanced(self):
        """Test enhanced solution comparison with multiple plot types."""
        # Create test solutions
        solutions = {
            'Solution A': np.random.rand(15, 15),
            'Solution B': np.random.rand(15, 15),
            'Solution C': np.random.rand(15, 15)
        }
        
        # Test with heatmap and contour plots
        fig = EnhancedVisualizer.plot_solution_comparison_enhanced(
            solutions, 
            plot_types=['heatmap', 'contour'],
            figsize=(15, 10)
        )
        
        assert fig is not None
        axes = fig.get_axes()
        assert len(axes) >= 6  # 2 plot types × 3 solutions + colorbar
        
        plt.close(fig)
    
    def test_plot_parameter_sweep_enhanced(self):
        """Test enhanced parameter sweep visualization."""
        # Create mock parameter sweep result
        param_values = np.array([0.1, 0.2, 0.3])
        solutions = [np.random.rand(12, 12) for _ in range(3)]
        metrics = {
            'max_value': np.array([1.0, 0.8, 0.6]),
            'min_value': np.array([0.1, 0.1, 0.1]),
            'total_energy': np.array([50.0, 40.0, 30.0]),
            'center_value': np.array([0.9, 0.7, 0.5])
        }
        
        sweep_result = ParameterSweepResult(
            parameter_name='alpha',
            parameter_values=param_values,
            solutions=solutions,
            metrics=metrics,
            solver_config={'steps': 100},
            execution_time=1.0
        )
        
        # Test with heatmaps and contours
        fig = EnhancedVisualizer.plot_parameter_sweep_enhanced(
            sweep_result,
            include_heatmaps=True,
            include_contours=True,
            figsize=(15, 12)
        )
        
        assert fig is not None
        axes = fig.get_axes()
        assert len(axes) >= 7  # metrics + 3 solutions in heatmap + 3 solutions in contour
        
        plt.close(fig)
    
    def test_plot_parameter_sweep_enhanced_minimal(self):
        """Test enhanced parameter sweep with minimal options."""
        # Create minimal sweep result
        param_values = np.array([0.1, 0.2])
        solutions = [np.random.rand(10, 10) for _ in range(2)]
        metrics = {
            'max_value': np.array([1.0, 0.8]),
            'total_energy': np.array([50.0, 40.0])
        }
        
        sweep_result = ParameterSweepResult(
            parameter_name='c',
            parameter_values=param_values,
            solutions=solutions,
            metrics=metrics,
            solver_config={'steps': 50},
            execution_time=0.5
        )
        
        # Test with neither heatmaps nor contours
        fig = EnhancedVisualizer.plot_parameter_sweep_enhanced(
            sweep_result,
            include_heatmaps=False,
            include_contours=False,
            figsize=(10, 6)
        )
        
        assert fig is not None
        axes = fig.get_axes()
        assert len(axes) == 1  # just metrics
        
        plt.close(fig)
    
    def test_plot_wave_comparison(self):
        """Test wave-specific comparison visualization."""
        # Create test wave solutions (with positive and negative values)
        solutions = {
            'Wave A': np.random.rand(10, 10) - 0.5,
            'Wave B': np.random.rand(10, 10) - 0.5
        }
        
        fig = EnhancedVisualizer.plot_wave_comparison(
            solutions,
            symmetric_colormap=True,
            figsize=(12, 6)
        )
        
        assert fig is not None
        axes = fig.get_axes()
        assert len(axes) >= 2  # 2 solutions + colorbar
        
        plt.close(fig)
    
    def test_plot_heat_comparison(self):
        """Test heat-specific comparison visualization."""
        # Create test heat solutions
        solutions = {
            'Heat A': np.random.rand(10, 10),
            'Heat B': np.random.rand(10, 10)
        }
        
        fig = EnhancedVisualizer.plot_heat_comparison(
            solutions,
            figsize=(12, 6)
        )
        
        assert fig is not None
        axes = fig.get_axes()
        assert len(axes) >= 2  # 2 solutions + colorbar
        
        plt.close(fig)


class TestEnhancedVisualizationIntegration:
    """Test integration of enhanced visualizations with parameter exploration."""
    
    def test_heat_equation_contour_visualization(self):
        """Test contour visualization of heat equation solutions."""
        # Create explorer
        explorer = ParameterExplorer('heat', grid_shape=(20, 20))
        u0 = InitialConditions.gaussian_pulse((20, 20), center=(10, 10), sigma=4)
        explorer.set_initial_conditions(u0)
        
        # Run parameter sweep
        alpha_values = np.array([0.1, 0.3])
        sweep_result = explorer.parameter_sweep('alpha', alpha_values, 
                                               custom_params={'steps': 50})
        
        # Test contour visualization of solutions
        for i, solution in enumerate(sweep_result.solutions):
            fig = EnhancedVisualizer.plot_contours(
                solution, 
                title=f"Heat Solution (α={alpha_values[i]:.1f})",
                fill_contours=True,
                cmap='hot'
            )
            assert fig is not None
            plt.close(fig)
    
    def test_wave_equation_evolution_visualization(self):
        """Test evolution visualization of wave equation solutions."""
        # Create explorer
        explorer = ParameterExplorer('wave', grid_shape=(20, 20))
        u0 = InitialConditions.gaussian_pulse((20, 20), center=(10, 10), sigma=4)
        explorer.set_initial_conditions(u0)
        
        # Generate solutions at different time points
        time_points = [0.0, 1.0, 2.0]
        solutions = []
        
        for t in time_points:
            if t == 0.0:
                solutions.append(u0)
            else:
                steps = int(t * 50)
                solver = PDESolver('wave', grid_shape=(20, 20))
                solver.set_parameters(c=1.0, dt=0.05)
                solver.set_initial_conditions(u0)
                solution = solver.solve(steps=steps)
                solutions.append(solution)
        
        # Test evolution visualization
        fig = EnhancedVisualizer.plot_solution_evolution(
            solutions, time_points, title="Wave Evolution", plot_type='heatmap'
        )
        
        assert fig is not None
        plt.close(fig)
    
    def test_boundary_condition_visualization(self):
        """Test visualization with different boundary conditions."""
        boundary_conditions = [
            ('Dirichlet', BoundaryCondition.dirichlet(0.0)),
            ('Neumann', BoundaryCondition.neumann(0.0))
        ]
        
        solutions = {}
        
        for name, boundary in boundary_conditions:
            explorer = ParameterExplorer('heat', grid_shape=(15, 15), boundary=boundary)
            u0 = InitialConditions.gaussian_pulse((15, 15), center=(7, 7), sigma=3)
            explorer.set_initial_conditions(u0)
            
            # Quick solve
            solver = PDESolver('heat', grid_shape=(15, 15), boundary=boundary)
            solver.set_parameters(alpha=0.2, dt=0.1)
            solver.set_initial_conditions(u0)
            solution = solver.solve(steps=50)
            
            solutions[name] = solution
        
        # Test enhanced comparison
        fig = EnhancedVisualizer.plot_solution_comparison_enhanced(
            solutions,
            plot_types=['heatmap', 'contour'],
            figsize=(12, 8)
        )
        
        assert fig is not None
        plt.close(fig)


class TestEnhancedVisualizationEdgeCases:
    """Test edge cases and error conditions."""
    
    def test_single_solution_evolution(self):
        """Test evolution plot with single solution."""
        solution = np.random.rand(10, 10)
        time_points = [0.0]
        
        fig = EnhancedVisualizer.plot_solution_evolution(
            [solution], time_points, plot_type='heatmap'
        )
        
        assert fig is not None
        plt.close(fig)
    
    def test_empty_solutions_dict(self):
        """Test enhanced comparison with empty solutions dict."""
        with pytest.raises(ValueError, match="No solutions provided"):
            EnhancedVisualizer.plot_solution_comparison_enhanced({})
    
    def test_parameter_landscape_missing_initial_conditions(self):
        """Test parameter landscape with missing initial conditions."""
        explorer = ParameterExplorer('heat', grid_shape=(10, 10))
        # Don't set initial conditions
        
        with pytest.raises(ValueError, match="Initial conditions not set"):
            EnhancedVisualizer.plot_parameter_landscape(
                explorer, 'alpha', (0.1, 0.3), 'dt', (0.05, 0.1), resolution=2
            )
    
    def test_small_solution_arrays(self):
        """Test visualizations with very small solution arrays."""
        solution = np.random.rand(3, 3)
        
        # Test contours
        fig = EnhancedVisualizer.plot_contours(solution)
        assert fig is not None
        plt.close(fig)
    
    def test_parameter_sweep_single_solution(self):
        """Test enhanced parameter sweep with single solution."""
        param_values = np.array([0.25])
        solutions = [np.random.rand(10, 10)]
        metrics = {
            'max_value': np.array([1.0]),
            'total_energy': np.array([50.0])
        }
        
        sweep_result = ParameterSweepResult(
            parameter_name='alpha',
            parameter_values=param_values,
            solutions=solutions,
            metrics=metrics,
            solver_config={'steps': 100},
            execution_time=1.0
        )
        
        fig = EnhancedVisualizer.plot_parameter_sweep_enhanced(
            sweep_result, include_heatmaps=True, include_contours=False
        )
        
        assert fig is not None
        plt.close(fig)