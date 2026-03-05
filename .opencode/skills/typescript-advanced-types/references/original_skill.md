---
name: typescript-advanced-types
description: "Master TypeScript's advanced type system including generics, conditional types, mapped types, template literals, and utility types for building type-safe applications. Use when implementing complex type logic, creating reusable type utilities, or ensuring compile-time type safety in TypeScript projects. Cluster: JavaScript/TypeScript (SPLIT)"
---

# Advanced TypeScript Type System

Master advanced TypeScript features to build highly type-safe, robust, and maintainable codebases.

## When to Use This Skill

- Creating reusable, generic utility types (e.g., deep read-only, deep partial)
- Enforcing structure via mapped types
- Creating types derived from function signatures (e.g., parameters/return types)
- Constraining types based on run-time values (template literal types)
- Implementing structural checks (conditional types)
- Building type-safe libraries or frameworks

## Core Concepts

### 1. Generics
Types that are placeholders for a type parameter, enabling reusable components.

```typescript
// Generic Function
function identity<T>(arg: T): T {
    return arg;
}

// Generic Interface
interface Box<T> {
    value: T;
}
```

### 2. Conditional Types (The `extends` Ternary)
Types that evaluate to one of two types based on a condition.

```typescript
type IsString<T> = T extends string ? 'Yes' : 'No';

type A = IsString<string>; // type A = 'Yes'
type B = IsString<number>; // type B = 'No'

// Distributive Conditional Types (applies to union types)
type Boxed<T> = T extends string ? string[] : number[];
type C = Boxed<string | number>; // type C = string[] | number[] (Distributes over the union)
```

### 3. Mapped Types
Transforming properties of an existing type into a new type.

```typescript
type User = { id: number; name: string; active: boolean; };

// Make all properties optional
type PartialUser = { [K in keyof User]?: User[K] }; 
// { id?: number; name?: string; active?: boolean; }

// Make all properties readonly
type ReadonlyUser = { readonly [K in keyof User]: User[K] };
```

### 4. Utility Types & Combinations
-   **`Partial<T>`**: Makes all properties optional.
-   **`Required<T>`**: Makes all properties non-optional.
-   **`Pick<T, K>` / `Omit<T, K>`**: Select/exclude properties by key.
-   **`ReturnType<T>` / `Parameters<T>`**: Infer from function signatures.

## Advanced Patterns

### Pattern 1: Recursive Mapped Types (Deep Utility)
Use recursion to apply transformations (like `readonly` or `partial`) deeply into nested objects.

```typescript
type DeepReadonly<T> = T extends (infer R)[]
    ? DeepReadonlyArray<R>
    : T extends Function | Date | RegExp
    ? T
    : T extends object
    ? { readonly [K in keyof T]: DeepReadonly<T[K]> }
    : T;

type DeepReadonlyArray<T> = ReadonlyArray<DeepReadonly<T>>;

interface Config {
    server: { host: string; port: number };
    paths: string[];
}
type ImmutableConfig = DeepReadonly<Config>;
// ImmutableConfig is fully readonly, including nested properties and array elements.
```

### Pattern 2: Instance Type Utility
Infer the type of an instantiated class.

```typescript
class UserService {
    constructor(private db: Database) {}
    async find(id: number) { return this.db.find(id); }
}

// InstanceType<typeof UserService> will be:
// { find: (id: number) => Promise<User>, db: Database }
type UserServiceInstance = InstanceType<typeof UserService>;
```

### Pattern 3: Template Literal Types (String Manipulation)
Use template literals to constrain or modify string types at compile time.

```typescript
type APIEndpoints = 'users' | 'products' | 'orders';
type APIUrl = `/api/${APIEndpoints}`; // type APIUrl = "/api/users" | "/api/products" | "/api/orders"

type UppercaseAPI = Uppercase<APIEndpoints>; // type UppercaseAPI = "USERS" | "PRODUCTS" | "ORDERS"

type StringPrefix<S extends string, Prefix extends string> =
  S extends `${Prefix}${infer Rest}` ? Rest : S;

type PathWithoutPrefix = StringPrefix<APIUrl, '/api/'>; // type PathWithoutPrefix = "users" | "products" | "orders"
```

## Best Practices

-   **Prefer Structural Typing:** Use types that describe the *shape* of the data.
-   **Use `infer`** within conditional types for powerful type derivation.
-   **Don't Overuse `any`**: Use `unknown` when type information is missing initially.
-   **Use Utility Types**: Build complex types from built-in utilities (`Pick`, `Omit`, `Partial`).

## References

-   [TypeScript Handbook: Advanced Types](references/advanced-types.html)
-   [TypeScript Utility Types](references/utility-types.html)
-   [Conditional Types](references/conditional-types.html)

---

**Remember:** Advanced types are powerful for catching errors at compile time that would otherwise surface as runtime bugs. (Cluster: JavaScript/TypeScript)
