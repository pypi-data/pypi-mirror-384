import numpy as np
from numba import njit

DEFAULT_ALGO_ID = 0
DEFAULT_LAMBDA = 0.5
DEFAULT_LOCAL_SEARCH = True
DEFAULT_SEED = 42
DEFAULT_MAX_ITER = 1000

@njit(fastmath=True, cache=True)
def tour_length_from_D(D, tour):
    total = 0.0
    for i in range(len(tour) - 1):
        total += D[tour[i], tour[i + 1]]
    total += D[tour[-1], tour[0]]
    return total

@njit(fastmath=True, cache=True)
def greedy_tsp(D):
    n = D.shape[0]
    visited = np.zeros(n, dtype=np.bool_)
    route = np.zeros(n, dtype=np.int64)
    route[0] = 0
    visited[0] = True
    for i in range(1, n):
        best_j = -1
        best_dist = 1e18
        for j in range(n):
            if not visited[j] and D[route[i - 1], j] < best_dist:
                best_j = j
                best_dist = D[route[i - 1], j]
        route[i] = best_j
        visited[best_j] = True
    return route

@njit(fastmath=True, cache=True)
def clarke_wright(D):
    n = D.shape[0]
    depot = 0
    savings = []
    for i in range(1, n):
        for j in range(i + 1, n):
            s = D[depot, i] + D[depot, j] - D[i, j]
            savings.append((s, i, j))
    savings.sort(key=lambda x: x[0], reverse=True)
    routes = [[i, depot] for i in range(1, n)]
    for s, i, j in savings:
        ri = rj = None
        for r in routes:
            if r[0] == i or r[-2] == i:
                ri = r
            if r[0] == j or r[-2] == j:
                rj = r
        if ri is not None and rj is not None and ri != rj:
            if ri[-2] == i and rj[0] == j:
                merged = ri[:-1] + rj
                routes.remove(ri)
                routes.remove(rj)
                routes.append(merged)
    best_route = [depot]
    for r in routes:
        if depot in r:
            continue
        best_route.extend(r[:-1])
    best_route.append(depot)
    return np.array(best_route, dtype=np.int64)

@njit(fastmath=True, cache=True)
def greedy_lambda_tsp(D, lambda_value=0.5):
    n = D.shape[0]
    depot = 0
    visited = np.zeros(n, dtype=np.bool_)
    route = np.zeros(n, dtype=np.int64)
    route[0] = depot
    visited[depot] = True
    for i in range(1, n):
        best_j = -1
        best_cost = 1e18
        for j in range(n):
            if visited[j]:
                continue
            cost = lambda_value * D[route[i - 1], j] + (1 - lambda_value) * (D[depot, route[i - 1]] + D[depot, j] - D[route[i - 1], j])
            if cost < best_cost:
                best_cost = cost
                best_j = j
        route[i] = best_j
        visited[best_j] = True
    return route

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

def build_tsp_route(D, algo_id=DEFAULT_ALGO_ID, local_search=DEFAULT_LOCAL_SEARCH,
                    lambda_value=DEFAULT_LAMBDA, max_iter=DEFAULT_MAX_ITER, seed=DEFAULT_SEED):
    np.random.seed(seed)
    if algo_id == 0:
        route = clarke_wright(D)
    elif algo_id == 1:
        route = greedy_tsp(D)
    elif algo_id == 2:
        route = greedy_lambda_tsp(D, lambda_value)
    else:
        raise ValueError("Invalid algo_id (0=Clarke–Wright, 1=Greedy, 2=Greedy+Lambda)")
    if local_search:
        route = two_opt(D, route, max_iter=max_iter)
    return route

def warmup():
    print("[tsp_cw] Warming up Numba kernels...")
    D = np.random.rand(6, 6)
    D = (D + D.T) / 2
    np.fill_diagonal(D, 0)
    build_tsp_route(D, algo_id=0, local_search=True)
    build_tsp_route(D, algo_id=1, local_search=False)
    build_tsp_route(D, algo_id=2, lambda_value=0.5)
    tour_length_from_D(D, np.arange(6))
    print("[tsp_cw] Kernels ready and cached!")

if __name__ == "__main__":
    warmup()
    print("Example run finished.")
