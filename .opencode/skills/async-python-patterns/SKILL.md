---
name: async-python-patterns
description: "Master Python asyncio, concurrent programming, and async/await patterns for high-performance applications. Use when building async APIs, concurrent systems, or I/O-bound applications requiring non-blocking operations. Covers event loops, tasks, futures, and synchronization primitives."
---

# Async Python Patterns

Master Python's `asyncio` library for building high-performance, non-blocking applications.

## When to Use This Skill

- Building asynchronous web servers or APIs (FastAPI, aiohttp)
- Creating concurrent network clients or services
- Implementing I/O-bound operations efficiently (databases, file operations, network requests)
- Managing background tasks and schedulers
- Understanding event loops, coroutines, and tasks
- Utilizing synchronization primitives (locks, semaphores, events)

## Core Concepts

### 1. Event Loop

- The heart of `asyncio`, managing I/O and task scheduling.
- `asyncio.run()` starts the event loop.
- `asyncio.get_event_loop()` retrieves the current loop.

### 2. Coroutines (`async`/`await`)

- Functions defined with `async def`.
- Execution can be paused and resumed.
- `await` keyword yields control back to the event loop.

### 3. Tasks

- Wrappers around coroutines, scheduling their execution.
- `asyncio.create_task()` schedules a coroutine.
- `asyncio.gather()` runs multiple tasks concurrently.

### 4. Synchronization Primitives

- **Locks:** `asyncio.Lock` for mutual exclusion.
- **Semaphores:** `asyncio.Semaphore` to limit concurrent access.
- **Events:** `asyncio.Event` for signaling between tasks.
- **Queues:** `asyncio.Queue` for producer-consumer patterns.

## Key Patterns

### Pattern 1: Concurrent Network Requests (See references/concurrent-requests.md)

### Pattern 2: Background Task with Queue (See references/background-tasks.md)

## Best Practices

-   **Use `async with`** for context managers (sessions, locks).
-   **Avoid blocking calls** within coroutines.
-   **Handle exceptions gracefully** in tasks.
-   **Use `asyncio.gather`** for concurrent operations.
-   **Use `asyncio.create_task`** for background work.
-   **Use queues** for inter-task communication.
-   **Properly cancel tasks** when no longer needed.

## References

-   [Asyncio Official Documentation](references/official-docs.md)
-   [Real Python Asyncio Guide](references/real-python.md)
-   [aiohttp Documentation](references/aiohttp-docs.md)

---

**Remember:** Async programming requires a different mindset; embrace `await` to yield control effectively.
