# AGENTS.md

Behavioral guidelines to reduce common LLM coding mistakes. Merge with project-specific instructions as needed.

**Tradeoff:** These guidelines bias toward caution over speed. For trivial tasks, use judgment.

## 1. Think Before Coding

**Don't assume. Don't hide confusion. Surface tradeoffs.**

Before implementing:
- State your assumptions explicitly. If uncertain, ask.
- If multiple interpretations exist, present them - don't pick silently.
- If a simpler approach exists, say so. Push back when warranted.
- If something is unclear, stop. Name what's confusing. Ask.

## 2. Simplicity First

**Minimum code that solves the problem. Nothing speculative.**

- No features beyond what was asked.
- No abstractions for single-use code.
- No "flexibility" or "configurability" that wasn't requested.
- No error handling for impossible scenarios.
- If you write 200 lines and it could be 50, rewrite it.

Ask yourself: "Would a senior engineer say this is overcomplicated?" If yes, simplify.

## 3. Surgical Changes

**Touch only what you must. Clean up only your own mess.**

When editing existing code:
- Don't "improve" adjacent code, comments, or formatting.
- Don't refactor things that aren't broken.
- Match existing style, even if you'd do it differently.
- If you notice unrelated dead code, mention it - don't delete it.

When your changes create orphans:
- Remove imports/variables/functions that YOUR changes made unused.
- Don't remove pre-existing dead code unless asked.

The test: Every changed line should trace directly to the user's request.

## 4. Goal-Driven Execution

**Define success criteria. Loop until verified.**

Transform tasks into verifiable goals:
- "Add validation" → "Write tests for invalid inputs, then make them pass"
- "Fix the bug" → "Write a test that reproduces it, then make it pass"
- "Refactor X" → "Ensure tests pass before and after"

For multi-step tasks, state a brief plan:
```
1. [Step] → verify: [check]
2. [Step] → verify: [check]
3. [Step] → verify: [check]
```

Strong success criteria let you loop independently. Weak criteria ("make it work") require constant clarification.

---

**These guidelines are working if:** fewer unnecessary changes in diffs, fewer rewrites due to overcomplication, and clarifying questions come before implementation rather than after mistakes.

# Code Style Guidelines

Adherence to consistent code style is crucial for readability and maintainability.

### Imports
- **Ordering:** Imports should be grouped and ordered consistently. A common pattern is:
    1. Standard library imports
    2. Third-party library imports
    3. Local application imports
- **Specificity:** Import only what is necessary. Avoid wildcard imports (`import *`).

### Formatting
- **Indentation:** Use spaces for indentation (e.g., 2 or 4 spaces). Tabs are generally discouraged.
- **Line Length:** Maintain a maximum line length (e.g., 80 or 100 characters) to ensure readability.
- **Brace Style:** Follow the brace style of the surrounding code (e.g., opening brace on the same line or new line).
- **Whitespace:** Use whitespace judiciously to improve readability around operators, after commas, and to separate logical blocks of code.

### Types
- **Type Hinting:** Use type hints (e.g., in Python, TypeScript) to specify expected data types for variables, function parameters, and return values. This improves code clarity and enables static analysis.
- **Consistency:** Be consistent with the type definitions used throughout the project.

### Naming Conventions
- **Variables:** Use camelCase for most variables (e.g., `userName`, `totalCount`).
- **Constants:** Use SCREAMING_SNAKE_CASE for constants (e.g., `MAX_RETRIES`, `API_KEY`).
- **Functions/Methods:** Use camelCase or snake_case depending on the language conventions (e.g., `getUserData()`, `calculate_total()`).
- **Classes:** Use PascalCase (also known as UpperCamelCase) for class names (e.g., `UserProfile`, `DatabaseManager`).
- **Clarity:** Choose descriptive names that clearly indicate the purpose of the variable, function, or class. Avoid overly short or ambiguous names.

### Error Handling
- **Be Explicit:** Handle potential errors gracefully. Use try-catch blocks, error codes, or specific error types as appropriate for the language.
- **Informative Messages:** Error messages should be informative, providing enough context to help diagnose the issue.
- **Avoid Silencing Errors:** Do not swallow errors without proper handling or logging.
- **Consistency:** Follow the established error handling patterns used in the existing codebase.

### Comments
- **Purpose:** Use comments to explain the "why" behind complex logic, non-obvious decisions, or workarounds, rather than the "what."
- **Conciseness:** Keep comments concise and to the point.
- **Maintenance:** Ensure comments are kept up-to-date with code changes.

### General Principles
- **Readability:** Prioritize code that is easy to read and understand.
- **Simplicity:** Favor simpler solutions over overly complex ones.
- **Consistency:** Maintain consistency with the existing codebase's style and patterns.
- **DRY (Don't Repeat Yourself):** Avoid redundant code; abstract common logic into reusable functions or classes.
