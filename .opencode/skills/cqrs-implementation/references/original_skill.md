---
name: cqrs-implementation
description: "Implement Command Query Responsibility Segregation (CQRS) for scalable architectures. Use when separating read and write models, optimizing query performance, or building event-sourced systems. Focuses on decoupling CRUD operations and optimizing data stores independently. Cluster: Architecture (SPLIT)"
---

# Command Query Responsibility Segregation (CQRS)

Implement CQRS by separating the models and interfaces used for updating data (Commands) from those used for reading data (Queries).

## When to Use This Skill

- When read and write loads are significantly different (high read volume).
- When performance optimization for reads requires a different data store (e.g., denormalized view).
- Building systems that benefit from event sourcing or eventual consistency.
- When business complexity requires distinct aggregate models for updates and reads.

## Core Components

### 1. Commands (Write Side)
-   **Purpose:** Handle state changes (Create, Update, Delete).
-   **Model:** Optimized for business logic, transactions, and consistency. Often maps directly to a Domain Model/Aggregate Root.
-   **Output:** Commands usually result in an Event or a success/failure response.

### 2. Queries (Read Side)
-   **Purpose:** Retrieve data (Read operations).
-   **Model:** Optimized for fast retrieval (denormalized, materialized views, simple projections).
-   **Decoupled:** Queries should not know about command logic or transactional boundaries.

### 3. Event/Projection Layer (Optional but common)
-   Commands result in Events.
-   Events are consumed by **Projections** which update the Read Model.

## Key Patterns

### Pattern 1: Separate Models (Cluster: Architecture)

The write model validates business rules; the read model optimizes for presentation.

```typescript
// Write Model (e.g., SQL/Transactional DB)
interface UserAggregate {
    id: string;
    firstName: string;
    lastName: string;
    email: string;
    version: number;
    changeName(newName: string): DomainEvent[]; // Business logic here
}

// Read Model (e.g., NoSQL/Materialized View)
interface UserView {
    userId: string; // Primary Key
    fullName: string; // Denormalized for fast display
    status: 'Active' | 'Pending'; // Derived state
}
```

### Pattern 2: Asynchronous Projection Update (Eventual Consistency)

Use an event stream to update the read model asynchronously.

```mermaid
graph LR
    A[Client sends Command] --> B{Command Handler};
    B -- Saves Aggregate --> C[Write DB];
    C -- Publishes Event --> D(Message Broker/Stream);
    D -- Event Consumed --> E[Projection Service];
    E -- Updates Read Model --> F[Read DB/Cache];
    F <-- Responds to Query --> G[Client Query];
```

### Pattern 3: Query Handlers

Queries are simple functions that bypass the write stack entirely.

```typescript
// services/readService.ts
async function getUserView(userId: string): Promise<UserView> {
    // Query directly into the optimized read model store (e.g., MongoDB or Redis)
    const readDoc = await ReadDB.users.findOne({ userId });
    
    if (!readDoc) throw new NotFoundError();
    
    return {
        userId: readDoc.id,
        fullName: `${readDoc.firstName} ${readDoc.lastName}`, // Denormalized for display
        status: readDoc.accountStatus // Derived state
    };
}
```

## Best Practices

-   **Query Optimization:** Read models can be highly specialized (e.g., Elasticsearch for search, Redis for session data).
-   **Command Simplicity:** Write handlers should be thin wrappers around domain logic, focused on validation and consistency.
-   **Data Synchronization:** Embrace eventual consistency; notify clients when data might be stale.

## References

-   [CQRS Official Site](https://cqrs.nu/)
-   [Event Sourcing Patterns](references/event-sourcing.md)
-   [Data Projection Strategies](references/data-projection.md)

---

**Remember:** CQRS is a pattern for managing complexity where reads and writes have different performance/consistency requirements. (Cluster: Architecture)
