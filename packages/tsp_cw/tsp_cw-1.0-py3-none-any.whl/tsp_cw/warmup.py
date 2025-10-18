import numpy as np
from .core import build_tsp_route
from .utils import tour_length_from_D

def warmup():
    print("[tsp_cw] Precompiling Numba kernels...")
    D = np.random.rand(6, 6)
    D = (D + D.T) / 2
    np.fill_diagonal(D, 0)
    build_tsp_route(D, algo_id=0, local_search=True)
    tour_length_from_D(D, np.arange(6))
    print("[tsp_cw] Warmup complete.")
