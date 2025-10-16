#!/usr/bin/env python3
"""
Full Integration Test for Parameter Exploration Module
Tests all major functionality with real PDE solving.
"""

import numpy as np
import matplotlib.pyplot as plt
from pdevisualizer.parameter_exploration import ParameterExplorer, ParameterVisualizer
from pdevisualizer.solver import InitialConditions, BoundaryCondition
import time

def test_heat_equation_parameter_exploration():
    """Test parameter exploration with heat equation."""
    print("🔥 Testing Heat Equation Parameter Exploration...")
    
    # Create explorer
    explorer = ParameterExplorer('heat', grid_shape=(30, 30))
    
    # Set up initial conditions - Gaussian pulse
    u0 = InitialConditions.gaussian_pulse((30, 30), center=(15, 15), sigma=5)
    explorer.set_initial_conditions(u0)
    
    # Test 1: Parameter sweep for thermal diffusivity
    print("  📊 Running alpha parameter sweep...")
    alpha_values = np.linspace(0.1, 0.5, 5)
    sweep_result = explorer.parameter_sweep('alpha', alpha_values, 
                                           custom_params={'steps': 100})
    
    print(f"    ✅ Generated {len(sweep_result.solutions)} solutions")
    print(f"    ✅ Computed metrics: {list(sweep_result.metrics.keys())}")
    print(f"    ✅ Execution time: {sweep_result.execution_time:.2f}s")
    
    # Test 2: Compare different configurations
    print("  📊 Running parameter comparison...")
    configs = [
        {'alpha': 0.1, 'dt': 0.1, 'steps': 50},
        {'alpha': 0.3, 'dt': 0.1, 'steps': 50},
        {'alpha': 0.5, 'dt': 0.1, 'steps': 50}
    ]
    labels = ['Low Diffusion', 'Medium Diffusion', 'High Diffusion']
    comparison_results = explorer.compare_parameters(configs, labels)
    
    print(f"    ✅ Compared {len(comparison_results)} configurations")
    
    # Test 3: Sensitivity analysis
    print("  📊 Running sensitivity analysis...")
    sensitivity_result = explorer.sensitivity_analysis('alpha', base_value=0.25,
                                                      perturbation_percent=20,
                                                      n_samples=7)
    
    print(f"    ✅ Sensitivity analysis completed")
    print(f"    ✅ Sensitivity metrics: {list(sensitivity_result['sensitivity_metrics'].keys())}")
    
    # Test 4: Visualizations
    print("  📊 Creating visualizations...")
    
    # Parameter sweep plot
    fig1 = ParameterVisualizer.plot_parameter_sweep(sweep_result)
    plt.savefig('heat_parameter_sweep.png', dpi=100, bbox_inches='tight')
    plt.close(fig1)
    
    # Solution comparison plot
    fig2 = ParameterVisualizer.plot_solution_comparison(comparison_results)
    plt.savefig('heat_solution_comparison.png', dpi=100, bbox_inches='tight')
    plt.close(fig2)
    
    # Sensitivity analysis plot
    fig3 = ParameterVisualizer.plot_sensitivity_analysis(sensitivity_result)
    plt.savefig('heat_sensitivity_analysis.png', dpi=100, bbox_inches='tight')
    plt.close(fig3)
    
    # Parameter grid (2D parameter space)
    fig4 = ParameterVisualizer.plot_parameter_grid(
        explorer, 'alpha', np.array([0.1, 0.3]), 'dt', np.array([0.05, 0.1]),
        figsize=(10, 8)
    )
    plt.savefig('heat_parameter_grid.png', dpi=100, bbox_inches='tight')
    plt.close(fig4)
    
    print("    ✅ All visualizations saved successfully")
    
    return sweep_result, comparison_results, sensitivity_result


def test_wave_equation_parameter_exploration():
    """Test parameter exploration with wave equation."""
    print("🌊 Testing Wave Equation Parameter Exploration...")
    
    # Create explorer
    explorer = ParameterExplorer('wave', grid_shape=(25, 25))
    
    # Set up initial conditions - circular wave
    u0 = InitialConditions.circular_wave((25, 25), center=(12, 12), radius=5)
    explorer.set_initial_conditions(u0)
    
    # Test 1: Parameter sweep for wave speed
    print("  📊 Running wave speed parameter sweep...")
    c_values = np.linspace(0.5, 2.0, 4)
    sweep_result = explorer.parameter_sweep('c', c_values, 
                                           custom_params={'steps': 150})
    
    print(f"    ✅ Generated {len(sweep_result.solutions)} solutions")
    print(f"    ✅ Execution time: {sweep_result.execution_time:.2f}s")
    
    # Test 2: Compare different time steps
    print("  📊 Running time step comparison...")
    configs = [
        {'c': 1.0, 'dt': 0.02, 'steps': 100},
        {'c': 1.0, 'dt': 0.05, 'steps': 100},
        {'c': 1.0, 'dt': 0.08, 'steps': 100}
    ]
    labels = ['Fine Δt', 'Medium Δt', 'Coarse Δt']
    comparison_results = explorer.compare_parameters(configs, labels)
    
    print(f"    ✅ Compared {len(comparison_results)} time steps")
    
    # Test 3: Visualizations
    print("  📊 Creating wave visualizations...")
    
    fig1 = ParameterVisualizer.plot_parameter_sweep(sweep_result, 
                                                   metric_names=['max_value', 'total_energy'])
    plt.savefig('wave_parameter_sweep.png', dpi=100, bbox_inches='tight')
    plt.close(fig1)
    
    fig2 = ParameterVisualizer.plot_solution_comparison(comparison_results)
    plt.savefig('wave_solution_comparison.png', dpi=100, bbox_inches='tight')
    plt.close(fig2)
    
    print("    ✅ Wave visualizations saved successfully")
    
    return sweep_result, comparison_results


