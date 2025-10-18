from numba import njit
import numpy as np

@njit(fastmath=True, cache=True)
def tour_length_from_D(D, route):
    total = 0.0
    for i in range(len(route) - 1):
        total += D[route[i], route[i + 1]]
    total += D[route[-1], route[0]]
    return total

@njit(fastmath=True, cache=True)
def two_opt(D, route, max_iter=1000):
    improved = True
    n = len(route)
    best_route = route.copy()
    best_length = tour_length_from_D(D, route)
    iter_count = 0
    while improved and iter_count < max_iter:
        improved = False
        iter_count += 1
        for i in range(1, n - 2):
            for j in range(i + 1, n - 1):
                if j - i == 1:
                    continue
                new_route = np.concatenate((best_route[:i], best_route[i:j][::-1], best_route[j:]))
                new_length = tour_length_from_D(D, new_route)
                if new_length < best_length:
                    best_route = new_route
                    best_length = new_length
                    improved = True
    return best_route
