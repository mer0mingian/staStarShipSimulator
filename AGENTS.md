# AGENTS.md

Behavioral guidelines to reduce common LLM coding mistakes. Merge with project-specific instructions as needed.

---

# Core Development Workflow

This project uses a **skill-based workflow** for software development. Understanding when to invoke each skill is critical.

## The Workflow Chain

```
brainstorming → writing-plans → (subagent-driven-development OR executing-plans) → finishing-a-development-branch
                            ↓
                    using-git-worktrees
```

### Phase 1: Exploration (brainstorming)

- **When:** User wants to build something new, fix a bug, or explore a design
- **Skill:** `superpowers:brainstorming`
- **Purpose:** Ask questions, refine requirements, explore alternatives, create design document

### Phase 2: Planning (writing-plans)

- **When:** Design is approved, ready to implement
- **Skill:** `superpowers:writing-plans`
- **Purpose:** Break work into bite-sized tasks (2-5 min each), specify exact file paths and verification steps

### Phase 3: Implementation

- **Option A - Same session:** `superpowers:subagent-driven-development`
  - Use when: Working through tasks sequentially in current session
- **Option B - Parallel:** `superpowers:executing-plans`
  - Use when: Multiple independent tasks can run in parallel

### Phase 4: Cleanup (finishing-a-development-branch)

- **When:** All tasks complete
- **Skill:** `superpowers:finishing-a-development-branch`
- **Purpose:** Verify tests pass, present merge/PR options, cleanup worktree

### Supporting Skills

- **using-git-worktrees:** Creates isolated workspace on new branch (used by writing-plans)
- **python-debugging:** For troubleshooting Python issues using pdb/logging
- **python-verification:** For TDD, pytest, and performance profiling
- **python-code-quality:** For review checklists and enforcing SOLID/anti-patterns

## Skill Invocation Guidelines

**Key principle:** Each skill has a specific trigger. Don't guess - follow the chain.

| Trigger                           | Skill to Use                   |
| --------------------------------- | ------------------------------ |
| "Let's build X", "design Y"       | brainstorming first            |
| "Plan this", "break down"         | writing-plans                  |
| "Implement", "work through tasks" | subagent-driven-development    |
| "Parallel", "batch"               | executing-plans                |
| "Complete", "finish", "merge"     | finishing-a-development-branch |
| "Debug", "why is this broken"     | python-debugging               |
| "Write tests", "TDD"              | python-verification            |
| "Verify fix", "confirm it works"  | python-verification            |
| "Review code", "audit"            | python-code-quality            |

---

## AI Assistant Rules & Project Constraints (CRITICAL)

### Subagent Model Enforcement

**CRITICAL**: The agent framework may default to inheriting the parent agent's model, ignoring the `model` specified in the subagent's definition file. This can lead to incorrect model usage and violate project budget constraints.

To prevent this, you **MUST** explicitly provide the `model` parameter when calling the `Task` tool to specify which model the subagent should use.

**Good Example (Correct):**
```python
task(
    subagent_type="python-dev",
    prompt="Implement the feature.",
    description="...",
    model="opencode/minimax-m2.5-free" # Explicitly sets the model. However, this specific model is only an example 
)
```

**Bad Example (Incorrect):**
```python
task(
    subagent_type="python-dev",
    prompt="Implement the feature.",
    description="..."
    # Missing the model parameter, will likely inherit the wrong model
)
```

- **Model Choice**: ALWAYS use `opencode/minimax-m2.5-free` for all tasks (development, review, debugging) unless instructed otherwise.
- **Minimal Changes**: Keep changes to existing files absolutely minimal! This is a private extension to an open-source project, and compatibility with the upstream branch is paramount.
- **Dependency Management & Testing**:
  - ALWAYS use the `python-environment` skill for dependency management and environment setup.
  - ALWAYS use the `python-verification` skill for running tests and verifying completion.
  - Test commands (MUST use `uv`):
    ```bash
    uv venv
    uv pip install -r requirements.txt -r requirements-dev.txt
    uv run pytest tests/ -v
    uv run pytest --cov=sta tests/
    ```
  - Ensure `.venv` is created and used for requirements.
  - Check `.gitignore` to ensure `.venv` is excluded.
- **Reference Files**: Do NOT read or reference `STA2e_Core Rulebook_DIGITAL_v1.1.txt`. Use `starshiprules.md` and other extracted reference files instead.
- **Document Learnings**: After every significant user interaction, decision, or milestone completion, update `docs/learnings_and_decisions.md` to capture what was learned and what was decided.

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

## Parallel Worktree Workflow (For Future Self)

When working on a feature that requires parallel agent coordination:

1. **Create base feature branch** from `vtt-scope`:

   ```bash
   git checkout -b feature/milestone-task vtt-scope
   ```
2. **Launch agents** with subagent-driven-development, assigning each to its own task. Instruct them to:

   - Create a separate git worktree: `git worktree add -b <task-branch> ../<task-name> feature/milestone-task`
   - Work in that isolated directory
   - Implement, test, commit, and push their branch
   - Report back completion
3. **Merge task branches** back to the base feature branch:

   ```bash
   git merge <task-branch>
   ```

   Resolve conflicts by combining distinct functionality (keep both agents' changes).
4. **Cleanup** worktrees after merge:

   ```bash
   git worktree remove ../<task-name>
   ```
5. **Testing**: Run full test suite in base branch after merges.

### Common Pitfalls & Detection

- **Import errors in tests**: If tests fail with `module 'sta' has no attribute 'web'`, add `import sta.web` before any `mock.patch("sta.web.routes.*")` in `tests/conftest.py`. This ensures the submodule is loaded.
- **Virtualenv missing**: Agents may find `.venv` absent in worktree. They should run `uv venv && uv pip install -r requirements*.txt`.
- **Branch confusion**: Agents may commit to detached HEAD if worktree created incorrectly. Always create a named branch in worktree: `git worktree add -b my-task ../my-task feature/base`.
- **Merge conflicts**: Shared files (e.g., `scenes.py`) will have overlapping changes. Resolve by merging logic, not discarding one side. Look for distinct endpoint functions; keep both.

### Model Override

When invoking an agent, specify model explicitly if needed:

```json
{
  "model": "openrouter/stepfun/step-3.5-flash:free"
}
```

Use this for cost savings or when default model fails.

---

## Documentation Structure

This project uses **progressive disclosure** - essential info first, detailed references on demand.

| Level                  | Files                                                           | When to Use                         |
| ---------------------- | --------------------------------------------------------------- | ----------------------------------- |
| **Start Here**   | `docs/delivery_plan.md`                                       | Understand VTT transition roadmap   |
| **Current Work** | `docs/milestone2_tasks.md`                                    | Execute in-progress milestone tasks |
| **Reference**    | `docs/rules_reference.md`, `docs/objects.md`                | Game rules, data models             |
| **Archive**      | `docs/open_questions.md`, `docs/learnings_and_decisions.md` | Historical context                  |

See `docs/README.md` for full documentation guide.

---

**These guidelines are working if:** fewer unnecessary changes in diffs, fewer rewrites due to overcomplication, and clarifying questions come before implementation rather than after mistakes.