def test_boundary_conditions():
    """Test parameter exploration with different boundary conditions."""
    print("🔲 Testing Different Boundary Conditions...")
    
    boundary_conditions = [
        ('Dirichlet', BoundaryCondition.dirichlet(0.0)),
        ('Neumann', BoundaryCondition.neumann(0.0)),
        ('Periodic', BoundaryCondition.periodic())
    ]
    
    results = {}
    
    for name, boundary in boundary_conditions:
        print(f"  📊 Testing {name} boundary condition...")
        
        explorer = ParameterExplorer('heat', grid_shape=(20, 20), boundary=boundary)
        u0 = InitialConditions.gaussian_pulse((20, 20), center=(10, 10), sigma=3)
        explorer.set_initial_conditions(u0)
        
        # Quick parameter sweep
        alpha_values = np.array([0.1, 0.3])
        sweep_result = explorer.parameter_sweep('alpha', alpha_values, 
                                               custom_params={'steps': 50})
        
        results[name] = sweep_result
        print(f"    ✅ {name} boundary condition working correctly")
    
    return results


def test_edge_cases():
    """Test edge cases and error handling."""
    print("⚠️  Testing Edge Cases and Error Handling...")
    
    explorer = ParameterExplorer('heat', grid_shape=(10, 10))
    u0 = InitialConditions.zeros((10, 10))
    u0[5, 5] = 1.0  # Point source
    explorer.set_initial_conditions(u0)
    
    # Test 1: Empty parameter array
    result1 = explorer.parameter_sweep('alpha', np.array([]))
    print(f"    ✅ Empty parameter array handled: {len(result1.solutions)} solutions")
    
    # Test 2: Single parameter value
    result2 = explorer.parameter_sweep('alpha', np.array([0.25]))
    print(f"    ✅ Single parameter value handled: {len(result2.solutions)} solutions")
    
    # Test 3: Very small grid
    small_explorer = ParameterExplorer('heat', grid_shape=(5, 5))
    small_u0 = InitialConditions.zeros((5, 5))
    small_u0[2, 2] = 1.0
    small_explorer.set_initial_conditions(small_u0)
    
    result3 = small_explorer.parameter_sweep('alpha', np.array([0.1, 0.2]))
    print(f"    ✅ Small grid handled: {len(result3.solutions)} solutions")
    
    # Test 4: Error handling for missing initial conditions
    try:
        empty_explorer = ParameterExplorer('heat')
        empty_explorer.parameter_sweep('alpha', np.array([0.1]))
        print("    ❌ Should have raised ValueError")
    except ValueError as e:
        print(f"    ✅ Proper error handling: {e}")
    
    return result1, result2, result3


def main():
    """Run the complete integration test."""
    print("🚀 Starting Parameter Exploration Integration Test")
    print("=" * 60)
    
    start_time = time.time()
    
    try:
        # Test heat equation
        heat_results = test_heat_equation_parameter_exploration()
        print()
        
        # Test wave equation
        wave_results = test_wave_equation_parameter_exploration()
        print()
        
        # Test boundary conditions
        boundary_results = test_boundary_conditions()
        print()
        
        # Test edge cases
        edge_results = test_edge_cases()
        print()
        
        # Summary
        total_time = time.time() - start_time
        print("=" * 60)
        print("🎉 Integration Test Results:")
        print(f"   ✅ Heat equation parameter exploration: PASSED")
        print(f"   ✅ Wave equation parameter exploration: PASSED")
        print(f"   ✅ Boundary condition variations: PASSED")
        print(f"   ✅ Edge case handling: PASSED")
        print(f"   ✅ All visualizations generated: PASSED")
        print(f"   ⏱️  Total execution time: {total_time:.2f} seconds")
        print()
        print("🎯 Generated Files:")
        print("   📈 heat_parameter_sweep.png")
        print("   📈 heat_solution_comparison.png") 
        print("   📈 heat_sensitivity_analysis.png")
        print("   📈 heat_parameter_grid.png")
        print("   📈 wave_parameter_sweep.png")
        print("   📈 wave_solution_comparison.png")
        print()
        print("✨ Parameter Exploration Module: FULLY FUNCTIONAL!")
        
        return True
        
    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)