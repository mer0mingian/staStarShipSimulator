---
name: modern-javascript-patterns
description: "Master ES6+ features including async/await, destructuring, spread operators, arrow functions, promises, modules, iterators, generators, and functional programming patterns for writing clean, efficient JavaScript code. Use when refactoring legacy code, implementing modern patterns, or optimizing JavaScript applications. Cluster: JavaScript/TypeScript (SPLIT)"
---

# Modern JavaScript/TypeScript Patterns (ES6+)

Write clean, efficient, and maintainable code using modern ECMAScript features (ES6+).

## When to Use This Skill

- Refactoring older JavaScript code (pre-ES6)
- Writing clean, declarative functions
- Managing asynchronous operations reliably
- Improving code readability with modern syntax
- Working with React/Node/TypeScript projects

## Core Features & Syntax

### 1. Asynchronous Programming
-   **Promises**: Manage asynchronous operations (e.g., `fetch`, DB calls).
-   **`async`/`await`**: Syntactic sugar over Promises for sequential-looking async code.

### 2. Data Manipulation
-   **Spread/Rest Operators (`...`)**: Copy objects/arrays immutably; collect arguments.
-   **Destructuring**: Easily extract values from objects/arrays.

### 3. Functions & Scope
-   **Arrow Functions (`=>`)**: Lexical `this` binding; cleaner syntax.
-   **Default Parameters**: Set fallback values for missing arguments.

### 4. Modules
-   **ES Modules (`import`/`export`)**: Standardized way to structure code dependencies.

## Key Patterns

### Pattern 1: Immutable Updates with Spread (Cluster: Frontend/UI)

Always prefer creating new objects/arrays over mutating existing ones to ensure predictable state changes.

```javascript
const user = { id: 1, name: "Alice", settings: { theme: "dark" }, posts: [] };

// 1. Updating a top-level property
const updatedUser1 = { ...user, name: "Alicia" };

// 2. Deep update (must spread all intermediate layers)
const updatedUser2 = {
    ...user,
    settings: {
        ...user.settings,
        theme: "light" // Override only theme
    }
};

// 3. Adding to an array (immutably)
const newPosts = ["Post A", "Post B"];
const userWithPosts = { ...user, posts: [...user.posts, ...newPosts] };
```

### Pattern 2: Promise Chaining & Error Handling (Cluster: Code Quality)
Use `.then()` for success and `.catch()` for reliable error handling.

```javascript
fetch('/api/data')
    .then(response => {
        if (!response.ok) throw new Error('Network response was not ok');
        return response.json();
    })
    .then(data => {
        console.log('Data received:', data);
    })
    .catch(error => {
        console.error('Fetch failed:', error.message);
    });
```

### Pattern 3: Destructuring in Function Signatures (Cluster: Frontend/UI)
Makes function signatures self-documenting and safer.

```javascript
// GOOD: Explicitly defines expected keys and provides defaults
function displayUser({ name, email, role = 'guest' }) {
    console.log(`Name: ${name}, Role: ${role}`);
}
```

### Pattern 4: Functional Programming Concepts (Cluster: General)
-   **Immutability**: Data structures should not change after creation.
-   **Pure Functions**: Given the same input, always return the same output, no side effects.
-   **Composition**: Building complex logic by chaining simple, pure functions.

## Best Practices

-   **Prefer `const` and `let`** over `var`.
-   **Use template literals** (`` ` ``) for string interpolation.
-   **Use Optional Chaining (`?.`) and Nullish Coalescing (`??`)** for safer property access.
-   **Always use Modules** (`import`/`export`) for structure.

## References

-   [MDN JavaScript Guide](references/mdn-guide.html)
-   [JavaScript.info ES6+ Features](references/javascript-info.html)
-   [Functional Programming in JS](references/fp-guide.html)

---

**Remember:** Modern JavaScript prioritizes immutability and declarative coding styles for improved reliability. (Cluster: JavaScript/TypeScript)
