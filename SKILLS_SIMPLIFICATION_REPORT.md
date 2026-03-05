# Skills Simplification Report

**Based on Quality Criteria from `skill-auditor`**

---

## Executive Summary

Your skills collection has **significant structural issues** that violate multiple skill-auditor principles:

| Issue | Count | Impact |
|-------|-------|--------|
| Complete duplicates (.opencode + .agents) | 19 skills | 2x maintenance burden |
| Oversized SKILL.md (>500 lines) | 7 skills | Token inefficiency |
| Potential overlaps | 8+ skills | Confusion, bloat |
| Tiny/empty skills | 2 skills | Useless without content |

**RE-EVALUATED Recommendation:** After analyzing dependencies, some original recommendations must be **changed**. See Section 0 below.

---

## SECTION 0: Dependency Analysis (CRITICAL)

Before making changes, I analyzed how skills are used:

### Current Skill Chain (WORKING)
```
brainstorming → writing-plans → (subagent-driven-development OR executing-plans) → finishing-a-development-branch
                            ↓
                    using-git-worktrees (referenced)
```

### Agent References:
| Agent | Skills Allowed |
|-------|----------------|
| python-dev.md | subagent-driven-development, systematic-debugging, test-driven-development, verification-before-completion |
| orchestrator.md | brainstorming |
| architect.md | writing-plans |
| code-reviewer.md | requesting-code-review, receiving-code-review, differential-review, comprehensive-review/* |
| code-auditor.md | requesting-code-review, receiving-code-review, differential-review |

### Command References:
| Command | Invokes Skill |
|---------|----------------|
| brainstorm.md | superpowers:brainstorming |
| write-plan.md | superpowers:writing-plans |
| execute-plan.md | superpowers:executing-plans |

### Cross-Skill References:
| From Skill | References |
|------------|------------|
| writing-plans | executing-plans, subagent-driven-development |
| subagent-driven-development | writing-plans, finishing-a-development-branch, requesting-code-review, test-driven-development |
| executing-plans | finishing-a-development-branch, writing-plans |
| finishing-a-development-branch | subagent-driven-development, executing-plans |
| brainstorming | writing-plans, system-design |
| systematic-debugging | test-driven-development, verification-before-completion |
| api-documentation-generator | test-driven-development, systematic-debugging |

---

## RE-EVALUATED Changes

### ❌ DO NOT Delete: `.agents/skills/`

**Original recommendation:** Delete entire `.agents/skills/` directory.

**RE-EVALUATION:** After analyzing dependencies:
- Skills in `.agents/skills/` include: `modern-python` (NOT in .opencode!)
- The `.agents/skills/modern-python` is the **primary** location
- Deleting it would break functionality

**New Recommendation:**
- Compare each skill individually
- Keep `.agents/skills/modern-python` (it's unique there)
- Investigate if other skills have unique content in .agents before deleting

### ❌ DO NOT Merge: Code Review Cluster

**Original recommendation:** Merge requesting-code-review, receiving-code-review, differential-review, comprehensive-review into one skill.

**RE-EVALUATION:** After analyzing dependencies:
- Different agents reference different skills (code-reviewer vs code-auditor)
- Each skill has distinct purpose and is referenced by different triggers
- Merging would require updating multiple agents

**New Recommendation:**
- KEEP as separate skills
- They are already working well with different agents

### ✅ CONFIRMED: Development Workflow Chain

**Original recommendation:** Keep as-is with clear descriptions.

**RE-EVALUATION:** This is the **core workflow** and works correctly:
- Used by orchestrator, architect, python-dev agents
- Referenced by commands
- Clear chaining between skills

**New Recommendation:**
- NO CHANGES NEEDED to workflow chain

### ✅ CONFIRMED: Oversized Skills Still Need Fixing

The following still need progressive disclosure:
1. skill-auditor (671 lines)
2. writing-skills (655 lines) 
3. excalidraw-diagrams (715 lines)
4. embedding-strategies (608 lines)

---

## Critical Issues (After Re-evaluation)

---

## Critical Issues (After Re-evaluation)

### 1. Oversized Skills (>500 lines) - STILL VALID

**Problem:** 7 skills exceed the 500-line recommendation from skill-auditor.

| Skill | Lines | Issue | Dependencies Affected |
|-------|-------|-------|----------------------|
| skill-auditor | 671 | Self-reference - needs fix | None (meta-skill) |
| writing-skills | 655 | Needs progressive disclosure | Referenced by skill-creator |
| excalidraw-diagrams | 715 | Needs split | Independent |
| embedding-strategies | 608 | Needs split | Independent |
| api-documentation-generator | 484 | Close - monitor | References test-driven-development, systematic-debugging |
| qdrant-vector-search | 493 | Close - monitor | Independent |
| docker-expert | 408 | Acceptable | Independent |

**Impact on dependencies:** Minimal. These are standalone skills with few cross-references.

**Recommendation for skill-auditor:**
```
skill-auditor/
├── SKILL.md              # ~150 lines: Overview, When to Use, Audit Process
├── references/
│   ├── quality-criteria.md   # Sections 1-6 from current SKILL.md
│   ├── common-anti-patterns.md # Anti-patterns section
│   ├── audit-template.md      # Report template
│   └── testing-requirements.md # Testing sections
└── scripts/
    └── audit_checklist.py     # Optional helper
```

---

### 2. Duplicate Skills - REQUIRES CAREFUL HANDLING

**Status:** After analysis, some duplicates are intentional:

| Skill | .opencode | .agents | Status | Action |
|-------|-----------|---------|--------|--------|
| modern-python | ❌ | ✅ | **UNIQUE in .agents** | KEEP |
| notebooklm | ❌ | ✅ | **UNIQUE in .agents** | KEEP |
| template-skill | ✅ | ✅ | Both empty | DELETE .agents/ |
| software-architecture | ✅ | ✅ | Duplicate | DELETE .agents/ |
| system-design | ✅ | ✅ | Duplicate | DELETE .agents/ |
| solid | ✅ | ✅ | Duplicate | DELETE .agents/ |
| skill-creator | ✅ | ✅ | Duplicate | DELETE .agents/ |
| differential-review | ✅ | ✅ | Duplicate | DELETE .agents/ |
| databases | ✅ | ✅ | Duplicate | DELETE .agents/ |
| docker-expert | ✅ | ✅ | Duplicate | DELETE .agents/ |
| cloudflare | ✅ | ✅ | Duplicate | DELETE .agents/ |
| mcp-builder | ✅ | ✅ | Duplicate | DELETE .agents/ |
| hugging-face-cli | ✅ | ✅ | Duplicate | DELETE .agents/ |
| senior-ml-engineer | ✅ | ✅ | Duplicate | DELETE .agents/ |
| qdrant-vector-search | ✅ | ✅ | Duplicate | DELETE .agents/ |
| embedding-strategies | ✅ | ✅ | Duplicate | DELETE .agents/ |
| building-mcp-server-on-cloudflare | ✅ | ✅ | Duplicate | DELETE .agents/ |
| api-documentation-generator | ✅ | ✅ | Duplicate | DELETE .agents/ |
| excalidraw | ✅ | ✅ | Duplicate | DELETE .agents/ |
| excalidraw-diagrams | ✅ | ✅ | Duplicate | DELETE .agents/ |
| google-workspace | ✅ | ✅ | Duplicate | DELETE .agents/ |

**Total unique in .agents: 2** (modern-python, notebooklm)

---

### 3. Overlapping Skills - RE-EVALUATED

### 3a. Code Review Cluster - KEEP SEPARATE

**Status:** DO NOT MERGE. Already working correctly.

| Skill | Referenced By | Status |
|-------|---------------|--------|
| requesting-code-review | code-reviewer agent, subagent-driven-development | ✅ Working |
| receiving-code-review | code-reviewer agent | ✅ Working |
| differential-review | code-reviewer agent, code-auditor agent | ✅ Working |
| comprehensive-review/* | code-reviewer agent, tdd-workflows | ✅ Working |

**Recommendation:** No changes needed.

### 3b. Development Workflow Chain - KEEP SEPARATE

These are already working well as separate skills with clear triggers:

| Skill | Trigger | Referenced By |
|-------|---------|---------------|
| brainstorming | "plan this feature", "design X" | orchestrator agent, commands |
| writing-plans | After brainstorming | architect agent, commands |
| executing-plans | "implement this plan" | commands |
| subagent-driven-development | "work through tasks" | python-dev agent |
| finishing-a-development-branch | "complete work", "merge" | subagent-driven-development |

**Recommendation:** No changes needed. This is the core workflow and works correctly.

### 3c. Python Development Cluster

| Skill | Location | Status |
|-------|----------|--------|
| modern-python | .agents/skills/ ONLY | ✅ Unique |
| python-pro | .opencode/skills/python-dev-agents/ | Independent |
| fastapi-pro | .opencode/skills/python-dev-agents/ | Independent |
| django-pro | .opencode/skills/python-dev-agents/ | Independent |
| databases | Both locations | Delete .agents/ copy |

**Recommendation:** 
- Keep modern-python in .agents/skills/
- Delete duplicates from .agents/
- python-dev-agents are independent (not referenced yet)

---

## Dependencies That Need Updates

Based on the re-evaluation, here are the actual changes needed:

### Phase 1: Execute Safe Deletions

```bash
# UNIQUE in .agents/ - MUST KEEP:
# .agents/skills/modern-python/ (NOT in .opencode!)
# .agents/skills/notebooklm/ (NOT in .opencode!)

# Execute deletions:
rm -rf .agents/skills/template-skill/
rm -rf .agents/skills/software-architecture/
rm -rf .agents/skills/system-design/
rm -rf .agents/skills/solid/
rm -rf .agents/skills/skill-creator/
rm -rf .agents/skills/differential-review/
rm -rf .agents/skills/databases/
rm -rf .agents/skills/docker-expert/
rm -rf .agents/skills/cloudflare/
rm -rf .agents/skills/mcp-builder/
rm -rf .agents/skills/hugging-face-cli/
rm -rf .agents/skills/senior-ml-engineer/
rm -rf .agents/skills/qdrant-vector-search/
rm -rf .agents/skills/embedding-strategies/
rm -rf .agents/skills/building-mcp-server-on-cloudflare/
rm -rf .agents/skills/api-documentation-generator/
rm -rf .agents/skills/excalidraw/
rm -rf .agents/skills/excalidraw-diagrams/
rm -rf .agents/skills/google-workspace/
```

**Savings:** ~3800 lines (keeping modern-python + notebooklm)

---

## Revised Consolidation Plan

### ✅ Phase 1: COMPLETE - Duplicate Removal & Directory Restructuring

**Actions taken:**
1. Deleted 19 duplicate skills from `.agents/skills/`
2. Moved unique skills (modern-python, notebooklm) to `.opencode/skills/`
3. Removed empty `.agents/` directory
4. Created `.opencode/backup-agents/` for plugin agents (62 agent collections)

**New Structure:**
```
.opencode/
├── agents/           # Active agents (7 files)
├── commands/        # Active commands (3 files)
├── skills/          # All skills including modern-python, notebooklm (37 dirs)
├── plugins/         # Plugin directories (now without agents)
└── backup-agents/  # Archived agents from plugins (62 dirs)
```

**Lines saved:** ~3800

---

### ✅ Phase 2: Progressive Disclosure - COMPLETE for skill-auditor

**Completed:**
- skill-auditor: 671 lines → 150 lines (SKILL.md) + references/

**New structure:**
```
skill-auditor/
├── SKILL.md (150 lines)
└── references/
    ├── quality-criteria.md
    ├── audit-template.md
    └── anti-patterns.md
```

---

### Phase 3: Reduce Remaining Large Skills

Remaining skills to split:
1. writing-skills (655 lines)
2. excalidraw-diagrams (715 lines)
3. embedding-strategies (608 lines)

---

### Summary of Changes

| Change | Status |
|--------|--------|
| Phase 1: Duplicate removal | ✅ Complete |
| Phase 2: skill-auditor split | ✅ Complete |
| Directory restructuring | ✅ Complete |
| Remaining large skills | ⏳ Pending |
rm -rf .agents/skills/solid/
rm -rf .agents/skills/skill-creator/
rm -rf .agents/skills/differential-review/
rm -rf .agents/skills/databases/
rm -rf .agents/skills/docker-expert/
rm -rf .agents/skills/cloudflare/
rm -rf .agents/skills/mcp-builder/
rm -rf .agents/skills/hugging-face-cli/
rm -rf .agents/skills/senior-ml-engineer/
rm -rf .agents/skills/qdrant-vector-search/
rm -rf .agents/skills/embedding-strategies/
rm -rf .agents/skills/building-mcp-server-on-cloudflare/
rm -rf .agents/skills/api-documentation-generator/
rm -rf .agents/skills/excalidraw/
rm -rf .agents/skills/excalidraw-diagrams/
rm -rf .agents/skills/google-workspace/
rm -rf .agents/skills/databases/

# KEEP:
# .agents/skills/modern-python/ (unique)
```

**Savings:** ~3800 lines (keeping modern-python)

---

### Phase 2: Reduce Large Skills (Week 2)

Priority order:
1. **skill-auditor** (671 lines) - Self-reference, easiest to fix
2. **writing-skills** (655 lines) - References skill-creator, needs care
3. **excalidraw-diagrams** (715 lines) - Independent
4. **embedding-strategies** (608 lines) - Independent

Method: Apply progressive disclosure pattern

---

### Phase 3: No Merges Needed

After re-evaluation, NO skill merges are needed:
- Code review cluster: Already working ✅
- Development workflow: Already working ✅
- Python tools: Already separate ✅

---

## Original Sections (For Reference)

---

# PART 2: Plugins Analysis

## Commands in Plugins

**Total: 74 command files** across 35+ plugin categories.

### OpenCode Command Quality Criteria

Based on https://opencode.ai/docs/commands/:

**Good Command Structure:**
```yaml
---
description: "[What it does]"
agent: [optional agent]
model: [optional model]
---

[Prompt content with $ARGUMENTS, @file references, !`command` output]
```

**Key requirements:**
- **description**: Brief, shown in TUI (max ~100 chars)
- **agent**: Optional, triggers specific agent
- **template**: The actual prompt
- **Arguments**: Use `$ARGUMENTS` or `$1`, `$2`, etc.
- **File references**: Use `@filename` to include files
- **Shell output**: Use `!`command`` to inject command output

### Commands Analysis

| Plugin Category | Command Count | Quality Issues |
|----------------|--------------|----------------|
| conductor | 7 | Multiple commands, good structure |
| tdd-workflows | 4 | Well-structured |
| ui-design | 4 | Good |
| error-debugging/error-diagnostics | 5 | Some duplicates |
| code-refactoring | 3 | Good |
| comprehensive-review | 2 | Good |
| git-pr-workflows | 3 | Good |

**Recommendation for Commands:**

Commands in plugins are specialized and should **stay in plugins** since they are:
- Domain-specific (business-analyst, ml-pipeline, security-audit)
- Not part of core development workflow
- Not referenced by main agents

**Do NOT move to .opencode/commands/** unless they are:
- Used by active agents
- Part of core workflow

---

## Skills in Plugins

**Total: 100+ skill files** across many plugin categories.

### Clusters Identified

| Cluster | Plugin Categories | Skill Count |
|---------|------------------|-------------|
| **UI/Design** | ui-design | ~15 skills |
| **Python Dev** | python-development | ~15 skills |
| **LLM/ML** | llm-application-dev, machine-learning-ops | ~12 skills |
| **Security** | security-scanning, security-compliance | ~8 skills |
| **Shell/Systems** | shell-scripting, systems-programming | ~5 skills |
| **Business** | startup-business-analyst | ~5 skills |
| **Observability** | observability-monitoring | ~4 skills |
| **Payment** | payment-processing | ~3 skills |

### Overlap Analysis

| Skill Area | Overlaps With | Assessment |
|------------|--------------|------------|
| python-development skills | modern-python (main skill) | HIGH - should reference main skill |
| llm-application-dev/skills/embedding-strategies | main embedding-strategies | DUPLICATE - remove from plugin |
| shell-scripting skills | bash-pro (backup-agents) | OK - specialized |
| ui-design skills | - | OK - domain specific |

---

## Recommendations

### 1. Commands - KEEP IN PLUGINS

Commands are domain-specific and should stay in their plugin folders. They are:
- Not part of the core workflow (brainstorm → plan → execute → finish)
- Used by specific use cases (security-audit, ml-pipeline)
- Well-structured following OpenCode conventions

### 2. Skills - Apply Progressive Disclosure

Many skills in plugins are **well-structured** but could benefit from:
- Progressive disclosure for larger skills
- References to main skills (e.g., python-development should use modern-python)

### 3. Duplicate Skills to Remove

| Duplicate | Original Location | Action |
|----------|------------------|--------|
| llm-application-dev/skills/embedding-strategies | .opencode/skills/embedding-strategies | DELETE from plugin |
| python-development skills | modern-python (main) | Keep - specialized focus |

### 4. Generic Agent Approach

**Key insight:** Instead of 62+ specific agents, use **generic skills** with focus parameters:

**Current (bloated):**
- 147 archived agents in backup-agents/
- Each agent has specific permissions

**Recommended (lean):**
- 7 active agents with generic skill access
- Agents pass "focus" parameter to skills
- Skills adapt behavior based on focus

Example:
```
# Instead of 10 specific agents:
# - python-django-agent, python-fastapi-agent, python-flask-agent

# Use 1 generic python-dev agent that:
# - Calls python-pro with focus=django|fastapi|flask
# - Calls modern-python with task=setup|testing|deployment
```

---

## Summary: Recommended Actions

| Action | Priority | Impact |
|--------|----------|--------|
| Keep commands in plugins | ✅ Done | N/A |
| Remove duplicate embedding-strategies from plugin | High | -1 duplicate |
| Apply progressive disclosure to large plugin skills | Medium | Token savings |
| Consolidate backup-agents into generic skills | Low | Future consideration |

---

*Analysis based on OpenCode command conventions and skill-auditor quality criteria*
