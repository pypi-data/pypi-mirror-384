PDEVisualizer Documentation
===========================

**PDEVisualizer** is a lightweight, high-performance Python library for prototyping and visualizing partial differential equations (PDEs).

.. image:: https://badge.fury.io/py/pdevisualizer.svg
   :target: https://badge.fury.io/py/pdevisualizer
   :alt: PyPI version

.. image:: https://img.shields.io/badge/python-3.10+-blue.svg
   :target: https://www.python.org/downloads/
   :alt: Python 3.10+

.. image:: https://img.shields.io/badge/License-MIT-yellow.svg
   :target: https://opensource.org/licenses/MIT
   :alt: License: MIT

Quick Start
-----------

Install with pip:

.. code-block:: bash

   pip install pdevisualizer

Basic heat equation example:

.. code-block:: python

   from pdevisualizer.solver import PDESolver
   from pdevisualizer.boundary_conditions import BoundaryCondition
   import numpy as np

   # Create solver
   solver = PDESolver('heat', grid_shape=(50, 50))
   
   # Set Gaussian initial condition
   x = np.linspace(0, 1, 50)
   y = np.linspace(0, 1, 50)
   X, Y = np.meshgrid(x, y)
   u0 = 100 * np.exp(-((X-0.5)**2 + (Y-0.5)**2) / 0.01)
   solver.set_initial_conditions(u0)
   
   # Set boundary conditions
   solver.set_boundary_conditions(BoundaryCondition.dirichlet(0.0))
   
   # Solve
   solution = solver.solve(steps=200, alpha=0.5)

Features
--------

🔥 **Unified PDE Solver**
   - Heat equation (diffusion, thermal dynamics)
   - Wave equation (acoustic/seismic propagation)
   - Support for 2D domains

🎨 **Advanced Visualization**
   - Animated GIF/MP4 exports
   - 3D surface plots
   - Parameter exploration tools

🧪 **Boundary Conditions**
   - Dirichlet (fixed values)
   - Neumann (flux/gradient)
   - Periodic (wraparound)

📊 **Scientific Analysis**
   - Parameter sweeps
   - Sensitivity analysis
   - Stability checking

API Reference
-------------

.. toctree::
   :maxdepth: 2
   :caption: Modules

   api/solver
   api/boundary_conditions
   api/visualizations
   api/parameter_exploration

Indices and Tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`