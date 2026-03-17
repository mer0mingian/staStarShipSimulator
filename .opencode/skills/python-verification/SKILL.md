---
name: python-verification
description: "Verify Python code quality through testing and performance profiling. Master TDD with pytest, fixtures, and mocking, and optimize hot paths using cProfile. Use when writing tests, debugging slow code, or verifying implementation completion. Cluster: Python Development (MERGED)"
---

# Python Verification & Performance

Ensure Python code works correctly and efficiently. This skill combines the discipline of Test-Driven Development (TDD) with technical performance profiling and optimization.

## When to Use This Skill

- Writing unit and integration tests with `pytest`
- Implementing features using TDD (Red-Green-Refactor)
- Debugging slow code or investigating performance bottlenecks
- Verifying code correctness before merge or completion
- Profiling memory usage and CPU time

## Core Principles

1.  **Tests as Documentation**: Well-written tests explain the intended behavior.
2.  **Red-Green-Refactor**: Always write a failing test first.
3.  **Isolation**: Use fixtures and mocking to isolate units under test.
4.  **Profile Before Optimizing**: Never guess where the bottleneck is.
5.  **Measure Twice**: Benchmark before and after optimization.

## Testing Patterns (pytest)

```python
import pytest

@pytest.fixture
def mock_db():
    # Setup
    yield Database()
    # Teardown

def test_behavior(mock_db):
    result = mock_db.query("...")
    assert result == expected
```

See [references/testing-patterns.md](references/testing-patterns.md) for more examples.

## Performance Profiling

| Tool | Purpose | Use Case |
|------|---------|----------|
| **cProfile** | Aggregate timing | Find which functions are slow |
| **line_profiler** | Line-by-line timing | Find which lines in a function are slow |
| **memory_profiler** | RAM usage | Detect memory leaks or heavy allocations |

See [references/profiling-guide.md](references/profiling-guide.md) for CLI commands.

## Verification Checklist

Before claiming a task is "Done":
- [ ] **Tests Written**: Unit tests for happy path and edge cases.
- [ ] **Tests Passing**: All project tests pass locally.
- [ ] **Coverage Verified**: No significant gaps in new logic.
- [ ] **Performance Checked**: No obvious $O(N^2)$ loops or blocking I/O in hot paths.
- [ ] **Linter Passing**: `ruff check` returns no errors.

## References

- [Pytest & TDD Patterns](references/testing-patterns.md)
- [Mocking & Fixtures Guide](references/mocking-fixtures.md)
- [Performance Profiling Guide](references/profiling-guide.md)
- [Optimization Strategies](references/optimization.md)

---

**Remember:** Code without tests is broken by design. Optimize only when measured.
