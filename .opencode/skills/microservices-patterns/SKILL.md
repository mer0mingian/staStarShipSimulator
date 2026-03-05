---
name: microservices-patterns
description: "Design microservices architectures with service boundaries, event-driven communication, and resilience patterns. Use when building distributed systems, decomposing monoliths, or implementing microservices. Cluster: Architecture (SPLIT)"
---

# Microservices Architecture Patterns

Designing robust, scalable, and maintainable distributed systems using well-established microservice patterns.

## When to Use This Skill

- Decomposing a monolith into independent services
- Defining clear service boundaries (Bounded Contexts)
- Implementing inter-service communication strategies
- Ensuring resilience against service failure
- Designing for eventual consistency

## Core Concepts

### 1. Service Boundaries (Domain-Driven Design)
-   Services should align with **Bounded Contexts** from the business domain.
-   Each service owns its own data store (Database per Service pattern).
-   Minimize chatty communication between services.

### 2. Communication Styles
-   **Synchronous (Request/Response):** Good for real-time queries/commands (e.g., HTTP/REST, gRPC). Introduces tight coupling and latency.
-   **Asynchronous (Event-Driven):** Good for broadcasting state changes and decoupling. Requires a message broker (Kafka, RabbitMQ, SNS/SQS).

### 3. Resilience Patterns
Microservices must anticipate and handle failure gracefully.
-   **Circuit Breaker:** Stops overwhelming a failing service (e.g., Hystrix/Resilience4j equivalent).
-   **Retry Logic:** Implement exponential backoff for transient failures.
-   **Bulkhead:** Isolate resources so failure in one area doesn't crash the whole system.

## Key Patterns

### Pattern 1: Database per Service (Cluster: Architecture)
Each microservice must manage its own private database schema. Other services access the data only through that service's API or published events.

**Anti-Pattern to Avoid:** Direct access to another service's database.

### Pattern 2: Saga Pattern for Distributed Transactions (Cluster: Architecture)

Use Sagas (orchestration or choreography) to manage transactions that span multiple services, ensuring atomicity through compensating actions. (See `saga-orchestration` skill).

### Pattern 3: API Gateway (Cluster: Architecture)

A single entry point for external clients that handles routing, authentication, rate limiting, and protocol translation before traffic reaches internal services.

## Best Practices

-   **Smart Endpoints, Dumb Pipes:** Logic belongs in services; communication infrastructure should be simple (e.g., an HTTP server or a message queue).
-   **Observability:** Implement distributed tracing (Jaeger/Tempo) to follow requests across service hops.
-   **Deployment:** Use independent deployment pipelines for each service (CI/CD per service).

## References

-   [Martin Fowler's Microservices](https://martinfowler.com/articles/microservices.html)
-   [Patterns.dev](https://patterns.dev/architecture/microservices)
-   [Resilience Patterns](references/resilience-patterns.md)

---

**Remember:** Microservices trade complexity for autonomy and scale. Manage coupling carefully. (Cluster: Architecture)
