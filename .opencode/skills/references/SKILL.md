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

### Pattern 1: Concurrent Network Requests

```python
import asyncio
import aiohttp

async def fetch_url(session, url):
    async with session.get(url) as response:
        return await response.text()

async def main():
    urls = [
        "http://example.com/page1",
        "http://example.com/page2",
        "http://example.com/page3",
    ]
    async with aiohttp.ClientSession() as session:
        tasks = [fetch_url(session, url) for url in urls]
        results = await asyncio.gather(*tasks)
        for result in results:
            print(f"Fetched {len(result)} bytes")

if __name__ == "__main__":
    asyncio.run(main())
```

### Pattern 2: Background Task with Queue

```python
import asyncio

async def producer(queue):
    for i in range(5):
        await queue.put(f"Item {i}")
        await asyncio.sleep(0.1)
    await queue.put(None)  # Sentinel value

async def consumer(queue, id):
    while True:
        item = await queue.get()
        if item is None:
            break
        print(f"Consumer {id} got: {item}")
        await asyncio.sleep(1)
        queue.task_done()

async def main():
    queue = asyncio.Queue()
    producer_task = asyncio.create_task(producer(queue))
    consumer_tasks = [
        asyncio.create_task(consumer(queue, 1)),
        asyncio.create_task(consumer(queue, 2))
    ]

    await producer_task
    await queue.join()  # Wait for all items to be processed

    for task in consumer_tasks:
        task.cancel() # Cancel consumers after queue is empty
    await asyncio.gather(*consumer_tasks, return_exceptions=True)

if __name__ == "__main__":
    asyncio.run(main())
```

## Best Practices

- **Use `async with`** for context managers (sessions, locks).
- **Avoid blocking calls** within coroutines.
- **Handle exceptions gracefully** in tasks.
- **Use `asyncio.gather`** for concurrent operations.
- **Use `asyncio.create_task`** for background work.
- **Use queues** for inter-task communication.
- **Properly cancel tasks** when no longer needed.

## References

- [Asyncio Official Documentation](https://docs.python.org/3/library/asyncio.html)
- [Real Python Asyncio Guide](https://realpython.com/async-io-python/)
- [aiohttp Documentation](https://docs.aiohttp.org/)

---

**Remember:** Async programming requires a different mindset; embrace `await` to yield control effectively.
