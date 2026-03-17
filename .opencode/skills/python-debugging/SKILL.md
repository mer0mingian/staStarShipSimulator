---
name: python-debugging
description: "Master systematic debugging in Python using pdb, logging, and performance profiling. Apply the scientific method to isolate and fix bugs. Use when investigating Python bugs, performance issues, or unexpected behavior. Cluster: Python Development (MERGED)"
---

# Python Debugging & Root Cause Analysis

Transform Python debugging from guesswork into a systematic process. This skill combines the "Scientific Method" with Python-specific tools like `pdb`, `breakpoint()`, and `cProfile`.

## When to Use This Skill

- Tracking down elusive Python bugs
- Investigating performance bottlenecks or memory leaks
- Understanding unfamiliar Python codebases
- Debugging production issues through logs and post-mortems

## The Systematic Process

1.  **Reproduce**: Create a minimal, consistent reproduction case.
2.  **Observe**: Gather stack traces, logs, and environment details.
3.  **Hypothesize**: What could be causing this? (Input? Logic? I/O?)
4.  **Experiment**: Test one change at a time.
5.  **Verify**: Confirm the fix works and doesn't break regressions.

## Essential Python Tools

### 1. In-Code Debugging

```python
# Modern Python 3.7+
breakpoint()

# Older versions
import pdb; pdb.set_trace()
```

### 2. Logging for Discovery

```python
import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

logger.debug(f"State at point A: {state}")
```

### 3. Post-Mortem Debugging

```python
try:
    risky_operation()
except Exception:
    import pdb
    pdb.post_mortem()
```

### 4. Performance & Memory Profiling

-   **`cProfile`**: Standard library CPU profiler.
-   **`tracemalloc`**: Standard library memory allocation tracer.

## Advanced Techniques

-   **Binary Search**: Comment out half the code to isolate the failure.
-   **Differential Debugging**: Compare working vs. broken environments (e.g., Python version, dependencies).
-   **Git Bisect**: Find the exact commit that introduced a regression.

## Verification Workflow

1.  **Identify failure**: Error message or incorrect behavior.
2.  **Reproduction script**: Smallest possible code to trigger the bug.
3.  **Debugging run**: Use `breakpoint()` to inspect local state.
4.  **Apply fix**: Minimal change required.
5.  **Test loop**: Run reproduction script + existing test suite.

## References

- [Python Debugging Tools (pdb, logging)](references/debugging-tools.md)
- [Performance & Memory Profiling](references/profiling.md)
- [The Scientific Method for Debugging](references/scientific-method.md)
- [Common Python Bugs & Fixes](references/common-bugs.md)

---

**Remember:** Reproduce first, fix second. Don't change more than one thing at a time.
