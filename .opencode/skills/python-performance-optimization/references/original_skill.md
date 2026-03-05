---
name: python-performance-optimization
description: "Profile and optimize Python code using cProfile, memory profilers, and performance best practices. Use when debugging slow Python code, optimizing bottlenecks, or improving application performance. Focuses on CPU and memory analysis. Cluster: Python Development (SPLIT)"
---

# Python Performance Optimization

Techniques to profile, analyze, and optimize Python code bottlenecks, focusing on CPU time and memory usage.

## When to Use This Skill

- Identifying slow areas in production code
- Reducing memory footprint of I/O-bound services
- Choosing fast data structures and algorithms
- Debugging unexpected memory growth (leaks)

## Core Tools

### 1. CPU Profiling
-   **`cProfile`**: Built-in standard library profiler. Best for aggregate function call time.
-   **`line_profiler`**: Shows time spent on *each line* within functions.

### 2. Memory Profiling
-   **`memory_profiler`**: Tracks memory usage line-by-line.
-   **`tracemalloc`**: Built-in module for tracing memory allocations.

## Key Patterns

### Pattern 1: CPU Profiling with cProfile
Use `cProfile` to identify the hot spots in your code execution.
```bash
# Run script with cProfile and output stats to file
python -m cProfile -o profile.stats your_script.py

# Analyze the profile data (requires SnakeViz)
pip install snakeviz
snakeviz profile.stats
```

### Pattern 2: Line Profiling
Use `@profile` decorator (requires installing `line_profiler`).
```python
# my_slow_module.py
from memory_profiler import profile

@profile
def complex_calculation(n):
    # This is the slow part
    result = sum(i*i for i in range(n))
    return result

# Run profiler
kernprof -l -v my_slow_module.py
```

### Pattern 3: Memory Profiling
Use `@profile` from `memory_profiler` to see line-by-line RAM usage.
```python
# my_memory_hog.py
from memory_profiler import profile

@profile
def create_large_list():
    # This causes significant allocation
    big_list = [b'X' * 1024] * 100000 # 100MB list
    return big_list
```

## Optimization Strategies

1.  **Algorithm Choice:** Replace $O(N^2)$ with $O(N \log N)$ or $O(N)$.
2.  **Data Structures:** Use sets/dicts over lists for membership testing/lookups.
3.  **Built-ins:** Leverage C-optimized built-ins (`sum`, list comprehensions) over manual loops.
4.  **Caching:** Use `@functools.lru_cache` for expensive, pure functions.
5.  **I/O Bound:** If I/O is the bottleneck, use `asyncio` (see `async-python-patterns` skill).
6.  **Heavy Compute:** Use NumPy or offload to Cython/Rust via `PyO3` or `Cython`.

## Best Practices

-   **Profile Before Optimizing**: Never guess where the bottleneck is.
-   **Benchmark**: Measure impact before and after changes.
-   **Focus on Hot Paths**: 90% of time is spent in 10% of code.

## References

-   [cProfile Documentation](references/cprofile-docs.md)
-   [line_profiler GitHub](references/line-profiler-github.md)
-   [memory_profiler GitHub](references/memory-profiler-github.md)
-   [functools.lru_cache](references/lru-cache-docs.md)

---

**Remember:** Optimization is iterative. Profile, optimize, measure, repeat. (Cluster: Python Development)
