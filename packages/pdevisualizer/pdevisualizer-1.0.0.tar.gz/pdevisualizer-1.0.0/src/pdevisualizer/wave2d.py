import numpy as np
from numba import njit
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation


@njit
def step_wave(u, u_prev, c, dt, dx, dy):
    """
    Perform one time step of the 2D wave equation using finite differences.
    
    Uses the explicit leapfrog scheme:
    u^(n+1) = 2u^n - u^(n-1) + c²dt²[(u^n_{i+1,j} - 2u^n_{i,j} + u^n_{i-1,j})/dx² + 
                                      (u^n_{i,j+1} - 2u^n_{i,j} + u^n_{i,j-1})/dy²]
    
    Parameters:
    -----------
    u : numpy.ndarray
        Current wave amplitude field
    u_prev : numpy.ndarray
        Previous time step wave amplitude field
    c : float
        Wave speed
    dt : float
        Time step size
    dx, dy : float
        Spatial grid spacing in x and y directions
    
    Returns:
    --------
    numpy.ndarray
        Updated wave amplitude field after one time step
    """
    nx, ny = u.shape
    u_next = np.zeros_like(u)
    
    # Apply finite difference scheme to interior points
    for i in range(1, nx-1):
        for j in range(1, ny-1):
            # Second derivatives
            d2u_dx2 = (u[i+1, j] - 2*u[i, j] + u[i-1, j]) / dx**2
            d2u_dy2 = (u[i, j+1] - 2*u[i, j] + u[i, j-1]) / dy**2
            
            # Leapfrog time stepping
            u_next[i, j] = (2*u[i, j] - u_prev[i, j] + 
                           c**2 * dt**2 * (d2u_dx2 + d2u_dy2))
    
    # Boundary conditions (fixed at zero - can be extended later)
    u_next[0, :] = 0.0    # Left boundary
    u_next[-1, :] = 0.0   # Right boundary
    u_next[:, 0] = 0.0    # Bottom boundary
    u_next[:, -1] = 0.0   # Top boundary
    
    return u_next


@njit
def step_wave_first(u0, v0, c, dt, dx, dy):
    """
    Perform the first time step of the wave equation using initial velocity.
    
    For the first step, we use: u^1 = u^0 + dt*v^0 + (dt²/2)*c²∇²u^0
    
    Parameters:
    -----------
    u0 : numpy.ndarray
        Initial wave amplitude field
    v0 : numpy.ndarray
        Initial velocity field (∂u/∂t at t=0)
    c : float
        Wave speed
    dt : float
        Time step size
    dx, dy : float
        Spatial grid spacing
    
    Returns:
    --------
    numpy.ndarray
        Wave amplitude field after first time step
    """
    nx, ny = u0.shape
    u1 = np.zeros_like(u0)
    
    # Apply first-step scheme to interior points
    for i in range(1, nx-1):
        for j in range(1, ny-1):
            # Second derivatives of u0
            d2u_dx2 = (u0[i+1, j] - 2*u0[i, j] + u0[i-1, j]) / dx**2
            d2u_dy2 = (u0[i, j+1] - 2*u0[i, j] + u0[i, j-1]) / dy**2
            
            # First time step formula
            u1[i, j] = (u0[i, j] + dt * v0[i, j] + 
                       0.5 * c**2 * dt**2 * (d2u_dx2 + d2u_dy2))
    
    # Boundary conditions
    u1[0, :] = 0.0
    u1[-1, :] = 0.0
    u1[:, 0] = 0.0
    u1[:, -1] = 0.0
    
    return u1


def solve_wave(u0, v0=None, c=1.0, dt=0.1, dx=1.0, dy=1.0, steps=100):
    """
    Solve the 2D wave equation for a given number of time steps.
    
    Parameters:
    -----------
    u0 : numpy.ndarray
        Initial wave amplitude field
    v0 : numpy.ndarray, optional
        Initial velocity field (default: zeros)
    c : float, optional
        Wave speed (default: 1.0)
    dt : float, optional
        Time step size (default: 0.1)
    dx, dy : float, optional
        Spatial grid spacing (default: 1.0)
    steps : int, optional
        Number of time steps to run (default: 100)
    
    Returns:
    --------
    numpy.ndarray
        Final wave amplitude field after all time steps
    
    Notes:
    ------
    For numerical stability, ensure: c * dt * sqrt(1/dx² + 1/dy²) ≤ 1 (CFL condition)
    """
    if v0 is None:
        v0 = np.zeros_like(u0)
    
    # Check CFL stability condition
    cfl_factor = c * dt * np.sqrt(1/dx**2 + 1/dy**2)
    if cfl_factor > 1.0:
        raise ValueError(f"CFL condition violated! "
                        f"CFL factor = {cfl_factor:.3f} > 1.0. "
                        f"Reduce dt or increase dx/dy.")
    
    # Initialize
    u_prev = u0.copy()
    u_curr = step_wave_first(u0, v0, c, dt, dx, dy)
    
    # Time stepping loop
    for _ in range(steps - 1):
        u_next = step_wave(u_curr, u_prev, c, dt, dx, dy)
        u_prev = u_curr
        u_curr = u_next
    
    return u_curr


