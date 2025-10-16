"""
Flexible boundary condition implementations for 2D PDEs.

This module provides functions to apply different types of boundary conditions
to 2D fields, supporting Dirichlet, Neumann, periodic, and absorbing boundaries.
"""

import numpy as np
from numba import njit
from typing import Dict, Any, Optional, Union
from enum import Enum


class BoundaryType(Enum):
    """Types of boundary conditions."""
    DIRICHLET = "dirichlet"  # Fixed value
    NEUMANN = "neumann"      # Fixed flux/derivative
    PERIODIC = "periodic"    # Wrap-around
    ABSORBING = "absorbing"  # Wave-absorbing


class BoundarySpec:
    """Specification for boundary conditions on all four edges."""
    
    def __init__(self, left=None, right=None, top=None, bottom=None):
        """
        Initialize boundary specification.
        
        Parameters:
        -----------
        left, right, top, bottom : dict or BoundaryType
            Boundary condition for each edge. Can be:
            - BoundaryType enum value
            - Dict with 'type' and 'value' keys
            - None (defaults to Dirichlet with value=0)
        """
        self.left = self._normalize_boundary(left)
        self.right = self._normalize_boundary(right)
        self.top = self._normalize_boundary(top)
        self.bottom = self._normalize_boundary(bottom)
    
    def _normalize_boundary(self, boundary):
        """Normalize boundary specification to standard format."""
        if boundary is None:
            return {'type': BoundaryType.DIRICHLET, 'value': 0.0}
        elif isinstance(boundary, BoundaryType):
            return {'type': boundary, 'value': 0.0}
        elif isinstance(boundary, dict):
            if 'type' not in boundary:
                raise ValueError("Boundary dict must have 'type' key")
            if 'value' not in boundary:
                boundary['value'] = 0.0
            return boundary
        else:
            raise ValueError(f"Invalid boundary specification: {boundary}")
    
    @classmethod
    def uniform(cls, boundary_type, value=0.0):
        """Create uniform boundary conditions on all edges."""
        spec = {'type': boundary_type, 'value': value}
        return cls(left=spec, right=spec, top=spec, bottom=spec)
    
    @classmethod
    def dirichlet(cls, value=0.0):
        """Create Dirichlet boundary conditions on all edges."""
        return cls.uniform(BoundaryType.DIRICHLET, value)
    
    @classmethod
    def neumann(cls, flux=0.0):
        """Create Neumann boundary conditions on all edges."""
        return cls.uniform(BoundaryType.NEUMANN, flux)
    
    @classmethod
    def periodic(cls):
        """Create periodic boundary conditions."""
        return cls.uniform(BoundaryType.PERIODIC)
    
    @classmethod
    def absorbing(cls):
        """Create absorbing boundary conditions."""
        return cls.uniform(BoundaryType.ABSORBING)


@njit
def apply_dirichlet_boundary(u, value):
    """Apply Dirichlet boundary condition (fixed value)."""
    nx, ny = u.shape
    u[0, :] = value      # Left edge
    u[-1, :] = value     # Right edge
    u[:, 0] = value      # Bottom edge
    u[:, -1] = value     # Top edge
    return u


@njit
def apply_neumann_boundary(u, flux, dx, dy):
    """Apply Neumann boundary condition (fixed flux/derivative)."""
    nx, ny = u.shape
    
    # Left edge: ∂u/∂x = flux at x=0
    u[0, :] = u[1, :] - flux * dx
    
    # Right edge: ∂u/∂x = flux at x=L
    u[-1, :] = u[-2, :] + flux * dx
    
    # Bottom edge: ∂u/∂y = flux at y=0
    u[:, 0] = u[:, 1] - flux * dy
    
    # Top edge: ∂u/∂y = flux at y=L
    u[:, -1] = u[:, -2] + flux * dy
    
    return u


@njit
def apply_periodic_boundary(u):
    """Apply periodic boundary condition (wrap-around)."""
    nx, ny = u.shape
    
    # Create a copy to avoid modifying corners multiple times
    u_out = u.copy()
    
    # Left-right periodicity
    u_out[0, 1:-1] = u[-2, 1:-1]   # Left edge = second-to-last interior
    u_out[-1, 1:-1] = u[1, 1:-1]   # Right edge = second interior
    
    # Bottom-top periodicity  
    u_out[1:-1, 0] = u[1:-1, -2]   # Bottom edge = second-to-last interior
    u_out[1:-1, -1] = u[1:-1, 1]   # Top edge = second interior
    
    # Handle corners
    u_out[0, 0] = u[-2, -2]     # Bottom-left corner
    u_out[0, -1] = u[-2, 1]     # Top-left corner
    u_out[-1, 0] = u[1, -2]     # Bottom-right corner
    u_out[-1, -1] = u[1, 1]     # Top-right corner
    
    return u_out


