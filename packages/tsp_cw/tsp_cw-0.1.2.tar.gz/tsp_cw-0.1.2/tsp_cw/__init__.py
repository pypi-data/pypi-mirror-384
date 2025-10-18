"""
tsp_cw — Numba-accelerated TSP Solver
-------------------------------------
A lightweight TSP/VRP heuristic library accelerated by Numba JIT.

Includes:
- Clarke–Wright Savings
- Greedy
- Greedy + λ Combination
- 2-opt Local Search Optimization

Quick usage:
    >>> import numpy as np
    >>> from tsp_cw import build_tsp_route
    >>> D = np.random.rand(6, 6)
    >>> D = (D + D.T) / 2; np.fill_diagonal(D, 0)
    >>> route = build_tsp_route(D)
    >>> print(route)
"""

from pathlib import Path

# Try to load full README.md content into __doc__
try:
    readme_path = Path(__file__).resolve().parent.parent / "README.md"
    if readme_path.exists():
        __doc__ = readme_path.read_text(encoding="utf-8")
    else:
        __doc__ += "\n\n(README.md not found — showing short summary instead.)"
except Exception as e:
    __doc__ += f"\n\n(Unable to load README.md: {e})"

# Import core functions
from .tsp_cw import (
    build_tsp_route,
    tour_length_from_D,
    warmup,
)
