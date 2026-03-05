---
name: solid
description: "Enforce SOLID principles for robust, maintainable, and flexible code. Use when writing, refactoring, designing architecture, or reviewing code. Explicitly checks for SRP, OCP, LSP, ISP, and DIP adherence. Cluster: Code Quality (CHECK)"
---

# SOLID Principles for Professional Software Engineering

Enforce the SOLID principles to ensure high-quality, maintainable, and flexible software design.

## When to Use This Skill

**ALWAYS use this skill when:**
- Writing ANY new code (features, fixes, utilities)
- Refactoring existing code
- Planning or designing architecture
- Reviewing code quality
- Making design decisions

## Core Principles (See references/solid-principles.md)

Every class, every module, every function must adhere to these principles:

| Principle | Full Name | Question to Ask |
|-----------|-----------|-----------------|
| **S**RP | Single Responsibility Principle | "Does this have ONE reason to change?" |
| **O**CP | Open/Closed Principle | "Can I extend without modifying the source?" |
| **L**SP | Liskov Substitution Principle | "Can subtypes safely replace base types?" |
| **I**SP | Interface Segregation Principle | "Are clients forced to depend on unused methods?" |
| **D**IP | Dependency Inversion Principle | "Do high-level modules depend on abstractions (interfaces)?" |

## Process & Practices (See references/process.md)
-   **TDD First**: Design happens during REFACTORING, not initial coding.
-   **Clean Code**: Prioritize consistency, specificity, and clarity in naming.
-   **Value Objects**: MANDATORY wrapping of primitives (IDs, Money, Email) to prevent error-prone use of raw types.

## References

-   [SOLID Principles Explained](references/solid-principles.md)
-   [Value Object Implementation](references/value-objects.md)
-   [Design Patterns Overview](references/design-patterns.md)

---

**Remember:** SOLID is the foundation for clean, flexible code that makes future changes cheap. (Cluster: Code Quality)
