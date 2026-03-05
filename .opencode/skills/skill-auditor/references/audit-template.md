# Audit Report Template

Standard template for skill audit reports.

## Template

```markdown
# Skill Audit: [Skill Name]

## Executive Summary

[2-3 sentences on overall quality and main findings]

## Critical Issues

### 1. [Issue Name]
- **Impact:** [Why this matters]
- **Current:** [What's wrong]
- **Recommended:** [Specific fix]
- **Location:** [File:line or section]

## High-Priority Improvements

### 1. [Issue Name]
[Same format]

## Medium-Priority Improvements

### 1. [Issue Name]
[Same format]

## Low-Priority Improvements

### 1. [Issue Name]
[Same format]

## Overall Assessment

| Dimension | Status | Notes |
|-----------|--------|-------|
| Structure | Pass/Needs Work/Fail | |
| Discoverability | Pass/Needs Work/Fail | |
| Content Quality | Pass/Needs Work/Fail | |
| Effectiveness | Pass/Needs Work/Fail/N/A | |
| Workflows | Pass/Needs Work/N/A | |
| Technical | Pass/Needs Work/N/A | |

## Next Steps

1. [Prioritized action items]
2. [...]
```

## Example

```markdown
# Skill Audit: my-coding-skill

## Executive Summary

The skill has a solid workflow but suffers from discoverability issues. The description lacks specific triggers, and the SKILL.md exceeds recommended length. Structure is otherwise sound.

## Critical Issues

### 1. Description Lacks Triggers
- **Impact:** Skill may not activate for relevant queries
- **Current:** `description: "Helps with coding tasks"`
- **Recommended:** `description: "Assists with Python debugging. Use when user mentions errors, exceptions, tracebacks, or debugging sessions."`
- **Location:** SKILL.md:2

### 2. SKILL.md Too Long (520 lines)
- **Impact:** Token inefficiency, potential partial reads
- **Current:** 520 lines in single file
- **Recommended:** Split into references/ directory with progressive disclosure
- **Location:** SKILL.md (entire file)

## High-Priority Improvements

### 1. Missing Feedback Loop
- **Impact:** No verification step after execution
- **Current:** Skill executes without validation
- **Recommended:** Add checklist with verification step before claiming success

## Overall Assessment

| Dimension | Status | Notes |
|----------|--------|-------|
| Structure | Needs Work | Needs progressive disclosure |
| Discoverability | Needs Work | Description too vague |
| Content Quality | Pass | Concise, consistent |
| Effectiveness | Pass | Good rationalization |
| Workflows | Needs Work | Missing verification |
| Technical | Pass | Good script patterns |
```

## Usage

When conducting an audit:

1. **Initial Assessment:** Run through each dimension checklist
2. **Issue Identification:** Categorize each issue by priority
3. **Recommendations:** Provide specific, actionable fixes
4. **Assessment:** Give overall status for each dimension

Remember: Be specific. "The description is bad" is not actionable. "The description lacks specific triggers" is actionable.