@njit
def apply_absorbing_boundary_first_order(u, u_prev, c, dt, dx, dy):
    """
    Apply first-order absorbing boundary condition for waves.
    
    Uses the Sommerfeld radiation condition:
    ∂u/∂t + c·∂u/∂n = 0 at boundaries
    
    This prevents wave reflections at boundaries.
    """
    nx, ny = u.shape
    
    # Left boundary (n points in +x direction)
    for j in range(1, ny-1):
        u[0, j] = u_prev[0, j] - (c * dt / dx) * (u[1, j] - u_prev[1, j])
    
    # Right boundary (n points in -x direction)
    for j in range(1, ny-1):
        u[-1, j] = u_prev[-1, j] - (c * dt / dx) * (u_prev[-2, j] - u[-2, j])
    
    # Bottom boundary (n points in +y direction)
    for i in range(1, nx-1):
        u[i, 0] = u_prev[i, 0] - (c * dt / dy) * (u[i, 1] - u_prev[i, 1])
    
    # Top boundary (n points in -y direction)
    for i in range(1, nx-1):
        u[i, -1] = u_prev[i, -1] - (c * dt / dy) * (u_prev[i, -2] - u[i, -2])
    
    return u


def apply_boundary_conditions(u, boundary_spec, dx=1.0, dy=1.0, 
                             u_prev=None, c=1.0, dt=0.1):
    """
    Apply boundary conditions to a 2D field.
    
    Parameters:
    -----------
    u : numpy.ndarray
        2D field to apply boundaries to
    boundary_spec : BoundarySpec
        Boundary condition specification
    dx, dy : float
        Grid spacing (needed for Neumann conditions)
    u_prev : numpy.ndarray, optional
        Previous time step (needed for absorbing conditions)
    c : float
        Wave speed (needed for absorbing conditions)
    dt : float
        Time step (needed for absorbing conditions)
    
    Returns:
    --------
    numpy.ndarray
        Field with boundary conditions applied
    """
    # For simplicity, we'll implement uniform boundary conditions first
    # Mixed boundaries (different on each edge) can be added later
    
    # Get the boundary type (assume uniform for now)
    boundary_type = boundary_spec.left['type']
    boundary_value = boundary_spec.left['value']
    
    if boundary_type == BoundaryType.DIRICHLET:
        u = apply_dirichlet_boundary(u, boundary_value)
        
    elif boundary_type == BoundaryType.NEUMANN:
        u = apply_neumann_boundary(u, boundary_value, dx, dy)
        
    elif boundary_type == BoundaryType.PERIODIC:
        u = apply_periodic_boundary(u)
        
    elif boundary_type == BoundaryType.ABSORBING:
        if u_prev is None:
            raise ValueError("Absorbing boundaries require previous time step (u_prev)")
        u = apply_absorbing_boundary_first_order(u, u_prev, c, dt, dx, dy)
    
    return u


@njit
def step_heat_with_boundaries(u, α, dt, dx, dy, boundary_spec_type, boundary_value):
    """
    Heat equation time step with flexible boundary conditions.
    
    This is an enhanced version of the original step_heat function.
    """
    nx, ny = u.shape
    out = u.copy()
    
    # Interior points - same as before
    for i in range(1, nx-1):
        for j in range(1, ny-1):
            out[i,j] = (
                u[i,j]
                + α * dt * (
                    (u[i+1,j] - 2*u[i,j] + u[i-1,j]) / dx**2
                    + (u[i,j+1] - 2*u[i,j] + u[i,j-1]) / dy**2
                )
            )
    
    # Apply boundary conditions
    if boundary_spec_type == 0:  # Dirichlet
        out = apply_dirichlet_boundary(out, boundary_value)
    elif boundary_spec_type == 1:  # Neumann
        out = apply_neumann_boundary(out, boundary_value, dx, dy)
    elif boundary_spec_type == 2:  # Periodic
        out = apply_periodic_boundary(out)
    
    return out


