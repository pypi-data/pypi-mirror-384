from numba import njit
import numpy as np

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
