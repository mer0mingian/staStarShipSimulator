---
name: javascript-testing-patterns
description: "Implement comprehensive testing strategies using Jest, Vitest, and Testing Library for unit tests, integration tests, and end-to-end testing with mocking, fixtures, and test-driven development. Use when writing JS/TS tests, setting up test infrastructure, or establishing testing standards. Cluster: JavaScript/TypeScript (SPLIT)"
---

# Modern JavaScript/TypeScript Testing Patterns (Jest/Vitest/Testing Library)

Master testing strategies for JavaScript and TypeScript applications using modern frameworks.

## When to Use This Skill

- Writing unit tests for utility functions and libraries
- Setting up integration tests for component interaction
- Implementing End-to-End (E2E) tests with Playwright/Cypress
- Mocking modules, APIs, and timers
- Adopting Test-Driven Development (TDD) in frontend/Node.js
- Configuring testing tools (Jest, Vitest, ts-jest)

## Core Concepts

### 1. Testing Frameworks
-   **Jest**: Comprehensive framework, all-in-one solution.
-   **Vitest**: Vite-native, faster startup, growing rapidly.
-   **Mocha/Chai**: Classic BDD setup.

### 2. Testing Library Philosophy (For UI Code)
-   Focus on testing user behavior, not implementation details.
-   Query elements by role, text, or label (accessibility first).
-   Avoid relying on component state/props directly.

### 3. Mocking Strategies
-   **Module Mocking**: Mock entire files (`jest.mock('./module')`).
-   **Function Mocking**: Mock specific functions or network calls (`jest.fn()`, `jest.spyOn`).
-   **Timer Mocks**: Control asynchronous timing (`jest.useFakeTimers()`).

## Key Patterns

### Pattern 1: Unit Testing with Jest

```javascript
// math.js
export const add = (a, b) => a + b;

// math.test.js
import { add } from './math';

describe('add function', () => {
  test('should add two positive numbers correctly', () => {
    expect(add(2, 3)).toBe(5);
  });

  test('should handle zero correctly', () => {
    expect(add(5, 0)).toBe(5);
  });

  test('should handle negative numbers', () => {
    expect(add(-5, 2)).toBe(-3);
  });
});
```

### Pattern 2: Component Integration Testing (React Testing Library)

```jsx
import { render, screen, fireEvent } from '@testing-library/react';
import Button from '../Button'; // Assuming component exists

test('button increments counter on click', () => {
  render(<Button initialCount={0} />);

  const button = screen.getByRole('button', { name: /count: 0/i });
  
  fireEvent.click(button); // Simulate user action
  
  // Assert based on the resulting DOM state
  expect(screen.getByRole('button', { name: /count: 1/i })).toBeInTheDocument();
});
```

### Pattern 3: Mocking API Responses

```javascript
// API call utility
const fetchUser = async (id) => {
  const res = await fetch(`/api/users/${id}`);
  if (!res.ok) throw new Error('Failed to fetch');
  return res.json();
};

// Test file
import { fetchUser } from '../api';
import { rest } from 'msw'; // Mock Service Worker for API mocking

server.use(
  rest.get('/api/users/:id', (req, res, ctx) => {
    const { id } = req.params;
    if (id === '1') {
      return res(ctx.status(200), ctx.json({ id: 1, name: 'Test User' }));
    }
    return res(ctx.status(404));
  })
);

test('fetchUser returns correct data for user 1', async () => {
  const user = await fetchUser(1);
  expect(user.name).toBe('Test User');
});
```

## Best Practices

-   **Naming:** Use descriptive names (`test_should_fail_when_input_is_empty`).
-   **Isolation:** Use fixtures/mocks for external state (network, storage).
-   **Async Testing:** Use `await` correctly and mock timers where appropriate.
-   **Code Coverage:** Aim for high coverage on critical business logic.

## References

-   [Jest Documentation](https://jestjs.io/docs/)
-   [Testing Library Docs](https://testing-library.com/docs/)
-   [MSW (Mock Service Worker)](https://mswjs.io/docs/)
-   [Vitest Documentation](https://vitest.dev/guide/)

---

**Remember:** Tests enforce correctness. Well-written tests *are* documentation. (Cluster: JavaScript/TypeScript)
