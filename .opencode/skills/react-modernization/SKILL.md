---
name: react-modernization
description: "Upgrade React applications to latest versions, migrate from class components to hooks, and adopt concurrent features. Use when modernizing React codebases, migrating to React Hooks, or upgrading to latest React versions. Cluster: Frontend/UI (SPLIT)"
---

# Modernizing React Codebases (Hooks & Concurrent Features)

Strategically upgrade legacy React applications, migrating from Class Components to Functional Components with Hooks, and adopting modern concurrent features.

## When to Use This Skill

- Migrating a large codebase from Class Components to Functional Components/Hooks
- Upgrading React framework versions (e.g., React 16 to 18+)
- Adopting concurrent rendering features (`useTransition`, `useDeferredValue`)
- Refactoring complex lifecycle methods into clean Effects
- Improving performance using state management modernization (Zustand/Query)

## Core Upgrade Path

The modernization path generally follows this sequence:

1.  **Dependencies:** Update React, ReactDOM, and tooling (`eslint-plugin-react-hooks`).
2.  **State/Lifecycle:** Migrate state management and lifecycle methods.
3.  **Concurrency:** Adopt concurrent features for non-blocking UI updates.
4.  **Cleanup:** Remove legacy patterns.

## Key Migration Steps

### Step 1: Class Components $\rightarrow$ Hooks

Focus on replacing lifecycle methods with Effect Hooks.

| Class Lifecycle Method | Hook Equivalent(s) | Notes |
|------------------------|--------------------|-------|
| `constructor`          | `useState`         | Initialize state |
| `componentDidMount`    | `useEffect(() => {}, [])` | Runs once after first render |
| `componentDidUpdate`   | `useEffect(() => {}, [deps])` | Runs when dependencies change |
| `componentWillUnmount` | `useEffect(() => { return () => {}; }, [])` | Cleanup function in Effect |
| `shouldComponentUpdate`| `React.memo`, `useMemo`, `useCallback` | Prevent unnecessary re-renders |

### Step 2: State Management Modernization
-   **Legacy:** Components manage local state via `this.setState`.
-   **Modern:** Use `useState` for local state; use context/Zustand/React Query for global state.

### Step 3: Adopting Concurrency (React 18+)
Implement features that allow React to interrupt urgent rendering tasks for critical updates.

-   **`useTransition`**: For state updates that should not block UI responsiveness (e.g., filtering large lists).
-   **`useDeferredValue`**: To defer recalculating a non-urgent part of the UI.

```tsx
// Example using useTransition for slow list filtering
const [isPending, startTransition] = useTransition();
const [filterText, setFilterText] = useState('');
const [listToRender, setListToRender] = useState(fullList);

const handleChange = (e) => {
  setFilterText(e.target.value); // Urgent update for input field
  startTransition(() => {
    // Non-urgent update that can be interrupted
    setListToRender(filterList(fullList, e.target.value)); 
  });
};

return (
    <>
        <input onChange={(e) => handleChange(e)} value={filterText} />
        {isPending && <LoadingSpinner />}
        {/* List renders quickly, then updates when transition finishes */}
        <List data={listToRender} /> 
    </>
);
```

## Best Practices

-   **Do not use state/props in dependency arrays**: Only use stable values.
-   **Cleanup Effects**: Always return a cleanup function for side effects that need teardown (timers, subscriptions).
-   **Strict Mode**: Enable React Strict Mode to catch side effects in effects.

## References

-   [React Hooks Documentation](references/react-hooks.html)
-   [React Concurrent Features](references/concurrent-features.html)
-   [Migrating to React 18](references/react-18-migration.html)

---

**Remember:** Hooks are functional; they replace class lifecycle methods with composable, declarative functions. (Cluster: Frontend/UI)
