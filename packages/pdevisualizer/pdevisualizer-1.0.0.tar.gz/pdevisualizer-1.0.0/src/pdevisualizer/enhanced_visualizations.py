"""
Enhanced visualization tools for PDEVisualizer.

This module provides advanced 2D visualization capabilities including contour plots,
multi-panel comparisons, parameter landscapes, and solution evolution plots that
build upon the existing matplotlib patterns in the codebase.
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
from matplotlib.figure import Figure
from matplotlib.axes import Axes
from typing import Dict, List, Tuple, Any, Optional, Union
import time

from .solver import PDESolver, BoundaryCondition, InitialConditions
from .parameter_exploration import ParameterSweepResult, ParameterExplorer


class EnhancedVisualizer:
    """
    Advanced 2D visualization tools for PDE solutions and parameter exploration.
    
    This class provides methods for creating enhanced 2D visualizations that
    build upon the existing matplotlib patterns in the codebase.
    """
    
    @staticmethod
    def plot_contours(solution: np.ndarray,
                     title: str = "PDE Solution",
                     figsize: Tuple[int, int] = (8, 6),
                     cmap: str = 'viridis',
                     levels: Optional[Union[int, List[float]]] = None,
                     fill_contours: bool = True) -> Figure:
        """
        Create contour plots of a PDE solution.
        
        Parameters:
        -----------
        solution : np.ndarray
            2D solution array
        title : str
            Plot title
        figsize : tuple
            Figure size
        cmap : str
            Colormap name
        levels : int or list, optional
            Number of contour levels or specific level values
        fill_contours : bool
            Whether to fill contours or just draw lines
        
        Returns:
        --------
        Figure
            Matplotlib figure object
        """
        fig, ax = plt.subplots(figsize=figsize)
        
        # Set default levels if not provided
        if levels is None:
            levels = 15
        
        # Create contour plot
        if fill_contours:
            cs = ax.contourf(solution, levels=levels, cmap=cmap, origin='lower')
            # Add contour lines on top
            ax.contour(solution, levels=levels, colors='black', alpha=0.3, linewidths=0.5, origin='lower')
        else:
            cs = ax.contour(solution, levels=levels, cmap=cmap, origin='lower')
        
        # Customize the plot
        ax.set_xlabel('x')
        ax.set_ylabel('y')
        ax.set_title(title, fontsize=14)
        ax.set_aspect('equal')
        
        # Add colorbar
        fig.colorbar(cs, ax=ax)
        
        return fig
    
    @staticmethod
    def plot_solution_evolution(solutions: List[np.ndarray],
                               time_points: List[float],
                               title: str = "Solution Evolution",
                               figsize: Tuple[int, int] = (15, 10),
                               cmap: str = 'viridis',
                               plot_type: str = 'heatmap') -> Figure:
        """
        Create a multi-panel plot showing solution evolution over time.
        
        Parameters:
        -----------
        solutions : list
            List of 2D solution arrays at different time points
        time_points : list
            List of time values corresponding to solutions
        title : str
            Overall plot title
        figsize : tuple
            Figure size
        cmap : str
            Colormap name
        plot_type : str
            Type of plot ('heatmap' or 'contour')
        
        Returns:
        --------
        Figure
            Matplotlib figure object
        """
        n_solutions = len(solutions)
        
        # Determine grid layout
        if n_solutions <= 3:
            rows, cols = 1, n_solutions
        elif n_solutions <= 6:
            rows, cols = 2, 3
        else:
            rows = int(np.ceil(np.sqrt(n_solutions)))
            cols = int(np.ceil(n_solutions / rows))
        
        # Find common color scale
        vmin = min(np.min(sol) for sol in solutions)
        vmax = max(np.max(sol) for sol in solutions)
        
        fig, axes = plt.subplots(rows, cols, figsize=figsize)
        
        # Handle different subplot configurations
        if n_solutions == 1:
            axes = [axes]
        elif rows == 1:
            axes = [axes] if cols == 1 else axes
        else:
            axes = axes.flatten()
        
        cs = None  # Initialize cs variable
        for i, (solution, t) in enumerate(zip(solutions, time_points)):
            ax = axes[i]
            
            if plot_type == 'contour':
                cs = ax.contourf(solution, levels=15, cmap=cmap, vmin=vmin, vmax=vmax, origin='lower')
                ax.contour(solution, levels=15, colors='black', alpha=0.3, linewidths=0.5, origin='lower')
            else:  # heatmap
                cs = ax.imshow(solution, cmap=cmap, origin='lower', vmin=vmin, vmax=vmax)
            
            ax.set_title(f't = {t:.2f}', fontsize=12)
            ax.set_xlabel('x')
            ax.set_ylabel('y')
        
        # Remove empty subplots
        for i in range(n_solutions, len(axes)):
            axes[i].remove()
        
        plt.suptitle(title, fontsize=16)
        
        # Add colorbar - ensure cs is defined
        if n_solutions > 0 and cs is not None:
            fig.colorbar(cs, ax=axes[:n_solutions], orientation='vertical', fraction=0.046, pad=0.04)
        
        plt.subplots_adjust(left=0.1, right=0.9, top=0.9, bottom=0.1, wspace=0.3, hspace=0.4)
        
        return fig
    
    @staticmethod
    def plot_parameter_landscape(explorer: ParameterExplorer,
                                param1_name: str, param1_range: Tuple[float, float],
                                param2_name: str, param2_range: Tuple[float, float],
                                metric: str = 'max_value',
                                resolution: int = 20,
                                figsize: Tuple[int, int] = (12, 9)) -> Figure:
        """
        Create a parameter landscape visualization showing how a metric varies
        across a 2D parameter space.
        
        Parameters:
        -----------
        explorer : ParameterExplorer
            Configured parameter explorer
        param1_name : str
            First parameter name (x-axis)
        param1_range : tuple
            (min, max) for first parameter
        param2_name : str
            Second parameter name (y-axis)
        param2_range : tuple
            (min, max) for second parameter
        metric : str
            Metric to visualize ('max_value', 'total_energy', etc.)
        resolution : int
            Number of points along each parameter axis
        figsize : tuple
            Figure size
        
        Returns:
        --------
        Figure
            Matplotlib figure object
        """
        if explorer.initial_conditions is None:
            raise ValueError("Initial conditions not set in explorer.")
        
        # Create parameter grids
        param1_values = np.linspace(param1_range[0], param1_range[1], resolution)
        param2_values = np.linspace(param2_range[0], param2_range[1], resolution)
        
        # Initialize result array
        metric_values = np.zeros((resolution, resolution))
        
        print(f"Computing {resolution}×{resolution} parameter landscape...")
        
        # Compute metric for each parameter combination
        for i, val1 in enumerate(param1_values):
            for j, val2 in enumerate(param2_values):
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
                    
                    # Compute metric
                    if metric == 'max_value':
                        metric_values[j, i] = np.max(solution)
                    elif metric == 'min_value':
                        metric_values[j, i] = np.min(solution)
                    elif metric == 'total_energy':
                        metric_values[j, i] = np.sum(solution**2)
                    elif metric == 'center_value':
                        center_i, center_j = explorer.grid_shape[0]//2, explorer.grid_shape[1]//2
                        metric_values[j, i] = solution[center_i, center_j]
                    else:
                        metric_values[j, i] = np.mean(solution)
                        
                except Exception as e:
                    print(f"    Warning: Failed: {e}")
                    metric_values[j, i] = np.nan
        
        # Create visualization
        fig = plt.figure(figsize=figsize)
        gs = GridSpec(2, 2, figure=fig, height_ratios=[3, 1], width_ratios=[3, 1])
        
        # Main contour plot
        ax_main = fig.add_subplot(gs[0, 0])
        P1, P2 = np.meshgrid(param1_values, param2_values)
        
        # Create filled contours
        cs = ax_main.contourf(P1, P2, metric_values, levels=20, cmap='viridis', origin='lower')
        ax_main.contour(P1, P2, metric_values, levels=20, colors='black', alpha=0.3, linewidths=0.5, origin='lower')
        
        ax_main.set_xlabel(param1_name)
        ax_main.set_ylabel(param2_name)
        ax_main.set_title(f'{metric.replace("_", " ").title()} Landscape')
        
        # Add colorbar
        cbar = plt.colorbar(cs, ax=ax_main)
        cbar.set_label(metric.replace("_", " ").title())
        
        # Parameter 1 marginal plot (right)
        ax_right = fig.add_subplot(gs[0, 1])
        param1_marginal = np.nanmean(metric_values, axis=0)
        ax_right.plot(param1_marginal, param1_values, 'b-', linewidth=2)
        ax_right.set_ylabel(param1_name)
        ax_right.set_title('Marginal')
        ax_right.grid(True, alpha=0.3)
        
        # Parameter 2 marginal plot (bottom)
        ax_bottom = fig.add_subplot(gs[1, 0])
        param2_marginal = np.nanmean(metric_values, axis=1)
        ax_bottom.plot(param2_values, param2_marginal, 'r-', linewidth=2)
        ax_bottom.set_xlabel(param2_name)
        ax_bottom.set_ylabel('Mean ' + metric.replace("_", " ").title())
        ax_bottom.grid(True, alpha=0.3)
        
        # Empty subplot (bottom-right)
        ax_empty = fig.add_subplot(gs[1, 1])
        ax_empty.axis('off')
        
        plt.suptitle(f'Parameter Landscape: {param1_name} vs {param2_name}', fontsize=16)
        plt.tight_layout()
        
        print("✅ Parameter landscape completed")
        return fig
    
    @staticmethod
    def plot_solution_comparison_enhanced(solutions: Dict[str, np.ndarray],
                                        figsize: Tuple[int, int] = (15, 10),
                                        cmap: str = 'viridis',
                                        plot_types: List[str] = ['heatmap', 'contour']) -> Figure:
        """
        Create an enhanced multi-panel comparison of solutions with different visualization types.
        
        Parameters:
        -----------
        solutions : dict
            Dictionary mapping labels to solution arrays
        figsize : tuple
            Figure size
        cmap : str
            Colormap name
        plot_types : list
            List of plot types to include ('heatmap', 'contour')
        
        Returns:
        --------
        Figure
            Matplotlib figure object
        """
        n_solutions = len(solutions)
        n_types = len(plot_types)
        
        if n_solutions == 0:
            raise ValueError("No solutions provided for comparison")
        
        # Create figure with subplots
        fig, axes = plt.subplots(n_types, n_solutions, figsize=figsize)
        
        # Handle different subplot configurations
        if n_types == 1 and n_solutions == 1:
            axes = [[axes]]
        elif n_types == 1:
            axes = [axes]
        elif n_solutions == 1:
            axes = [[ax] for ax in axes]
        
        # Find common color scale
        vmin = min(np.min(sol) for sol in solutions.values())
        vmax = max(np.max(sol) for sol in solutions.values())
        
        solution_items = list(solutions.items())
        
        cs = None  # Initialize cs variable
        for type_idx, plot_type in enumerate(plot_types):
            for sol_idx, (label, solution) in enumerate(solution_items):
                ax = axes[type_idx][sol_idx]
                
                if plot_type == 'contour':
                    cs = ax.contourf(solution, levels=15, cmap=cmap, vmin=vmin, vmax=vmax, origin='lower')
                    ax.contour(solution, levels=15, colors='black', alpha=0.3, linewidths=0.5, origin='lower')
                else:  # heatmap
                    cs = ax.imshow(solution, cmap=cmap, origin='lower', vmin=vmin, vmax=vmax)
                
                ax.set_xlabel('x')
                ax.set_ylabel('y')
                
                # Add title
                if type_idx == 0:
                    ax.set_title(label, fontsize=12)
                
                # Add plot type label on the left
                if sol_idx == 0:
                    ax.text(-0.1, 0.5, plot_type.upper(), transform=ax.transAxes, 
                           rotation=90, ha='center', va='center', fontsize=12, fontweight='bold')
        
        # Add colorbar - ensure cs is defined and axes are properly typed
        if n_solutions > 0 and cs is not None:
            # Create a flat list of axes for colorbar
            axes_list = []
            for type_idx in range(n_types):
                for sol_idx in range(n_solutions):
                    axes_list.append(axes[type_idx][sol_idx])
            
            fig.colorbar(cs, ax=axes_list, orientation='vertical', fraction=0.046, pad=0.04)
        
        plt.suptitle('Enhanced Solution Comparison', fontsize=16)
        plt.subplots_adjust(left=0.1, right=0.9, top=0.9, bottom=0.1, wspace=0.3, hspace=0.4)
        
        return fig
    
    @staticmethod
    def plot_parameter_sweep_enhanced(sweep_result: ParameterSweepResult,
                                     figsize: Tuple[int, int] = (15, 10),
                                     include_heatmaps: bool = True,
                                     include_contours: bool = True) -> Figure:
        """
        Create an enhanced parameter sweep visualization with multiple plot types.
        
        Parameters:
        -----------
        sweep_result : ParameterSweepResult
            Results from parameter sweep
        figsize : tuple
            Figure size
        include_heatmaps : bool
            Whether to include heatmap plots
        include_contours : bool
            Whether to include contour plots
        
        Returns:
        --------
        Figure
            Matplotlib figure object
        """
        n_solutions = len(sweep_result.solutions)
        
        # Determine layout
        if include_heatmaps and include_contours:
            rows = 3  # Metrics, heatmaps, contours
        elif include_heatmaps or include_contours:
            rows = 2  # Metrics + one visualization type
        else:
            rows = 1  # Just metrics
        
        fig = plt.figure(figsize=figsize)
        gs = GridSpec(rows, max(4, n_solutions), figure=fig)
        
        # Top row: Metrics
        ax_metrics = fig.add_subplot(gs[0, :])
        param_values = sweep_result.parameter_values
        
        colors = ['blue', 'red', 'green', 'orange']
        for i, (metric_name, metric_values) in enumerate(sweep_result.metrics.items()):
            color = colors[i % len(colors)]
            ax_metrics.plot(param_values, metric_values, 'o-', 
                          label=metric_name.replace('_', ' ').title(), 
                          color=color, linewidth=2, markersize=6)
        
        ax_metrics.set_xlabel(sweep_result.parameter_name)
        ax_metrics.set_ylabel('Metric Value')
        ax_metrics.legend()
        ax_metrics.grid(True, alpha=0.3)
        ax_metrics.set_title('Parameter Sweep Metrics')
        
        # Find common color scale for solutions
        vmin = min(np.min(sol) for sol in sweep_result.solutions)
        vmax = max(np.max(sol) for sol in sweep_result.solutions)
        
        current_row = 1
        
        # Heatmap plots
        if include_heatmaps and current_row < rows:
            for i, (solution, param_val) in enumerate(zip(sweep_result.solutions, param_values)):
                ax = fig.add_subplot(gs[current_row, i])
                
                cs = ax.imshow(solution, cmap='viridis', vmin=vmin, vmax=vmax, origin='lower')
                ax.set_title(f'{sweep_result.parameter_name}={param_val:.3f}')
                ax.set_xlabel('x')
                ax.set_ylabel('y')
            
            current_row += 1
        
        # Contour plots
        if include_contours and current_row < rows:
            for i, (solution, param_val) in enumerate(zip(sweep_result.solutions, param_values)):
                ax = fig.add_subplot(gs[current_row, i])
                
                cs = ax.contourf(solution, levels=15, cmap='viridis', vmin=vmin, vmax=vmax, origin='lower')
                ax.contour(solution, levels=15, colors='black', alpha=0.3, linewidths=0.5, origin='lower')
                ax.set_title(f'{sweep_result.parameter_name}={param_val:.3f}')
                ax.set_xlabel('x')
                ax.set_ylabel('y')
        
        plt.suptitle(f'Enhanced Parameter Sweep: {sweep_result.parameter_name}', fontsize=16)
        plt.subplots_adjust(left=0.1, right=0.9, top=0.9, bottom=0.1, wspace=0.3, hspace=0.4)
        
        return fig
    
    @staticmethod
    def plot_wave_comparison(solutions: Dict[str, np.ndarray],
                           figsize: Tuple[int, int] = (15, 5),
                           symmetric_colormap: bool = True) -> Figure:
        """
        Create a comparison plot specifically optimized for wave solutions.
        
        Parameters:
        -----------
        solutions : dict
            Dictionary mapping labels to solution arrays
        figsize : tuple
            Figure size
        symmetric_colormap : bool
            Whether to use symmetric colormap (good for waves)
        
        Returns:
        --------
        Figure
            Matplotlib figure object
        """
        n_solutions = len(solutions)
        fig, axes = plt.subplots(1, n_solutions, figsize=figsize)
        
        if n_solutions == 1:
            axes = [axes]
        
        # Find common color scale (symmetric for waves)
        if symmetric_colormap:
            all_abs_values = []
            for solution in solutions.values():
                all_abs_values.append(np.abs(np.min(solution)))
                all_abs_values.append(np.abs(np.max(solution)))
            vmax = max(all_abs_values)
            vmin = -vmax
            cmap = 'RdBu_r'
        else:
            vmin = min(np.min(solution) for solution in solutions.values())
            vmax = max(np.max(solution) for solution in solutions.values())
            cmap = 'viridis'
        
        im = None  # Initialize im variable
        for i, (label, solution) in enumerate(solutions.items()):
            im = axes[i].imshow(solution, cmap=cmap, origin='lower', 
                              vmin=vmin, vmax=vmax)
            axes[i].set_title(label)
            axes[i].set_xlabel('x')
            if i == 0:
                axes[i].set_ylabel('y')
        
        # Add colorbar - ensure im is defined
        if im is not None:
            fig.colorbar(im, ax=axes, orientation='vertical', fraction=0.046, pad=0.04)
        
        plt.subplots_adjust(left=0.1, right=0.9, top=0.9, bottom=0.1, wspace=0.3, hspace=0.3)
        return fig
    
    @staticmethod
    def plot_heat_comparison(solutions: Dict[str, np.ndarray],
                           figsize: Tuple[int, int] = (15, 5)) -> Figure:
        """
        Create a comparison plot specifically optimized for heat solutions.
        
        Parameters:
        -----------
        solutions : dict
            Dictionary mapping labels to solution arrays
        figsize : tuple
            Figure size
        
        Returns:
        --------
        Figure
            Matplotlib figure object
        """
        n_solutions = len(solutions)
        fig, axes = plt.subplots(1, n_solutions, figsize=figsize)
        
        if n_solutions == 1:
            axes = [axes]
        
        # Find common color scale
        vmin = min(np.min(solution) for solution in solutions.values())
        vmax = max(np.max(solution) for solution in solutions.values())
        
        im = None  # Initialize im variable
        for i, (label, solution) in enumerate(solutions.items()):
            im = axes[i].imshow(solution, cmap='hot', origin='lower', 
                              vmin=vmin, vmax=vmax)
            axes[i].set_title(label)
            axes[i].set_xlabel('x')
            if i == 0:
                axes[i].set_ylabel('y')
        
        # Add colorbar - ensure im is defined
        if im is not None:
            fig.colorbar(im, ax=axes, orientation='vertical', fraction=0.046, pad=0.04)
        
        plt.subplots_adjust(left=0.1, right=0.9, top=0.9, bottom=0.1, wspace=0.3, hspace=0.3)
        return fig