def animate_wave(u0, v0=None, c=1.0, dt=0.1, dx=1.0, dy=1.0, frames=100, interval=50):
    """
    Animate the 2D wave equation starting from initial conditions.
    
    Parameters:
    -----------
    u0 : numpy.ndarray
        Initial wave amplitude field
    v0 : numpy.ndarray, optional
        Initial velocity field (default: zeros)
    c : float, optional
        Wave speed (default: 1.0)
    dt : float, optional
        Time step size (default: 0.1)
    dx, dy : float, optional
        Spatial grid spacing (default: 1.0)
    frames : int, optional
        Number of animation frames (default: 100)
    interval : int, optional
        Time between frames in milliseconds (default: 50)
    
    Returns:
    --------
    matplotlib.animation.FuncAnimation
        Animation object that can be displayed or saved
    """
    if v0 is None:
        v0 = np.zeros_like(u0)
    
    # Check CFL stability condition
    cfl_factor = c * dt * np.sqrt(1/dx**2 + 1/dy**2)
    if cfl_factor > 1.0:
        raise ValueError(f"CFL condition violated! "
                        f"CFL factor = {cfl_factor:.3f} > 1.0. "
                        f"Reduce dt or increase dx/dy.")
    
    # Initialize wave fields
    u_prev = u0.copy()
    u_curr = step_wave_first(u0, v0, c, dt, dx, dy)
    
    # Set up the plot
    fig, ax = plt.subplots(figsize=(10, 8))
    
    # Use a symmetric colormap for waves (negative and positive amplitudes)
    vmax = max(np.abs(u0).max(), 1.0)  # Ensure reasonable scale
    im = ax.imshow(u_curr, cmap="RdBu_r", origin="lower", 
                   vmin=-vmax, vmax=vmax, animated=True)
    
    ax.set_title("2D Wave Equation")
    ax.set_xlabel("x")
    ax.set_ylabel("y")
    plt.colorbar(im, ax=ax, label="Amplitude")
    
    # Add time display
    time_text = ax.text(0.02, 0.98, '', transform=ax.transAxes, 
                       fontsize=12, verticalalignment='top',
                       bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
    
    def update(frame):
        nonlocal u_prev, u_curr
        
        # Compute next time step
        u_next = step_wave(u_curr, u_prev, c, dt, dx, dy)
        
        # Update for next iteration
        u_prev = u_curr
        u_curr = u_next
        
        # Update plot
        im.set_array(u_curr)
        time_text.set_text(f'Time: {frame * dt:.2f}')
        
        return [im, time_text]
    
    return FuncAnimation(fig, update, frames=frames, interval=interval, blit=True)


def create_gaussian_pulse(grid_size, center, sigma, amplitude=1.0):
    """
    Create a Gaussian pulse initial condition.
    
    Parameters:
    -----------
    grid_size : int or tuple
        Size of the grid (if int, creates square grid)
    center : tuple
        Center position (x, y) of the pulse
    sigma : float
        Standard deviation of the Gaussian
    amplitude : float, optional
        Peak amplitude (default: 1.0)
    
    Returns:
    --------
    numpy.ndarray
        2D array with Gaussian pulse
    """
    if isinstance(grid_size, int):
        nx = ny = grid_size
    else:
        nx, ny = grid_size
    
    x = np.linspace(0, nx-1, nx)
    y = np.linspace(0, ny-1, ny)
    X, Y = np.meshgrid(x, y)
    
    cx, cy = center
    gaussian = amplitude * np.exp(-((X - cx)**2 + (Y - cy)**2) / (2 * sigma**2))
    
    return gaussian


def create_circular_wave(grid_size, center, radius, amplitude=1.0):
    """
    Create a circular wave initial condition.
    
    Parameters:
    -----------
    grid_size : int or tuple
        Size of the grid
    center : tuple
        Center position (x, y) of the circular wave
    radius : float
        Radius of the circular wave
    amplitude : float, optional
        Peak amplitude (default: 1.0)
    
    Returns:
    --------
    numpy.ndarray
        2D array with circular wave
    """
    if isinstance(grid_size, int):
        nx = ny = grid_size
    else:
        nx, ny = grid_size
    
    x = np.linspace(0, nx-1, nx)
    y = np.linspace(0, ny-1, ny)
    X, Y = np.meshgrid(x, y)
    
    cx, cy = center
    r = np.sqrt((X - cx)**2 + (Y - cy)**2)
    
    # Create a ring-like initial condition
    wave = amplitude * np.exp(-0.5 * ((r - radius) / 2)**2)
    
    return wave


if __name__ == "__main__":
    # Example 1: Gaussian pulse
    print("Creating Gaussian pulse animation...")
    grid_size = 100
    
    # Create a Gaussian pulse in the center
    u0 = create_gaussian_pulse(grid_size, center=(50, 50), sigma=5, amplitude=2.0)
    
    # Use stable parameters
    c = 1.0
    dt = 0.05
    dx = dy = 1.0
    
    print(f"Running with CFL factor: {c * dt * np.sqrt(1/dx**2 + 1/dy**2):.3f}")
    
    # Create animation
    anim = animate_wave(u0, c=c, dt=dt, dx=dx, dy=dy, frames=200, interval=50)
    anim.save("wave_gaussian.gif", writer="pillow")
    print("Saved wave_gaussian.gif")
    
    # Example 2: Circular wave
    print("\nCreating circular wave animation...")
    u0_circle = create_circular_wave(grid_size, center=(50, 50), radius=20, amplitude=1.0)
    
    anim2 = animate_wave(u0_circle, c=c, dt=dt, dx=dx, dy=dy, frames=200, interval=50)
    anim2.save("wave_circular.gif", writer="pillow")
    print("Saved wave_circular.gif")