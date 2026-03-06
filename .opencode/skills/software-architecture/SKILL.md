---
name: software-architecture
description: "---
name: software-architecture
description: "Guide for quality focused software architecture. This skill should be used when users want to write code, design architecture, analyze code, in any case that relates to software development. Focuses on Clean Architecture, DDD, and framework independence. Cluster: Architecture (CHECK)"
---

# Software Architecture Principles

Guidance on designing robust, maintainable, and scalable software architecture using Clean Architecture and Domain-Driven Design (DDD) principles.

## When to Use This Skill

- Designing new microservices or monolithic decomposition
- Auditing existing architecture for structural integrity
- Making framework technology choices (e.g., ORM, messaging)
- Evaluating proposed designs for adherence to separation of concerns

## Core Principles (See references/core-principles.md)

### 1. Decoupling & Dependencies
-   **Dependency Rule**: Dependencies must only point inwards (Entities/Domain $\rightarrow$ Infrastructure/Frameworks). Frameworks and databases should never influence core business logic.
-   **Framework Independence**: Business logic must be usable without the web framework or database layer.

### 2. Domain-Driven Design (DDD)
-   **Ubiquitous Language**: Use domain terms consistently across code, tests, and communication.
-   **Entities & Aggregates**: Define domain concepts clearly.
-   **Bounded Contexts**: Use as the basis for service/module boundaries.

### 3. Clean Architecture Concepts
-   **Entities (Core Domain)**: Business rules that change infrequently.
-   **Use Cases (Application)**: Orchestrate domain logic to fulfill specific application goals.
-   **Interface Adapters**: Translate data between use cases and external agents (e.g., Controllers, Presenters, Gateways).
-   **Frameworks & Drivers (Infrastructure)**: Databases, web frameworks, external APIs.

## Anti-Patterns to Avoid (See references/anti-patterns.md)

-   **NIH (Not Invented Here) Syndrome:** Don't build custom solutions when established, high-quality libraries exist.
-   **Mixing Concerns:** Database queries in controllers, UI logic in domain entities.
-   **Generic Naming:** Avoid vague names like `utils`, `helpers`, `common`. Use domain-specific names.

## Best Practices

-   **Code Quality:** Follow SOLID principles, break down complex functions/files.
-   **Custom Code Justification:** Only write custom code for logic unique to the business domain or security-sensitive paths.

## References

-   [Clean Architecture Diagram & Explanation](references/clean-architecture-diagram.md)
-   [DDD Glossary](references/ddd-glossary.md)
-   [ADR Usage](references/adr-usage.md)

---

**Remember:** Architecture is about managing complexity and ensuring business rules are insulated from infrastructure churn. (Cluster: Architecture)
 Focuses on Clean Architecture, DDD, and framework independence. Cluster: Architecture (CHECK)"
---

# Software Architecture Principles

Guidance on designing robust, maintainable, and scalable software architecture using Clean Architecture and Domain-Driven Design (DDD) principles.

## When to Use This Skill

- Designing new microservices or monolithic decomposition
- Auditing existing architecture for structural integrity
- Making framework technology choices (e.g., ORM, messaging)
- Evaluating proposed designs for adherence to separation of concerns

## Core Principles (See references/core-principles.md)

### 1. Decoupling & Dependencies
-   **Dependency Rule**: Dependencies must only point inwards (Entities/Domain $\rightarrow$ Infrastructure/Frameworks). Frameworks and databases should never influence core business logic.
-   **Framework Independence**: Business logic must be usable without the web framework or database layer.

### 2. Domain-Driven Design (DDD)
-   **Ubiquitous Language**: Use domain terms consistently across code, tests, and communication.
-   **Entities & Aggregates**: Define domain concepts clearly.
-   **Bounded Contexts**: Use as the basis for service/module boundaries.

### 3. Clean Architecture Concepts
-   **Entities (Core Domain)**: Business rules that change infrequently.
-   **Use Cases (Application)**: Orchestrate domain logic to fulfill specific application goals.
-   **Interface Adapters**: Translate data between use cases and external agents (e.g., Controllers, Presenters, Gateways).
-   **Frameworks & Drivers (Infrastructure)**: Databases, web frameworks, external APIs.

## Anti-Patterns to Avoid (See references/anti-patterns.md)

-   **NIH (Not Invented Here) Syndrome:** Don't build custom solutions when established, high-quality libraries exist.
-   **Mixing Concerns:** Database queries in controllers, UI logic in domain entities.
-   **Generic Naming:** Avoid vague names like `utils`, `helpers`, `common`. Use domain-specific names.

## Best Practices

-   **Code Quality:** Follow SOLID principles, break down complex functions/files.
-   **Custom Code Justification:** Only write custom code for logic unique to the business domain or security-sensitive paths.

## References

-   [Clean Architecture Diagram & Explanation](references/clean-architecture-diagram.md)
-   [DDD Glossary](references/ddd-glossary.md)
-   [ADR Usage](references/adr-usage.md)

---

**Remember:** Architecture is about managing complexity and ensuring business rules are insulated from infrastructure churn. (Cluster: Architecture)
