"""
Parameter exploration tools for PDEVisualizer.

This module provides tools for exploring how different parameters affect
PDE solutions, including parameter sweeps, comparison grids, and sensitivity analysis.
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
from matplotlib.figure import Figure
from matplotlib.axes import Axes
import matplotlib.patches as patches
from typing import Dict, List, Tuple, Any, Optional, Callable, Union
import itertools
from dataclasses import dataclass
import time

from .solver import PDESolver, BoundaryCondition, InitialConditions


@dataclass
class ParameterSweepResult:
    """Results from a parameter sweep experiment."""
    parameter_name: str
    parameter_values: np.ndarray
    solutions: List[np.ndarray]
    metrics: Dict[str, np.ndarray]
    solver_config: Dict[str, Any]
    execution_time: float


class ParameterExplorer:
    """
    Tool for exploring parameter spaces in PDE solutions.
    
    This class provides methods for systematic parameter exploration,
    comparison studies, and sensitivity analysis.
    """
    
    def __init__(self, equation: str, grid_shape: Tuple[int, int] = (50, 50),
                 boundary: Optional[BoundaryCondition] = None):
        """
        Initialize parameter explorer.
        
        Parameters:
        -----------
        equation : str
            PDE type ('heat' or 'wave')
        grid_shape : tuple
            Grid dimensions
        boundary : BoundaryCondition, optional
            Boundary condition (default: Dirichlet(0))
        """
        self.equation = equation
        self.grid_shape = grid_shape
        self.boundary = boundary or BoundaryCondition.dirichlet(0.0)
        
        # Default parameters based on equation type
        if equation == 'heat':
            self.default_params = {'alpha': 0.25, 'dt': 0.1, 'steps': 100}
        elif equation == 'wave':
            self.default_params = {'c': 1.0, 'dt': 0.05, 'steps': 200}
        else:
            raise ValueError(f"Unknown equation type: {equation}")
        
        # Store base initial conditions
        self.initial_conditions: Optional[np.ndarray] = None
        self.initial_velocity: Optional[np.ndarray] = None
    
    def set_initial_conditions(self, u0: np.ndarray, v0: Optional[np.ndarray] = None):
        """Set initial conditions for parameter exploration."""
        self.initial_conditions = u0.copy()
        if v0 is not None:
            self.initial_velocity = v0.copy()
    
    def parameter_sweep(self, parameter_name: str, parameter_values: Union[np.ndarray, List[float]],
                       custom_params: Optional[Dict[str, Any]] = None,
                       compute_metrics: bool = True) -> ParameterSweepResult:
        """
        Perform a parameter sweep across a range of values.
        
        Parameters:
        -----------
        parameter_name : str
            Name of parameter to vary
        parameter_values : array-like
            Values to test
        custom_params : dict, optional
            Additional parameters to override defaults
        compute_metrics : bool
            Whether to compute solution metrics
            
        Returns:
        --------
        ParameterSweepResult
            Results of the parameter sweep
        """
        if self.initial_conditions is None:
            raise ValueError("Initial conditions not set. Use set_initial_conditions().")
        
        # Convert to numpy array if needed
        param_values = np.array(parameter_values)
        
        start_time = time.time()
        solutions = []
        metrics: Dict[str, List[float]] = {
            'max_value': [], 'min_value': [], 'total_energy': [], 'center_value': []
        }
        
        # Base parameters
        base_params = self.default_params.copy()
        if custom_params:
            base_params.update(custom_params)
        
        print(f"Running parameter sweep for {parameter_name}...")
        
        # Handle empty parameter array
        if len(param_values) == 0:
            print("No parameter values provided.")
        else:
            print(f"Testing {len(param_values)} values: {param_values[0]:.3f} to {param_values[-1]:.3f}")
        
        for i, value in enumerate(param_values):
            print(f"  Progress: {i+1}/{len(param_values)} ({parameter_name}={value:.3f})")
            
            # Update the parameter
            params = base_params.copy()
            params[parameter_name] = value
            
            # Separate solver parameters from solve parameters
            solver_params = {k: v for k, v in params.items() if k in ['alpha', 'c', 'dt', 'dx', 'dy']}
            steps = params.get('steps', 100)
            
            # Create solver
            solver = PDESolver(self.equation, grid_shape=self.grid_shape, boundary=self.boundary)
            solver.set_parameters(**solver_params)
            solver.set_initial_conditions(self.initial_conditions, self.initial_velocity)
            
            # Solve
            try:
                solution = solver.solve(steps=steps)
                solutions.append(solution)
                
                # Compute metrics
                if compute_metrics:
                    metrics['max_value'].append(float(np.max(solution)))
                    metrics['min_value'].append(float(np.min(solution)))
                    metrics['total_energy'].append(float(np.sum(solution**2)))
                    
                    # Center value
                    center_i, center_j = self.grid_shape[0]//2, self.grid_shape[1]//2
                    metrics['center_value'].append(float(solution[center_i, center_j]))
            
            except Exception as e:
                print(f"    Warning: Failed at {parameter_name}={value:.3f}: {e}")
                solutions.append(np.zeros(self.grid_shape))
                if compute_metrics:
                    metrics['max_value'].append(0.0)
                    metrics['min_value'].append(0.0)
                    metrics['total_energy'].append(0.0)
                    metrics['center_value'].append(0.0)
        
        execution_time = time.time() - start_time
        print(f"✅ Parameter sweep completed in {execution_time:.2f} seconds")
        
        # Convert metrics to numpy arrays
        metrics_np: Dict[str, np.ndarray] = {}
        for key, values in metrics.items():
            metrics_np[key] = np.array(values)
        
        return ParameterSweepResult(
            parameter_name=parameter_name,
            parameter_values=param_values,
            solutions=solutions,
            metrics=metrics_np,
            solver_config=base_params,
            execution_time=execution_time
        )
    
    def compare_parameters(self, param_configs: List[Dict[str, Any]],
                          labels: Optional[List[str]] = None) -> Dict[str, np.ndarray]:
        """
        Compare solutions with different parameter configurations.
        
        Parameters:
        -----------
        param_configs : list
            List of parameter dictionaries to compare
        labels : list, optional
            Labels for each configuration
            
        Returns:
        --------
        dict
            Dictionary mapping labels to solutions
        """
        if self.initial_conditions is None:
            raise ValueError("Initial conditions not set. Use set_initial_conditions().")
        
        if labels is None:
            labels = [f"Config {i+1}" for i in range(len(param_configs))]
        
        results = {}
        
        print(f"Comparing {len(param_configs)} parameter configurations...")
        
        for i, (config, label) in enumerate(zip(param_configs, labels)):
            print(f"  Running configuration {i+1}/{len(param_configs)}: {label}")
            
            # Merge with defaults
            params = self.default_params.copy()
            params.update(config)
            
            # Separate solver parameters from solve parameters
            solver_params = {k: v for k, v in params.items() if k in ['alpha', 'c', 'dt', 'dx', 'dy']}
            steps = params.get('steps', 100)
            
            # Create solver
            solver = PDESolver(self.equation, grid_shape=self.grid_shape, boundary=self.boundary)
            solver.set_parameters(**solver_params)
            solver.set_initial_conditions(self.initial_conditions, self.initial_velocity)
            
            # Solve
            try:
                solution = solver.solve(steps=steps)
                results[label] = solution
            except Exception as e:
                print(f"    Warning: Failed for {label}: {e}")
                results[label] = np.zeros(self.grid_shape)
        
        print("✅ Parameter comparison completed")
        return results
    
    def sensitivity_analysis(self, parameter_name: str, base_value: float,
                           perturbation_percent: float = 10.0,
                           n_samples: int = 5) -> Dict[str, Any]:
        """
        Analyze sensitivity to parameter changes.
        
        Parameters:
        -----------
        parameter_name : str
            Parameter to analyze
        base_value : float
            Base parameter value
        perturbation_percent : float
            Percentage perturbation to apply
        n_samples : int
            Number of samples around base value
            
        Returns:
        --------
        dict
            Sensitivity analysis results
        """
        perturbation = base_value * perturbation_percent / 100.0
        
        # Create parameter values around base
        if n_samples == 1:
            param_values = np.array([base_value])
        else:
            param_values = np.linspace(base_value - perturbation, 
                                     base_value + perturbation, n_samples)
        
        # Run parameter sweep
        sweep_result = self.parameter_sweep(parameter_name, param_values)
        
        # Calculate sensitivity metrics
        if len(sweep_result.solutions) > 1:
            # Relative sensitivity: (max_change / base_value) / (param_change / base_param)
            metric_changes = {}
            for metric_name, metric_values in sweep_result.metrics.items():
                if len(metric_values) > 1:
                    max_change = np.max(metric_values) - np.min(metric_values)
                    base_metric = metric_values[len(metric_values)//2]  # Middle value
                    param_change = np.max(param_values) - np.min(param_values)
                    
                    if base_metric != 0 and param_change != 0:
                        relative_sensitivity = (max_change / abs(base_metric)) / (param_change / abs(base_value))
                        metric_changes[metric_name] = relative_sensitivity
                    else:
                        metric_changes[metric_name] = 0.0
        else:
            metric_changes = {}
        
        return {
            'parameter_name': parameter_name,
            'base_value': base_value,
            'perturbation_percent': perturbation_percent,
            'parameter_values': param_values,
            'sweep_result': sweep_result,
            'sensitivity_metrics': metric_changes
        }


class ParameterVisualizer:
    """
    Visualization tools for parameter exploration results.
    """
    
    @staticmethod
    def plot_parameter_sweep(sweep_result: ParameterSweepResult, 
                           metric_names: Optional[List[str]] = None,
                           figsize: Tuple[int, int] = (12, 8)) -> Figure:
        """
        Plot parameter sweep results.
        
        Parameters:
        -----------
        sweep_result : ParameterSweepResult
            Results from parameter sweep
        metric_names : list, optional
            Metrics to plot (default: all)
        figsize : tuple
            Figure size
        """
        if metric_names is None:
            metric_names = list(sweep_result.metrics.keys())
        
        n_metrics = len(metric_names)
        n_cols = min(n_metrics, 2)
        n_rows = (n_metrics + n_cols - 1) // n_cols
        
        fig, axes = plt.subplots(n_rows, n_cols, figsize=figsize)
        
        # Handle different axes configurations
        if n_metrics == 1:
            axes_list = [axes]
        elif n_rows == 1:
            axes_list = list(axes) if hasattr(axes, '__len__') else [axes]
        else:
            axes_list = [axes[i // n_cols, i % n_cols] for i in range(n_metrics)]
        
        param_name = sweep_result.parameter_name
        param_values = sweep_result.parameter_values
        
        for i, metric_name in enumerate(metric_names):
            ax = axes_list[i]
            metric_values = sweep_result.metrics[metric_name]
            
            ax.plot(param_values, metric_values, 'o-', linewidth=2, markersize=6)
            ax.set_xlabel(f'{param_name}')
            ax.set_ylabel(metric_name.replace('_', ' ').title())
            ax.grid(True, alpha=0.3)
            ax.set_title(f'{metric_name.replace("_", " ").title()} vs {param_name}')
        
        # Remove empty subplots
        if n_rows > 1 and n_cols > 1:
            for i in range(n_metrics, n_rows * n_cols):
                row = i // n_cols
                col = i % n_cols
                axes[row, col].remove()
        
        plt.tight_layout()
        plt.suptitle(f'Parameter Sweep: {param_name}', fontsize=16, y=1.02)
        return fig
    
    @staticmethod
    def plot_solution_comparison(solutions: Dict[str, np.ndarray], 
                               figsize: Tuple[int, int] = (15, 5),
                               cmap: str = 'viridis') -> Figure:
        """
        Plot multiple solutions side by side.
        
        Parameters:
        -----------
        solutions : dict
            Dictionary mapping labels to solution arrays
        figsize : tuple
            Figure size
        cmap : str
            Colormap name
        """
        n_solutions = len(solutions)
        fig, axes = plt.subplots(1, n_solutions, figsize=figsize)
        
        # Handle single solution case
        if n_solutions == 1:
            axes_list = [axes]
        else:
            axes_list = list(axes)
        
        # Find common color scale
        vmin = min(np.min(sol) for sol in solutions.values())
        vmax = max(np.max(sol) for sol in solutions.values())
        
        im = None
        for i, (label, solution) in enumerate(solutions.items()):
            im = axes_list[i].imshow(solution, cmap=cmap, origin='lower', 
                                   vmin=vmin, vmax=vmax)
            axes_list[i].set_title(label)
            axes_list[i].set_xlabel('x')
            if i == 0:
                axes_list[i].set_ylabel('y')
        
        # Add colorbar
        if im is not None:
            plt.colorbar(im, ax=axes_list, orientation='vertical', fraction=0.046, pad=0.04)
        
        # Use subplots_adjust instead of tight_layout to avoid colorbar conflicts
        plt.subplots_adjust(left=0.1, right=0.9, top=0.9, bottom=0.1, wspace=0.3, hspace=0.3)
        return fig
    
    @staticmethod
    def plot_parameter_grid(explorer: ParameterExplorer, 
                          param1_name: str, param1_values: Union[np.ndarray, List[float]],
                          param2_name: str, param2_values: Union[np.ndarray, List[float]],
                          figsize: Tuple[int, int] = (12, 10),
                          cmap: str = 'viridis') -> Figure:
        """
        Create a grid of solutions for two parameters.
        
        Parameters:
        -----------
        explorer : ParameterExplorer
            Configured parameter explorer
        param1_name : str
            First parameter name (x-axis)
        param1_values : array-like
            First parameter values
        param2_name : str
            Second parameter name (y-axis)
        param2_values : array-like
            Second parameter values
        figsize : tuple
            Figure size
        cmap : str
            Colormap name
        """
        if explorer.initial_conditions is None:
            raise ValueError("Initial conditions not set in explorer.")
        
        # Convert to numpy arrays
        param1_arr = np.array(param1_values)
        param2_arr = np.array(param2_values)
        
        n1, n2 = len(param1_arr), len(param2_arr)
        fig, axes = plt.subplots(n2, n1, figsize=figsize)
        
        # Handle different grid configurations
        if n1 == 1 and n2 == 1:
            axes_grid = [[axes]]
        elif n1 == 1:
            axes_grid = [[ax] for ax in axes]
        elif n2 == 1:
            axes_grid = [list(axes)]
        else:
            axes_grid = axes
        
        solutions = []
        
        print(f"Creating {n1}×{n2} parameter grid...")
        
        for i, val1 in enumerate(param1_arr):
            for j, val2 in enumerate(param2_arr):
                print(f"  Computing ({i+1},{j+1}): {param1_name}={val1:.3f}, {param2_name}={val2:.3f}")
                
                # Create parameter config
                params = explorer.default_params.copy()
                params[param1_name] = val1
                params[param2_name] = val2
                
                # Separate solver parameters from solve parameters
                solver_params = {k: v for k, v in params.items() if k in ['alpha', 'c', 'dt', 'dx', 'dy']}
                steps = params.get('steps', 100)
                
                # Solve
                solver = PDESolver(explorer.equation, grid_shape=explorer.grid_shape, 
                                 boundary=explorer.boundary)
                solver.set_parameters(**solver_params)
                solver.set_initial_conditions(explorer.initial_conditions, explorer.initial_velocity)
                
                try:
                    solution = solver.solve(steps=steps)
                    solutions.append(solution)
                except Exception as e:
                    print(f"    Warning: Failed: {e}")
                    solution = np.zeros(explorer.grid_shape)
                    solutions.append(solution)
        
        # Find common color scale
        vmin = min(np.min(sol) for sol in solutions)
        vmax = max(np.max(sol) for sol in solutions)
        
        # Plot grid
        im = None
        for i, val1 in enumerate(param1_arr):
            for j, val2 in enumerate(param2_arr):
                solution = solutions[i * n2 + j]
                
                im = axes_grid[n2-1-j][i].imshow(solution, cmap=cmap, origin='lower',
                                               vmin=vmin, vmax=vmax)
                
                # Labels
                if j == 0:  # Bottom row
                    axes_grid[n2-1-j][i].set_xlabel(f'{param1_name}={val1:.3f}')
                if i == 0:  # Left column
                    axes_grid[n2-1-j][i].set_ylabel(f'{param2_name}={val2:.3f}')
                
                axes_grid[n2-1-j][i].set_xticks([])
                axes_grid[n2-1-j][i].set_yticks([])
        
        # Add colorbar
        if im is not None:
            # Flatten the 2D axes grid for colorbar
            axes_flat: List[Axes] = []
            if n1 == 1 and n2 == 1:
                # Single subplot case
                axes_flat = [axes_grid[0][0]]
            elif n1 == 1:
                # Single column case
                axes_flat = [axes_grid[i][0] for i in range(n2)]
            elif n2 == 1:
                # Single row case
                axes_flat = axes_grid[0]
            else:
                # Full grid case
                axes_flat = [axes_grid[i][j] for i in range(n2) for j in range(n1)]
            
            plt.colorbar(im, ax=axes_flat, orientation='vertical', fraction=0.046, pad=0.04)
        
        plt.suptitle(f'Parameter Grid: {param1_name} vs {param2_name}', fontsize=16)
        
        # Use subplots_adjust instead of tight_layout to avoid colorbar conflicts
        plt.subplots_adjust(left=0.1, right=0.85, top=0.9, bottom=0.1, wspace=0.3, hspace=0.3)
        
        print("✅ Parameter grid completed")
        return fig
    
    @staticmethod
    def plot_sensitivity_analysis(sensitivity_result: Dict[str, Any], 
                                figsize: Tuple[int, int] = (12, 6)) -> Figure:
        """
        Plot sensitivity analysis results.
        
        Parameters:
        -----------
        sensitivity_result : dict
            Results from sensitivity analysis
        figsize : tuple
            Figure size
        """
        sweep_result = sensitivity_result['sweep_result']
        sensitivity_metrics = sensitivity_result['sensitivity_metrics']
        
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=figsize)
        
        # Plot metric evolution
        param_values = sweep_result.parameter_values
        for metric_name, metric_values in sweep_result.metrics.items():
            ax1.plot(param_values, metric_values, 'o-', label=metric_name, linewidth=2)
        
        ax1.set_xlabel(sensitivity_result['parameter_name'])
        ax1.set_ylabel('Metric Value')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        ax1.set_title('Parameter Sensitivity')
        
        # Plot sensitivity coefficients
        metrics = list(sensitivity_metrics.keys())
        sensitivities = list(sensitivity_metrics.values())
        
        bars = ax2.bar(metrics, sensitivities, color='skyblue', alpha=0.7)
        ax2.set_ylabel('Relative Sensitivity')
        ax2.set_title('Sensitivity Coefficients')
        ax2.tick_params(axis='x', rotation=45)
        
        # Add value labels on bars
        for bar, sens in zip(bars, sensitivities):
            height = bar.get_height()
            ax2.text(bar.get_x() + bar.get_width()/2., height,
                    f'{sens:.3f}', ha='center', va='bottom')
        
        plt.tight_layout()
        return fig