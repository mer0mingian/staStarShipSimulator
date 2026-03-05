---
name: nextjs-app-router-patterns
description: "Master Next.js 14+ App Router with Server Components, streaming, parallel routes, and advanced data fetching. Use when building Next.js applications, implementing SSR/SSG, or optimizing React Server Components. Cluster: JavaScript/TypeScript (SPLIT)"
---

# Next.js 14+ App Router Mastery

Mastering the App Router paradigm in Next.js 14+ for building modern, performant, server-centric React applications.

## When to Use This Skill

- Starting a new Next.js project with the App Router
- Implementing Server Components for default data fetching
- Using streaming to improve perceived performance (Time To First Byte)
- Managing complex UI states with Parallel Routes
- Optimizing data fetching strategies (Server vs Client)
- Handling complex layouts and nested routing

## Core Concepts

### 1. Server Components (Default)
-   Components run exclusively on the server by default.
-   Ideal for data fetching, file system access, and heavy computation.
-   Cannot use state (`useState`), effects (`useEffect`), or browser APIs directly.

### 2. Client Components (`"use client"`)
-   Opt-in only for interactivity.
-   Place at the top level of interactivity boundaries (e.g., stateful forms, mouse tracking).

### 3. Data Fetching
-   **Server Components:** Use native `fetch` (with Next.js caching layer) or external libraries that support Server Components (e.g., Prisma, specialized SDKs).
-   **Client Components:** Use `useEffect` + `fetch`, SWR, or React Query.

### 4. Layouts and Routing
-   **`layout.js`**: Wraps children segments, survives navigation.
-   **`page.js`**: Renders the UI for a specific route segment.
-   **`loading.js`**: Shows suspense boundary fallback while loading.
-   **`error.js`**: Catches rendering errors within the segment.

## Key Patterns

### Pattern 1: Streaming Data from Server Components (Cluster: Frontend/UI)

Use `Suspense` boundary around data fetching in Server Components for progressive rendering.

```tsx
// app/dashboard/page.tsx (Server Component)
import { Suspense } from 'react';
import { UserList } from './UserList';
import { StatsWidget } from './StatsWidget';

export default function DashboardPage() {
  return (
    <div>
      <h1>Dashboard</h1>
      <StatsWidget /> 
      <Suspense fallback={<LoadingSpinner />}>
        <UserList />
      </Suspense>
    </div>
  );
}

// app/dashboard/UserList.tsx (Server Component that fetches data)
async function fetchUsers() {
  // Native fetch is automatically cached/deduplicated by Next.js
  const res = await fetch('https://api.example.com/users', { cache: 'no-store' }); 
  if (!res.ok) throw new Error('Failed to fetch');
  return res.json();
}

export async function UserList() {
  const users = await fetchUsers();
  return (
    <ul>
      {users.map(user => <li key={user.id}>{user.name}</li>)}
    </ul>
  );
}
```

### Pattern 2: Parallel Routes for Layout Independence (Cluster: Frontend/UI)
Use `(folder-name)` to create routes that render side-by-side without affecting the main path structure.

### Pattern 3: Revalidating Data (Cluster: Frontend/UI)
Use `revalidateTag` or `revalidatePath` within Server Actions or server-side data fetching to selectively clear the Next.js cache.

## Best Practices

-   **Colocate State:** Keep client components as shallow as possible; use them only where interactivity is mandatory.
-   **Server Actions:** Use for mutations (POST/PUT/DELETE) instead of client-side fetches to internal APIs.
-   **Caching Strategy:** Rely on Next.js's default caching (`force-cache`) and only use `{ cache: 'no-store' }` for dynamic content.
-   **Layouts:** Keep layouts simple and focused on shared UI shells.

## References

-   [Next.js App Router Docs](references/app-router-docs.html)
-   [Server Components vs. Client Components](references/server-client-components.html)
-   [Data Fetching in App Router](references/data-fetching.html)
-   [Next.js Server Actions](references/server-actions.html)

---

**Remember:** The App Router is server-first. Move logic server-side unless you need direct browser interaction. (Cluster: JavaScript/TypeScript)