@njit
def step_wave_with_boundaries(u, u_prev, c, dt, dx, dy, boundary_spec_type, boundary_value):
    """
    Wave equation time step with flexible boundary conditions.
    
    This is an enhanced version of the original step_wave function.
    """
    nx, ny = u.shape
    u_next = np.zeros_like(u)
    
    # Interior points - same as before
    for i in range(1, nx-1):
        for j in range(1, ny-1):
            d2u_dx2 = (u[i+1, j] - 2*u[i, j] + u[i-1, j]) / dx**2
            d2u_dy2 = (u[i, j+1] - 2*u[i, j] + u[i, j-1]) / dy**2
            
            u_next[i, j] = (2*u[i, j] - u_prev[i, j] + 
                           c**2 * dt**2 * (d2u_dx2 + d2u_dy2))
    
    # Apply boundary conditions
    if boundary_spec_type == 0:  # Dirichlet
        u_next = apply_dirichlet_boundary(u_next, boundary_value)
    elif boundary_spec_type == 1:  # Neumann
        u_next = apply_neumann_boundary(u_next, boundary_value, dx, dy)
    elif boundary_spec_type == 2:  # Periodic
        u_next = apply_periodic_boundary(u_next)
    elif boundary_spec_type == 3:  # Absorbing
        u_next = apply_absorbing_boundary_first_order(u_next, u_prev, c, dt, dx, dy)
    
    return u_next


def solve_heat_with_boundaries(u0, boundary_spec, α=1.0, dt=0.1, dx=1.0, dy=1.0, steps=100):
    """
    Solve 2D heat equation with flexible boundary conditions.
    
    Parameters:
    -----------
    u0 : numpy.ndarray
        Initial temperature field
    boundary_spec : BoundarySpec
        Boundary condition specification
    α : float
        Thermal diffusivity
    dt : float
        Time step
    dx, dy : float
        Grid spacing
    steps : int
        Number of time steps
    
    Returns:
    --------
    numpy.ndarray
        Final temperature field
    """
    # Map boundary type to integer for Numba
    boundary_type_map = {
        BoundaryType.DIRICHLET: 0,
        BoundaryType.NEUMANN: 1,
        BoundaryType.PERIODIC: 2,
        BoundaryType.ABSORBING: 3
    }
    
    # Get boundary type and value
    boundary_type_enum = boundary_spec.left['type']
    boundary_value = boundary_spec.left['value']
    boundary_type = boundary_type_map[boundary_type_enum]
    
    u = u0.copy()
    
    for _ in range(steps):
        u = step_heat_with_boundaries(u, α, dt, dx, dy, boundary_type, boundary_value)
    
    return u


def solve_wave_with_boundaries(u0, boundary_spec, v0=None, c=1.0, dt=0.1, dx=1.0, dy=1.0, steps=100):
    """
    Solve 2D wave equation with flexible boundary conditions.
    
    Parameters:
    -----------
    u0 : numpy.ndarray
        Initial wave amplitude field
    boundary_spec : BoundarySpec
        Boundary condition specification
    v0 : numpy.ndarray, optional
        Initial velocity field
    c : float
        Wave speed
    dt : float
        Time step
    dx, dy : float
        Grid spacing
    steps : int
        Number of time steps
    
    Returns:
    --------
    numpy.ndarray
        Final wave amplitude field
    """
    if v0 is None:
        v0 = np.zeros_like(u0)
    
    # Map boundary type to integer for Numba
    boundary_type_map = {
        BoundaryType.DIRICHLET: 0,
        BoundaryType.NEUMANN: 1,
        BoundaryType.PERIODIC: 2,
        BoundaryType.ABSORBING: 3
    }
    
    boundary_type_enum = boundary_spec.left['type']
    boundary_value = boundary_spec.left['value']
    boundary_type = boundary_type_map[boundary_type_enum]
    
    # First step using initial velocity
    u_prev = u0.copy()
    u_curr = u0.copy()
    
    # Apply initial boundary conditions
    if boundary_type_enum != BoundaryType.ABSORBING:
        u_curr = apply_boundary_conditions(u_curr, boundary_spec, dx, dy)
    
    # First time step (different formula)
    nx, ny = u0.shape
    u_next = np.zeros_like(u0)
    
    for i in range(1, nx-1):
        for j in range(1, ny-1):
            d2u_dx2 = (u0[i+1, j] - 2*u0[i, j] + u0[i-1, j]) / dx**2
            d2u_dy2 = (u0[i, j+1] - 2*u0[i, j] + u0[i, j-1]) / dy**2
            
            u_next[i, j] = (u0[i, j] + dt * v0[i, j] + 
                           0.5 * c**2 * dt**2 * (d2u_dx2 + d2u_dy2))
    
    # Apply boundary conditions to first step
    if boundary_type_enum == BoundaryType.ABSORBING:
        u_next = apply_absorbing_boundary_first_order(u_next, u_prev, c, dt, dx, dy)
    else:
        u_next = apply_boundary_conditions(u_next, boundary_spec, dx, dy)
    
    u_prev = u_curr
    u_curr = u_next
    
    # Regular time steps
    for _ in range(steps - 1):
        u_next = step_wave_with_boundaries(u_curr, u_prev, c, dt, dx, dy, boundary_type, boundary_value)
        u_prev = u_curr
        u_curr = u_next
    
    return u_curr