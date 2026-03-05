---
name: python-testing-patterns
description: "Implement comprehensive testing strategies with pytest, fixtures, mocking, and Test-Driven Development (TDD). Use when writing Python tests, setting up test suites, or implementing testing best practices. This skill includes guidance on test structure, TDD mapping, and testing async/database code. Cluster: Python Development (SPLIT)"
---

# Comprehensive Python Testing Patterns (pytest)

Master testing strategies for Python applications using `pytest`, fixtures, mocking, parameterization, and test-driven development practices.

## When to Use This Skill

- Writing unit tests for Python code
- Setting up test suites and test infrastructure
- Implementing Test-Driven Development (TDD)
- Creating integration tests for APIs and services
- Mocking external dependencies and services
- Testing async code and concurrent operations

## Core Concepts

### 1. Test Structure & Isolation
- **AAA Pattern**: Arrange, Act, Assert.
- **Isolation**: Tests must be independent; use fixtures for setup/teardown.

### 2. Key pytest Features
- **Fixtures**: Manage setup/teardown across scopes (`session`, `module`, `function`).
- **Mocking**: Use `unittest.mock.patch` or `pytest-mock` fixture.
- **Parameterization**: Use `@pytest.mark.parametrize` to run tests multiple times with different inputs.
- **Async**: Requires `@pytest.mark.asyncio` fixture/decorator.

### 3. TDD Mapping (See references/tdd-mapping.md)
1. **RED**: Write failing test based on requirements.
2. **GREEN**: Write minimum code to pass.
3. **REFACTOR**: Clean up while maintaining green tests.

## Fundamental Patterns

### Pattern 1: Basic pytest Tests (Cluster: Core Workflow)
-   Simple functions using standard `assert`.

### Pattern 2: Fixtures for Setup (Cluster: Core Workflow)
-   Use session/module/function scoped fixtures for controlled setup/teardown.

### Pattern 3: Parameterized Tests (Cluster: Code Quality)
-   Use `@pytest.mark.parametrize` to test multiple inputs/outputs efficiently.

### Pattern 4: Mocking External Calls (Cluster: Code Quality)
-   Patch dependencies (e.g., `requests.get`) to isolate units of code.

### Pattern 5: Test Exception Paths (Cluster: Code Quality)
-   Use `with pytest.raises(ExceptionType):` to assert exceptions are raised, optionally matching the message.

### Pattern 6: Testing Async Code (Cluster: Python Development)
-   Requires `@pytest.mark.asyncio` on test functions/fixtures.

### Pattern 7: Environment Manipulation (Cluster: Code Quality)
-   Use the built-in `monkeypatch` fixture to manage environment variables or object attributes temporarily.

### Pattern 8: Temporary Files/Dirs (Cluster: Code Quality)
-   Use the built-in `tmp_path` fixture to create isolated, temporary directories for file I/O tests.

### Pattern 9: Custom Fixtures and Conftest (Cluster: Core Workflow)
-   Shared setup logic belongs in `conftest.py`.

### Pattern 10: Property-Based Testing (Cluster: Code Quality)
-   Use `hypothesis` to generate random inputs that stress tested properties (e.g., sorting stability, commutativity).

## Best Practices

-   **Test Names:** Must be descriptive (e.g., `test_login_fails_with_invalid_password`).
-   **Fast Tests:** Avoid network/DB calls in unit tests; mock them.
-   **Coverage:** Measure what code is exercised; prioritize quality.

## References

-   [Pytest Documentation](references/pytest-docs.md)
-   [Pytest Fixtures Guide](references/fixtures-guide.md)
-   [Pytest Mocking Guide](references/mocking-guide.md)
-   [Hypothesis Documentation](references/hypothesis.md)

---

**Remember:** Tests are your primary form of documentation and safety net. Invest in them. (Cluster: Python Development)
