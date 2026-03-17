---
name: python-failure-handling
description: "Master error handling and resilience in Python. Covers input validation, exception hierarchies, retries, and timeouts. Use when building robust APIs, handling external service failures, or implementing fail-fast validation. Cluster: Python Development (MERGED)"
---

# Python Failure Handling & Resilience

Build robust, fault-tolerant Python applications. This skill combines internal error management (validation, exceptions) with external resilience (retries, timeouts, circuit breakers).

## When to Use This Skill

- Implementing input validation (Pydantic, fail-fast)
- Designing application exception hierarchies
- Handling external service or network failures
- Adding retry logic with exponential backoff
- Implementing timeouts for I/O operations
- Managing partial failures in batch processing

## Core Principles

1.  **Fail Fast**: Validate at the boundary (API, CLI) before expensive operations.
2.  **Specific Exceptions**: Use `ValueError`, `TypeError`, or custom domain exceptions—never bare `Exception`.
3.  **Preserve Context**: Always use `raise ... from e` to maintain the error trail.
4.  **Differentiate Failures**: Retry transient issues (network); abort on permanent issues (logic, auth).
5.  **Bound Retries**: Always cap attempt counts and total duration.

## Internal Error Management (Validation)

```python
from pydantic import BaseModel, Field

class InputSchema(BaseModel):
    id: int = Field(gt=0)
    email: str

def process(data: dict):
    # Validate at the boundary
    validated = InputSchema.model_validate(data)
    ...
```

See [references/validation-patterns.md](references/validation-patterns.md) for more details.

## External Resilience (Retries & Timeouts)

Use `tenacity` for robust retries:

```python
from tenacity import retry, stop_after_attempt, wait_exponential_jitter

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential_jitter(initial=1, max=10),
)
def call_external_api():
    response = httpx.get("https://api.example.com", timeout=5.0)
    response.raise_for_status()
    return response.json()
```

See [references/resilience-patterns.md](references/resilience-patterns.md) for advanced patterns.

## Batch Processing & Partial Failures

Never let one bad item abort an entire batch. Use a result container to track successes and failures.

See [references/batch-processing.md](references/batch-processing.md).

## References

- [Validation & Exception Patterns](references/validation-patterns.md)
- [Resilience & Retry Patterns](references/resilience-patterns.md)
- [Batch Processing Guide](references/batch-processing.md)
- [Exception Hierarchy Design](references/exception-hierarchy.md)

---

**Remember:** Reliability is built at the boundaries. Validate what comes in, be resilient to what you call.
