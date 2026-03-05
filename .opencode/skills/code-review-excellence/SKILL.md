---
name: code-review-excellence
description: "Master effective code review practices to provide constructive feedback, catch bugs early, and foster knowledge sharing while maintaining team morale. Use when reviewing pull requests, establishing review standards, or mentoring developers. Focuses on actionable feedback, team collaboration, and process improvement. Cluster: Code Quality (SPLIT)"
---

# Code Review Excellence

Transform code reviews from gatekeeping to knowledge sharing through constructive feedback, systematic analysis, and collaborative improvement.

## When to Use This Skill

- Reviewing pull requests and code changes
- Establishing code review standards for teams
- Mentoring junior developers through reviews
- Conducting architecture reviews
- Creating review checklists and guidelines

## Core Principles (See references/core-principles.md)

1.  **Review Mindset**: Goals are catching bugs, sharing knowledge, enforcing standards, not nitpicking formatting.
2.  **Effective Feedback**: Must be specific, actionable, educational, and prioritized.
3.  **Review Scope**: Focus on logic, security, performance, tests, and architecture; automate style checks.

## Review Process (See references/review-process.md)

-   **Phase 1: Context Gathering**: Understand PR scope, CI status, and business need.
-   **Phase 2: High-Level Review**: Architecture, file organization, testing strategy.
-   **Phase 3: Line-by-Line Review**: Logic, security, performance, maintainability.
-   **Phase 4: Summary & Decision**: Clear verdict (Approve/Comment/Request Changes).

## Review Techniques (See references/techniques.md)

-   **Checklist Method**: Use structured lists for Security, Performance, Testing.
-   **Question Approach**: Guide the author's thinking instead of dictating solutions.
-   **Severity Differentiation**: Use labels like `[blocking]`, `[important]`, `[nit]`.

## Language-Specific Patterns

-   **Python**: Watch for mutable defaults, broad exception catching.
-   **TypeScript/JS**: Watch for `any` types, unhandled async errors.

## Best Practices & Pitfalls

-   **Best Practices**: Review promptly, limit PR size, automate formatting.
-   **Pitfalls**: Perfectionism, Scope Creep, Delayed Reviews, Rubber Stamping.

## References

-   [Core Principles](references/core-principles.md)
-   [Review Process Steps](references/review-process.md)
-   [Review Techniques](references/techniques.md)
-   [Templates and Assets](references/templates-assets.md)

---

**Remember:** Evidence over assumptions. Always test skill changes before deploying. (Cluster: Code Quality)
