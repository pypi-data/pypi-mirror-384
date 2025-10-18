# tsp_cw — Numba-accelerated TSP Solver

`tsp_cw` là thư viện Python tăng tốc bằng **Numba JIT**, giúp giải nhanh bài toán **Travelling Salesman Problem (TSP)** bằng các heuristic kinh điển:
- Clarke–Wright Savings Algorithm  
- Greedy Heuristic  
- Greedy + λ Combination  
- Local Search 2-opt Optimization  

---

## ⚙️ Cài đặt

```bash
pip install tsp_cw
```

---

## 🚀 Hướng dẫn sử dụng

### 🔹 Ví dụ 1 — Giải TSP bằng Clarke–Wright

```python
import numpy as np
from tsp_cw import build_tsp_route, tour_length_from_D

D = np.array([
    [0, 2, 9, 10],
    [1, 0, 6, 4],
    [15, 7, 0, 8],
    [6, 3, 12, 0]
], dtype=np.float64)

route = build_tsp_route(D, algo_id=0, local_search=True)
print("Best route:", route)
print("Total distance:", tour_length_from_D(D, route))
```

---

### 🔹 Ví dụ 2 — So sánh nhiều thuật toán

```python
from tsp_cw import build_tsp_route, tour_length_from_D
import numpy as np

D = np.random.rand(10, 10)
D = (D + D.T) / 2
np.fill_diagonal(D, 0)

route_cw = build_tsp_route(D, algo_id=0)
route_greedy = build_tsp_route(D, algo_id=1)
route_lambda = build_tsp_route(D, algo_id=2, lambda_value=0.3)

print("CW:", tour_length_from_D(D, route_cw))
print("Greedy:", tour_length_from_D(D, route_greedy))
print("Greedy+λ:", tour_length_from_D(D, route_lambda))
```

---

### 🔹 Ví dụ 3 — Tuỳ chỉnh tham số nâng cao

```python
from tsp_cw import build_tsp_route

route = build_tsp_route(
    D, 
    algo_id=2,           # Greedy + λ
    lambda_value=0.4,    # trọng số saving vs distance
    local_search=True,   # bật tối ưu 2-opt
    max_iter=500,        # giới hạn số vòng lặp
    seed=123             # seed tái lập kết quả
)
print(route)
```

---

### 🔹 Ví dụ 4 — Warm-up để precompile Numba kernel

```python
import tsp_cw
tsp_cw.warmup()  # compile trước các kernel để lần sau chạy cực nhanh
```

---

### 🔹 Ví dụ 5 — Tích hợp trong project lớn (benchmark)

```python
import numpy as np, time
from tsp_cw import build_tsp_route, tour_length_from_D

for n in [50, 200, 1000]:
    D = np.random.rand(n, n)
    D = (D + D.T) / 2
    np.fill_diagonal(D, 0)
    start = time.time()
    route = build_tsp_route(D, algo_id=1)
    cost = tour_length_from_D(D, route)
    print(f"n={n:<4} | cost={cost:8.2f} | time={time.time() - start:.4f}s")
```

---

## 🧩 Tham số mặc định

| Tham số | Mặc định | Giải thích |
|----------|-----------|------------|
| `algo_id` | `0` | 0 = Clarke–Wright, 1 = Greedy, 2 = Greedy+λ |
| `lambda_value` | `0.5` | Trọng số giữa distance và saving |
| `local_search` | `True` | Có thực hiện 2-opt không |
| `max_iter` | `1000` | Số vòng tối đa trong 2-opt |
| `seed` | `42` | Seed ngẫu nhiên để tái lập |

---

## ⚡ Warm-up Kernels

```python
import tsp_cw
tsp_cw.warmup()
```

- Lần đầu chạy: JIT compile kernel (~1–2 s)  
- Sau đó: lấy từ cache `.nbi`, chạy gần như tức thì ⚡  

---

## 📈 Hiệu năng (Mac M1 Pro)

| n (điểm) | Clarke–Wright | Greedy | 2-opt cải thiện |
|-----------|---------------|---------|-----------------|
| 50 | 1.3 ms | 0.8 ms | +12 % |
| 200 | 8.5 ms | 5.2 ms | +8 % |
| 1000 | 63 ms | 42 ms | +5 % |

---

## 🧠 Hướng mở rộng
- Multi-depot VRP  
- Tabu Search / Simulated Annealing  
- GPU backend với `numba.cuda`  

---

## 📜 License
MIT © [Lê Sỹ Thức](https://github.com/thucnc7)
