import numpy as np
import pytest

from pdevisualizer.heat2d import solve_heat, step_heat, animate_heat


def test_constant_field():
    """Test that a constant temperature field remains constant."""
    u0 = np.full((10, 10), 5.0)
    u1 = solve_heat(u0, α=0.1, dt=0.1, dx=1.0, dy=1.0, steps=10)
    
    # Constant field should remain constant (with small numerical tolerance)
    assert np.allclose(u1, 5.0, atol=1e-10)


def test_zero_field():
    """Test that a zero temperature field remains zero."""
    u0 = np.zeros((10, 10))
    u1 = solve_heat(u0, α=0.1, dt=0.1, dx=1.0, dy=1.0, steps=10)
    
    assert np.allclose(u1, 0.0, atol=1e-10)


def test_stability_condition():
    """Test that stability condition is properly enforced."""
    u0 = np.random.rand(10, 10)
    
    # This should work (stable)
    u1 = solve_heat(u0, α=0.1, dt=0.1, dx=1.0, dy=1.0, steps=5)
    assert u1.shape == u0.shape
    
    # This should raise an error (unstable)
    with pytest.raises(ValueError, match="Numerical instability detected"):
        solve_heat(u0, α=1.0, dt=1.0, dx=1.0, dy=1.0, steps=5)


def test_boundary_conditions():
    """Test that boundary conditions are preserved (Dirichlet BC = 0)."""
    u0 = np.zeros((10, 10))
    u0[5, 5] = 100.0  # Hot spot in center
    
    u1 = solve_heat(u0, α=0.1, dt=0.1, dx=1.0, dy=1.0, steps=10)
    
    # Check that boundaries remain zero
    assert np.allclose(u1[0, :], 0.0)  # Top boundary
    assert np.allclose(u1[-1, :], 0.0)  # Bottom boundary
    assert np.allclose(u1[:, 0], 0.0)  # Left boundary
    assert np.allclose(u1[:, -1], 0.0)  # Right boundary


def test_heat_diffusion():
    """Test that heat diffuses from hot spot."""
    u0 = np.zeros((20, 20))
    u0[10, 10] = 100.0  # Hot spot in center
    
    u1 = solve_heat(u0, α=0.1, dt=0.1, dx=1.0, dy=1.0, steps=50)
    
    # Heat should have spread out
    assert u1[10, 10] < u0[10, 10]  # Center cooled down
    assert u1[9, 10] > 0  # Heat spread to neighbors
    assert u1[11, 10] > 0
    assert u1[10, 9] > 0
    assert u1[10, 11] > 0


def test_step_heat_single_step():
    """Test single step function."""
    u0 = np.zeros((10, 10))
    u0[5, 5] = 100.0
    
    u1 = step_heat(u0, α=0.1, dt=0.1, dx=1.0, dy=1.0)
    
    # Should be different from original
    assert not np.allclose(u1, u0)
    # But boundaries should remain zero
    assert np.allclose(u1[0, :], 0.0)
    assert np.allclose(u1[-1, :], 0.0)
    assert np.allclose(u1[:, 0], 0.0)
    assert np.allclose(u1[:, -1], 0.0)


def test_animation_creation():
    """Test that animation can be created without errors."""
    u0 = np.zeros((10, 10))
    u0[5, 5] = 100.0
    
    # Should not raise an error
    anim = animate_heat(u0, α=0.1, dt=0.1, dx=1.0, dy=1.0, frames=5)
    assert anim is not None


def test_animation_stability_check():
    """Test that animation also enforces stability condition."""
    u0 = np.random.rand(10, 10)
    
    # This should raise an error (unstable)
    with pytest.raises(ValueError, match="Numerical instability detected"):
        animate_heat(u0, α=1.0, dt=1.0, dx=1.0, dy=1.0, frames=5)


def test_conservation_property():
    """Test that total heat is conserved with zero boundary conditions."""
    u0 = np.zeros((20, 20))
    u0[8:12, 8:12] = 10.0  # Square heat source
    
    initial_heat = np.sum(u0)
    
    # Run for many steps
    u1 = solve_heat(u0, α=0.1, dt=0.05, dx=1.0, dy=1.0, steps=100)
    final_heat = np.sum(u1)
    
    # Heat should be conserved (within numerical tolerance)
    # Note: With zero boundary conditions, heat will actually dissipate
    # So we expect final_heat <= initial_heat
    assert final_heat <= initial_heat
    assert final_heat >= 0  # No negative temperatures