---
name: skill-auditor
description: Use when auditing skill quality, reviewing skills for improvements, or ensuring skills follow best practices. Evaluates skills against comprehensive quality criteria including structure, discoverability, effectiveness, and technical implementation.
---

# Skill Auditor

Comprehensive quality auditing and improvement recommendations for AI agent skills.

## Overview

This skill provides systematic evaluation of agent skills against established best practices from Anthropic, the Claude Code community, and real-world testing results.

**Core principle:** Skills that follow proven patterns are more discoverable, more effective under pressure, and easier to maintain.

## When to Use

Use this skill when:
- Reviewing a skill before deployment
- Auditing existing skills for quality issues
- Planning skill improvements
- Creating skill creation/review workflows

Don't use for:
- Writing new skills from scratch (use skill-creator instead)
- Testing skills with subagents (use testing-skills-with-subagents)

## Quality Criteria Summary

Skills are evaluated across six dimensions. See [references/quality-criteria.md](references/quality-criteria.md) for full details:

1. **Structure & Organization** - Progressive disclosure, file organization, frontmatter
2. **Discoverability** - Description field patterns (CRITICAL)
3. **Content Quality** - Conciseness, consistency, degrees of freedom
4. **Effectiveness Under Pressure** - For discipline-enforcing skills
5. **Workflows & Feedback Loops** - Multi-step processes, verification
6. **Technical Implementation** - Scripts, error handling, dependencies

## Audit Process

### Quick Assessment Checklist

Run through each dimension:
- [ ] Structure & Organization
- [ ] Discoverability
- [ ] Content Quality
- [ ] Effectiveness Under Pressure (if discipline skill)
- [ ] Workflows & Feedback Loops
- [ ] Technical Implementation

### Issue Prioritization

| Priority | Description |
|---------|-------------|
| **Critical** | Blocks skill effectiveness (e.g., broken triggers) |
| **High** | Significant impact (e.g., missing workflows) |
| **Medium** | Polish (e.g., token efficiency) |
| **Low** | Nice-to-have (e.g., wording) |

### Report Structure

See [references/audit-template.md](references/audit-template.md) for the standard template.

## Common Anti-Patterns

See [references/anti-patterns.md](references/anti-patterns.md) for detailed examples of:
- Description anti-patterns
- Content anti-patterns
- Structure anti-patterns

## Testing Requirements

For discipline-enforcing skills, see [references/testing-requirements.md](references/testing-requirements.md):
- Pressure scenario testing
- Evaluation-driven development
- Meta-testing approaches

## References

- [Quality Criteria Details](references/quality-criteria.md) - Full criteria breakdown
- [Audit Template](references/audit-template.md) - Report template
- [Anti-Patterns](references/anti-patterns.md) - Common mistakes to avoid
- [Testing Requirements](references/testing-requirements.md) - Discipline skill testing

---

**Remember:** Evidence over assumptions. Always test skill changes before deploying.
