---
name: debugging-strategies
description: Master systematic debugging techniques and root cause analysis. Apply the scientific method to efficiently track down bugs across any codebase. Use when investigating bugs, performance issues, or unexpected behavior.
---

# Systematic Debugging Strategies

Transform debugging from frustrating guesswork into systematic problem-solving with a methodical approach and the scientific method.

## When to Use This Skill

- Tracking down elusive bugs or regressions
- Investigating performance issues or memory growth
- Understanding complex behavior in unfamiliar codebases
- Debugging production incidents

## The Scientific Method (Core Process)

1.  **Observe**: What is the actual behavior? Collect error messages, logs, and stack traces.
2.  **Reproduce**: Create a minimal, consistent case that triggers the issue. **Can't fix what you can't reproduce.**
3.  **Hypothesize**: What could cause this? Formulate a theory based on observations.
4.  **Experiment**: Test your theory. Change **one thing at a time**.
5.  **Analyze**: Did the experiment prove or disprove the hypothesis?
6.  **Verify**: Once fixed, confirm it works in the target environment and passes all tests.

## Debugging Mindset: Red Flags

-   "It can't be X" (Check anyway)
-   "I didn't change that" (Check anyway)
-   "It works on my machine" (Find the environmental difference)
-   **Assumption is the enemy of the fix.**

## Advanced Techniques

-   **Binary Search (Isolate)**: Comment out half the logic/components to find the failure point.
-   **Differential Analysis**: Compare working vs. broken state (config, environment, inputs).
-   **Git Bisect**: Use version control to find the exact commit where a bug was introduced.
-   **Rubber Ducking**: Explain the logic out loud to reveal hidden assumptions.

## Language-Specific Tools

This skill focuses on **process**. For specific tools, use the corresponding language skill:

-   **Python**: Use `python-debugging` (pdb, logging, cProfile).
-   **JavaScript/TS**: Use browser DevTools or Node debugger.
-   **Go**: Use Delve (dlv).

## References

- [The Scientific Method for Software](references/scientific-method.md)
- [Reproduction Checklist](references/repro-checklist.md)
- [Root Cause Analysis Patterns](references/rca-patterns.md)

---

**Remember:** A bug is a gap between your mental model and reality. Use the process to close that gap.
