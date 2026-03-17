---
name: python-code-quality
description: "Review Python code for maintainability, security, and performance. Master SOLID principles, catch anti-patterns, and provide constructive feedback. Use when reviewing pull requests, performing code audits, or refactoring Python code. Cluster: Python Development (MERGED)"
---

# Python Code Quality & Review

Ensure high-quality, maintainable, and idiomatic Python code. This skill combines the "How" of code reviews with the "What" of Python-specific anti-patterns and principles.

## When to Use This Skill

- Reviewing Python pull requests
- Performing security and performance audits
- Refactoring legacy Python codebases
- Establishing coding standards and best practices
- Mentoring on Pythonic idioms

## Core Principles

1.  **SOLID Adherence**: SRP, OCP, LSP, ISP, DIP.
2.  **KISS (Keep It Simple, Stupid)**: Favor readability over "clever" one-liners.
3.  **DRY (Don't Repeat Yourself)**: Abstract repeated logic into reusable components.
4.  **Composition Over Inheritance**: Prefer simple objects and interfaces.

## Python Anti-Patterns Checklist

Before approving or finishing code, verify:

- [ ] **Infrastructure**: Centralized timeout/retry logic? No secrets in code?
- [ ] **Architecture**: Repository pattern for I/O? DTOs used for API responses?
- [ ] **Error Handling**: No bare `except:`? Partial failures handled in batches?
- [ ] **Resource Management**: Context managers (`with`) used for all files/connections?
- [ ] **Type Safety**: Public APIs fully annotated? Collections have type parameters?
- [ ] **Performance**: No blocking calls in async code? Efficient DB queries?

See [references/anti-patterns.md](references/anti-patterns.md) for detailed code examples of what to avoid.

## Review Workflow

1.  **Phase 1: Context**: Understand the "Why" behind the changes.
2.  **Phase 2: Logic & Security**: Check for bugs, race conditions, and vulnerabilities.
3.  **Phase 3: idiomatic Python**: Ensure PEP 8 compliance and use of Pythonic features (e.g., list comprehensions, f-strings).
4.  **Phase 4: Feedback**: Provide specific, actionable, and educational comments.

## Effective Feedback Patterns

-   **Labels**: Use `[blocking]`, `[important]`, or `[nit]`.
-   **Questions**: "Have you considered X?" instead of "Do Y."
-   **Context**: Explain *why* a change is requested, not just *what* to change.

## References

- [Python Anti-Patterns Guide](references/anti-patterns.md)
- [SOLID Principles for Python](references/solid.md)
- [Code Review Process & Workflow](references/review-process.md)
- [Modern Python Feedback Templates](references/feedback-templates.md)

---

**Remember:** A code review is a teaching tool, not a gate. Focus on long-term maintainability.
