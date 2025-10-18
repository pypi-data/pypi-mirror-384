from numba import njit
import numpy as np
from .heuristics import clarke_wright, greedy_tsp, greedy_lambda_tsp
from .utils import tour_length_from_D, two_opt

@njit(fastmath=True, cache=True)
def build_tsp_route(D, algo_id=0, local_search=True, lambda_value=0.5, max_iter=1000):
    if algo_id == 0:
        route = clarke_wright(D)
    elif algo_id == 1:
        route = greedy_tsp(D)
    elif algo_id == 2:
        route = greedy_lambda_tsp(D, lambda_value)
    else:
        raise ValueError("Invalid algo_id")
    if local_search:
        route = two_opt(D, route, max_iter)
    return route
