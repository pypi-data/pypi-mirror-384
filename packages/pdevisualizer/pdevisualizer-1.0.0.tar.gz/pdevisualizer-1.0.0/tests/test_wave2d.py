import numpy as np
import pytest
from pdevisualizer.wave2d import (
    solve_wave, step_wave, step_wave_first, animate_wave,
    create_gaussian_pulse, create_circular_wave
)


def test_zero_initial_conditions():
    """Test that zero initial conditions remain zero."""
    u0 = np.zeros((10, 10))
    v0 = np.zeros((10, 10))
    
    u_final = solve_wave(u0, v0, c=1.0, dt=0.1, dx=1.0, dy=1.0, steps=10)
    
    assert np.allclose(u_final, 0.0, atol=1e-10)


def test_cfl_stability_condition():
    """Test that CFL condition is properly enforced."""
    u0 = np.random.rand(10, 10)
    
    # This should work (stable)
    u1 = solve_wave(u0, c=0.5, dt=0.1, dx=1.0, dy=1.0, steps=5)
    assert u1.shape == u0.shape
    
    # This should raise an error (unstable)
    with pytest.raises(ValueError, match="CFL condition violated"):
        solve_wave(u0, c=2.0, dt=1.0, dx=1.0, dy=1.0, steps=5)


def test_boundary_conditions():
    """Test that boundary conditions are preserved (fixed at zero)."""
    u0 = np.zeros((10, 10))
    u0[5, 5] = 1.0  # Pulse in center
    
    u1 = solve_wave(u0, c=0.5, dt=0.1, dx=1.0, dy=1.0, steps=10)
    
    # Check that boundaries remain zero
    assert np.allclose(u1[0, :], 0.0)   # Left boundary
    assert np.allclose(u1[-1, :], 0.0)  # Right boundary
    assert np.allclose(u1[:, 0], 0.0)   # Bottom boundary
    assert np.allclose(u1[:, -1], 0.0)  # Top boundary


def test_wave_propagation():
    """Test that waves propagate outward from initial disturbance."""
    u0 = np.zeros((20, 20))
    u0[10, 10] = 1.0  # Central pulse
    
    u1 = solve_wave(u0, c=1.0, dt=0.05, dx=1.0, dy=1.0, steps=20)
    
    # Wave should have spread out from center
    assert np.abs(u1[10, 10]) < 1.0  # Center amplitude changed
    
    # Check that energy has spread to nearby points
    # (This tests basic wave propagation behavior)
    center_region = u1[8:13, 8:13]
    assert np.any(np.abs(center_region) > 1e-6)


def test_wave_symmetry():
    """Test that waves propagate symmetrically from central source."""
    u0 = np.zeros((21, 21))  # Odd size for perfect center
    u0[10, 10] = 1.0  # Central pulse
    
    u1 = solve_wave(u0, c=1.0, dt=0.05, dx=1.0, dy=1.0, steps=10)
    
    # Check approximate symmetry (within numerical tolerance)
    center = 10
    for offset in [1, 2, 3]:
        # Compare opposite sides
        assert np.abs(u1[center+offset, center] - u1[center-offset, center]) < 0.1
        assert np.abs(u1[center, center+offset] - u1[center, center-offset]) < 0.1


def test_step_wave_first():
    """Test the first time step function."""
    u0 = np.zeros((10, 10))
    u0[5, 5] = 1.0
    v0 = np.zeros((10, 10))
    
    u1 = step_wave_first(u0, v0, c=1.0, dt=0.1, dx=1.0, dy=1.0)
    
    # Should be different from original
    assert not np.allclose(u1, u0)
    # But boundaries should remain zero
    assert np.allclose(u1[0, :], 0.0)
    assert np.allclose(u1[-1, :], 0.0)
    assert np.allclose(u1[:, 0], 0.0)
    assert np.allclose(u1[:, -1], 0.0)


def test_step_wave_regular():
    """Test the regular time step function."""
    u0 = np.zeros((10, 10))
    u0[5, 5] = 1.0
    u_prev = np.zeros((10, 10))
    
    u_next = step_wave(u0, u_prev, c=1.0, dt=0.1, dx=1.0, dy=1.0)
    
    # Should be different from current state
    assert not np.allclose(u_next, u0)
    # Boundaries should be zero
    assert np.allclose(u_next[0, :], 0.0)
    assert np.allclose(u_next[-1, :], 0.0)
    assert np.allclose(u_next[:, 0], 0.0)
    assert np.allclose(u_next[:, -1], 0.0)


