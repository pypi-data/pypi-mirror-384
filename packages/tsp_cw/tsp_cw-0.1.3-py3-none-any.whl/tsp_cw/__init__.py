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

# Try to safely load README.md if it exists nearby
try:
    here = Path(__file__).resolve().parent
    readme_candidates = [
        here / "README.md",           # if README packaged inside tsp_cw/
        here.parent / "README.md",    # if README is at project root
    ]
    for path in readme_candidates:
        if path.exists():
            __doc__ = path.read_text(encoding="utf-8")
            break
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
