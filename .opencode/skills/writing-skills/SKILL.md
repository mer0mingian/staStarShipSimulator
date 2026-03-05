---
name: writing-skills
description: Use when creating new skills, editing existing skills, or verifying skills work before deployment
---

# Writing Skills

**Writing skills IS Test-Driven Development applied to process documentation.**

**REQUIRED:** Understand `superpowers:test-driven-development` first (RED-GREEN-REFACTOR cycle).

## Core Principle

If you didn't watch an agent fail without the skill, you don't know if the skill teaches the right thing.

## TDD Mapping

| TDD Concept | Skill Creation |
|-------------|----------------|
| Test case | Pressure scenario with subagent |
| Production code | Skill document (SKILL.md) |
| Test fails (RED) | Agent violates rule without skill |
| Test passes (GREEN) | Agent complies with skill |
| Refactor | Close loopholes while maintaining compliance |

## When to Create

**Create when:**
- Technique wasn't intuitively obvious to you
- You'd reference this again across projects
- Pattern applies broadly
- Others would benefit

**Don't create for:**
- One-off solutions
- Standard practices well-documented elsewhere
- Project-specific conventions (use CLAUDE.md)

## Directory Structure

```
skill-name/
├── SKILL.md           # Main reference (required)
├── references/        # Heavy reference (100+ lines)
├── scripts/          # Reusable tools
└── templates/        # Templates
```

## SKILL.md Requirements

**Frontmatter (only two fields):**
```yaml
---
name: skill-name
description: "[WHAT it does]. Use when [SPECIFIC TRIGGERS]."
---
```

**Content:**
- Keep under 500 lines
- Use progressive disclosure (references/ for detailed content)
- Third-person description
- Include concrete triggers

## References

- [Testing with Subagents](references/testing-skills-with-subagents.md) - Pressure scenarios, RED-GREEN-REFACTOR
- [Anthropic Best Practices](references/anthropic-best-practices.md) - Official guidance
- [Persuasion Principles](references/persuasion-principles.md) - Influencing agent behavior
- [CLAUDE_MD Testing](references/CLAUDE_MD_TESTING.md) - Testing patterns

---

**Remember:** Write test first (baseline scenario), watch it fail, then write the skill.
