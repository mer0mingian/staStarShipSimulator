---
name: system-design
description: "Diagnose design problems and guide architecture decisions for software projects. This skill should be used when the user asks to 'design the system', 'plan the architecture', 'make technology choices', 'create ADRs', 'define components', or needs help translating requirements into architecture. Keywords: architecture, design, components, ADR, walking skeleton, trade-offs, integration, YAGNI. Cluster: Architecture (MERGE CANDIDATE)"
---

# System Design

Diagnose system design problems in software projects. Help translate validated requirements into architecture decisions, component designs, and interface definitions without over-engineering or missing critical integration points.

## When to Use This Skill

- When requirements are validated and ready for architecture planning
- Making technology or framework choices
- Designing component boundaries and interfaces
- Planning integration points
- Documenting architectural decisions

## Core Principle

**Design emerges from constraints. Every architectural decision is a trade-off against something else. Make trade-offs explicit before they become bugs.**

## Diagnostic States (See references/diagnostics.md)

Focus on preventing common pitfalls:
1.  **SD0: No Requirements Clarity:** (Intervention: Use requirements-analysis, define problem statement).
2.  **SD1: Under-Engineering:** (Intervention: Data flow mapping, error enumeration).
3.  **SD2: Over-Engineering:** (Intervention: YAGNI audit, abstraction check).
4.  **SD3: Missing Integration Points:** (Intervention: Interface-first design, dependency inventory).
5.  **SD4: Risky Decisions Unidentified:** (Intervention: ADRs, reversal cost assessment).
6.  **SD5: No Walking Skeleton:** (Intervention: Define minimal end-to-end path first).
7.  **SD6: Design Validated:** (Outcome: Clear architecture, documented trade-offs).

## Anti-Patterns (See references/anti-patterns.md)

-   **The Architecture Astronaut:** Designing for scale you don't need (Fix: YAGNI audit).
-   **The Implicit Decision:** Architecture by accident (Fix: Use ADRs).
-   **The Big Bang Integration:** Deferring integration until the end (Fix: Walking skeleton first).
-   **The Golden Hammer:** Using familiar tech regardless of fit (Fix: Match tech to problem).
-   **The Premature Optimization:** Designing for performance you don't need (Fix: Measure first).

## Output Artifacts

Persist artifacts to `docs/design/` or dedicated skill reference files:
- Design Context Brief
- Architecture Decision Records (ADRs)
- Component Map
- Walking Skeleton Definition

## References

-   [ADR Template](references/adr-template.md)
-   [YAGNI Principle](references/yagni.md)
-   [Integration Checklist](references/integration-checklist.md)

---

**Remember:** Guide architecture by making explicit trade-offs based on constraints. (Cluster: Architecture)
