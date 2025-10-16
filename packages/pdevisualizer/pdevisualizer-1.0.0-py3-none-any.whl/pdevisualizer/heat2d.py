import numpy as np
from numba import njit
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation


@njit
def step_heat(u, α, dt, dx, dy):
    """
    Perform one time step of the 2D heat equation using finite differences.
    
    Parameters:
    -----------
    u : numpy.ndarray
        2D array representing the temperature field
    α : float
        Thermal diffusivity coefficient
    dt : float
        Time step size
    dx, dy : float
        Spatial grid spacing in x and y directions
    
    Returns:
    --------
    numpy.ndarray
        Updated temperature field after one time step
    """
    nx, ny = u.shape
    out = u.copy()
    
    # Apply finite difference scheme to interior points
    for i in range(1, nx-1):
        for j in range(1, ny-1):
            out[i,j] = (
                u[i,j]
                + α * dt * (
                    (u[i+1,j] - 2*u[i,j] + u[i-1,j]) / dx**2
                    + (u[i,j+1] - 2*u[i,j] + u[i,j-1]) / dy**2
                )
            )
    
    return out


def solve_heat(u0, α=1.0, dt=0.1, dx=1.0, dy=1.0, steps=100):
    """
    Solve the 2D heat equation for a given number of time steps.
    
    Parameters:
    -----------
    u0 : numpy.ndarray
        Initial temperature field
    α : float, optional
        Thermal diffusivity coefficient (default: 1.0)
    dt : float, optional
        Time step size (default: 0.1)
    dx, dy : float, optional
        Spatial grid spacing (default: 1.0)
    steps : int, optional
        Number of time steps to run (default: 100)
    
    Returns:
    --------
    numpy.ndarray
        Final temperature field after all time steps
    
    Notes:
    ------
    For numerical stability, ensure: α * dt * (1/dx² + 1/dy²) ≤ 0.5
    """
    # Validate stability condition
    stability_factor = α * dt * (1/dx**2 + 1/dy**2)
    if stability_factor > 0.5:
        raise ValueError(f"Numerical instability detected! "
                        f"Stability factor = {stability_factor:.3f} > 0.5. "
                        f"Reduce dt or increase dx/dy.")
    
    u = u0.copy()
    for _ in range(steps):
        u = step_heat(u, α, dt, dx, dy)
    return u


def animate_heat(u0, α=1.0, dt=0.1, dx=1.0, dy=1.0, frames=100, interval=50):
    """
    Animate the 2D heat equation starting from initial field u0.
    
    Parameters:
    -----------
    u0 : numpy.ndarray
        Initial temperature field
    α : float, optional
        Thermal diffusivity coefficient (default: 1.0)
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
    # Validate stability condition
    stability_factor = α * dt * (1/dx**2 + 1/dy**2)
    if stability_factor > 0.5:
        raise ValueError(f"Numerical instability detected! "
                        f"Stability factor = {stability_factor:.3f} > 0.5. "
                        f"Reduce dt or increase dx/dy.")
    
    u = u0.copy()
    fig, ax = plt.subplots(figsize=(8, 6))
    im = ax.imshow(u, cmap="hot", origin="lower")
    ax.set_title("2D Heat Equation")
    ax.set_xlabel("x")
    ax.set_ylabel("y")
    plt.colorbar(im, ax=ax, label="Temperature")
    
    def update(frame):
        nonlocal u
        u = step_heat(u, α, dt, dx, dy)  # Step once per frame
        im.set_array(u)
        return (im,)
    
    return FuncAnimation(fig, update, frames=frames, interval=interval, blit=True)


if __name__ == "__main__":
    # Example: hot spot in center
    grid_size = 100
    u0 = np.zeros((grid_size, grid_size))
    u0[grid_size//2, grid_size//2] = 100
    
    # Use stable parameters
    α = 0.25  # Reduced for better stability margin
    dt = 0.1
    dx = dy = 1.0
    
    print(f"Running with stability factor: {α * dt * (1/dx**2 + 1/dy**2):.3f}")
    
    anim = animate_heat(u0, α=α, dt=dt, dx=dx, dy=dy, frames=200, interval=50)
    anim.save("heat.gif", writer="pillow")  # Use pillow instead of imagemagick
    print("Saved heat.gif")