def test_energy_conservation():
    """Test approximate energy conservation in wave equation."""
    u0 = create_gaussian_pulse(20, center=(10, 10), sigma=3, amplitude=1.0)
    v0 = np.zeros_like(u0)
    
    # Calculate initial energy (kinetic + potential)
    initial_energy = np.sum(u0**2)  # Simplified energy measure
    
    # Run for several steps
    u_final = solve_wave(u0, v0, c=1.0, dt=0.05, dx=1.0, dy=1.0, steps=50)
    
    # With zero boundary conditions, energy will decrease
    # But it should decrease smoothly, not blow up
    final_energy = np.sum(u_final**2)
    
    # Energy should not increase (no amplification)
    assert final_energy <= initial_energy * 1.1  # Small tolerance for numerical errors
    
    # Energy should not go negative or become infinite
    assert final_energy >= 0
    assert np.isfinite(final_energy)


def test_gaussian_pulse_creation():
    """Test the Gaussian pulse creation function."""
    pulse = create_gaussian_pulse(20, center=(10, 10), sigma=2, amplitude=1.0)
    
    # Check shape
    assert pulse.shape == (20, 20)
    
    # Check maximum is at center
    assert np.argmax(pulse) == np.ravel_multi_index((10, 10), pulse.shape)
    
    # Check amplitude
    assert np.abs(pulse[10, 10] - 1.0) < 1e-10
    
    # Check it's approximately Gaussian (decreases away from center)
    assert pulse[10, 10] > pulse[8, 10]  # Center > offset
    assert pulse[10, 10] > pulse[10, 8]


def test_circular_wave_creation():
    """Test the circular wave creation function."""
    wave = create_circular_wave(20, center=(10, 10), radius=5, amplitude=1.0)
    
    # Check shape
    assert wave.shape == (20, 20)
    
    # Check it's not zero everywhere
    assert np.max(wave) > 0.1
    
    # Check it's approximately circular (values at same radius similar)
    center_x, center_y = 10, 10
    r = 5
    # Points at approximately same distance from center
    val1 = wave[center_x + r, center_y]
    val2 = wave[center_x, center_y + r]
    val3 = wave[center_x - r, center_y]
    val4 = wave[center_x, center_y - r]
    
    # They should be similar (within tolerance)
    values = [val1, val2, val3, val4]
    mean_val = np.mean(values)
    assert all(abs(v - mean_val) < 0.5 for v in values)


def test_animation_creation():
    """Test that animation can be created without errors."""
    u0 = create_gaussian_pulse(10, center=(5, 5), sigma=2, amplitude=1.0)
    
    # Should not raise an error
    anim = animate_wave(u0, c=1.0, dt=0.05, dx=1.0, dy=1.0, frames=5)
    assert anim is not None


def test_animation_cfl_check():
    """Test that animation also enforces CFL condition."""
    u0 = np.random.rand(10, 10)
    
    # This should raise an error (unstable)
    with pytest.raises(ValueError, match="CFL condition violated"):
        animate_wave(u0, c=2.0, dt=1.0, dx=1.0, dy=1.0, frames=5)


def test_different_wave_speeds():
    """Test that different wave speeds produce different results."""
    u0 = create_gaussian_pulse(20, center=(10, 10), sigma=3, amplitude=1.0)
    
    # Run with different wave speeds
    u1 = solve_wave(u0, c=0.5, dt=0.05, dx=1.0, dy=1.0, steps=20)
    u2 = solve_wave(u0, c=1.0, dt=0.05, dx=1.0, dy=1.0, steps=20)
    
    # Results should be different
    assert not np.allclose(u1, u2)
    
    # Both should be stable (no infinite values)
    assert np.all(np.isfinite(u1))
    assert np.all(np.isfinite(u2))


def test_initial_velocity_effect():
    """Test that initial velocity affects wave evolution."""
    u0 = create_gaussian_pulse(20, center=(10, 10), sigma=3, amplitude=1.0)
    v0_zero = np.zeros_like(u0)
    v0_nonzero = np.ones_like(u0) * 0.1
    
    # Run with different initial velocities
    u1 = solve_wave(u0, v0_zero, c=1.0, dt=0.05, dx=1.0, dy=1.0, steps=10)
    u2 = solve_wave(u0, v0_nonzero, c=1.0, dt=0.05, dx=1.0, dy=1.0, steps=10)
    
    # Results should be different
    assert not np.allclose(u1, u2)
    
    # Both should be stable
    assert np.all(np.isfinite(u1))
    assert np.all(np.isfinite(u2))