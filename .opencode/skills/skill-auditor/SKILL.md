---
name: skill-auditor
description: Use when auditing skill quality, reviewing skills for improvements, or ensuring skills follow best practices. Evaluates skills against comprehensive quality criteria including structure, discoverability, effectiveness, and technical implementation.
---

# Skill Auditor

Comprehensive quality auditing and improvement recommendations for AI agent skills.

## Overview

This skill provides systematic evaluation of agent skills against established best practices from Anthropic, the Claude Code community, and real-world testing results. Use it to audit existing skills, identify improvement opportunities, and ensure skills meet professional standards.

**Core principle:** Skills that follow proven patterns are more discoverable, more effective under pressure, and easier to maintain.

## When to Use

Use this skill when:
- Reviewing a skill before deployment
- Auditing existing skills for quality issues
- Planning skill improvements
- Creating skill creation/review workflows
- Evaluating community skills
- Teaching skill creation best practices

Don't use for:
- Writing new skills from scratch (use skill-creator instead)
- Testing skills with subagents (use testing-skills-with-subagents)
- General code review (use code review skills)

## Quality Criteria Framework

Skills are evaluated across six dimensions:

### 1. Structure & Organization

**Progressive Disclosure:**
- SKILL.md under 500 lines for optimal performance
- Complex content split into reference files
- References one level deep (no nested references)
- Clear navigation from SKILL.md to supporting files
- Table of contents for files >100 lines

**File Organization:**
- `SKILL.md` (required) - Core instructions with YAML frontmatter
- `references/` - Documentation loaded as needed
- `scripts/` - Executable utilities
- `assets/` - Templates, images, files for output
- No extraneous files (README, INSTALLATION_GUIDE, CHANGELOG)

**Frontmatter Requirements:**
- `name`: lowercase letters, numbers, hyphens only (no parentheses/special chars)
- `description`: max 1024 chars, third person, includes triggers
- No other fields allowed in YAML frontmatter

**Common Issues:**
- ❌ Verbose SKILL.md (>500 lines)
- ❌ Deeply nested references (skill.md → advanced.md → details.md)
- ❌ Missing table of contents in long reference files
- ❌ Extraneous documentation (README.md, QUICK_REFERENCE.md)
- ❌ Invalid frontmatter fields
- ❌ Windows-style paths (use forward slashes)

### 2. Discoverability (Critical)

**Description Field Quality:**

The description is THE critical trigger mechanism. Poor descriptions = skills never activate.

**MUST follow this pattern:**
```yaml
description: "[WHAT it does]. Use when [SPECIFIC TRIGGERS including symptoms, keywords, tools]."
```

**Key requirements:**
- Written in third person (injected into system prompt)
- Describes WHEN to use, NOT the workflow/process
- Includes concrete triggers users might mention
- Uses keywords Claude would search for
- Under 500 characters if possible

**Good examples:**
```yaml
# ✅ Excellent - clear what + specific when
description: "Extract text and tables from PDF files, fill forms, merge documents. Use when working with PDF files or when the user mentions PDFs, forms, or document extraction."

# ✅ Excellent - technologies + triggers
description: "Complete browser automation with Playwright. Use when user wants to test websites, automate browser interactions, validate web functionality, or perform any browser-based testing."
```

**Bad examples:**
```yaml
# ❌ Too vague
description: "Helps with documents"

# ❌ No triggers
description: "Extracts data from PDFs"

# ❌ Workflow summary (creates shortcut Claude takes instead of reading full skill)
description: "Use when executing plans - dispatches subagent per task with code review between tasks"

# ❌ First person
description: "I can help you with async tests when they're flaky"
```

**Why workflow summaries are dangerous:**
Testing revealed that when descriptions summarize the skill's workflow, Claude follows the description instead of reading the full skill content. This causes Claude to skip critical steps defined in the flowcharts and instructions.

**Keyword Coverage:**
- Error messages: "Hook timed out", "ENOTEMPTY", "race condition"
- Symptoms: "flaky", "hanging", "zombie", "pollution"
- Synonyms: "timeout/hang/freeze", "cleanup/teardown/afterEach"
- Tools: Actual commands, library names, file types
- Violation symptoms: "when about to claim work is complete", "before committing"

**Common Issues:**
- ❌ Description summarizes workflow/process
- ❌ Missing triggers/keywords
- ❌ Too abstract ("For async testing")
- ❌ First person ("I can help...")
- ❌ Language-specific when skill isn't ("tests use setTimeout")

### 3. Content Quality

**Conciseness:**
- Default assumption: Claude is already very smart
- Only add context Claude doesn't already have
- Challenge every paragraph: "Does this justify its token cost?"
- Prefer concise examples over verbose explanations

**Good (50 tokens):**
````markdown
## Extract PDF text

Use pdfplumber for text extraction:

```python
import pdfplumber
with pdfplumber.open("file.pdf") as pdf:
    text = pdf.pages[0].extract_text()
```
````

**Bad (150 tokens):**
```markdown
## Extract PDF text

PDF (Portable Document Format) files are a common file format...
There are many libraries available... pdfplumber is recommended...
First install it using pip. Then you can use...
```

**Consistency:**
- One term throughout (not "API endpoint"/"URL"/"API route"/"path")
- Consistent naming conventions (gerund form recommended: "processing-pdfs")
- No time-sensitive information (use "Old patterns" sections)

**Appropriate Degrees of Freedom:**

Match specificity to task fragility:

**High freedom** (text-based instructions):
- Multiple approaches valid
- Decisions depend on context
- Use for: code reviews, analysis, flexible workflows

**Medium freedom** (pseudocode/scripts with parameters):
- Preferred pattern exists
- Some variation acceptable
- Use for: templates, configurable workflows

**Low freedom** (specific scripts, few parameters):
- Operations fragile/error-prone
- Consistency critical
- Use for: database migrations, critical operations

**Common Issues:**
- ❌ Over-explaining (Claude knows what PDFs are)
- ❌ Inconsistent terminology
- ❌ Time-sensitive instructions
- ❌ Wrong degree of freedom for task type
- ❌ Multiple language implementations (choose one excellent example)
- ❌ Generic labels in flowcharts (step1, helper2)

### 4. Effectiveness Under Pressure

**For Discipline-Enforcing Skills:**

These skills must resist rationalization. Agents are smart and find loopholes under pressure.

**Required Elements:**

1. **Foundational Principle (early)**
   ```markdown
   **Violating the letter of the rules is violating the spirit of the rules.**
   ```

2. **Explicit Negations**
   ```markdown
   Write code before test? Delete it. Start over.
   
   **No exceptions:**
   - Don't keep it as "reference"
   - Don't "adapt" it while writing tests
   - Don't look at it
   - Delete means delete
   ```

3. **Rationalization Table**
   ```markdown
   | Excuse | Reality |
   |--------|---------|
   | "Too simple to test" | Simple code breaks. Test takes 30 seconds. |
   | "I'll test after" | Tests passing immediately prove nothing. |
   | "Tests after achieve same goals" | Tests-after = "what does this do?" Tests-first = "what should this do?" |
   ```

4. **Red Flags List**
   ```markdown
   ## Red Flags - STOP and Start Over
   
   - Code before test
   - "I already manually tested it"
   - "Tests after achieve the same purpose"
   - "It's about spirit not ritual"
   - "This is different because..."
   
   **All of these mean: Delete code. Start over with TDD.**
   ```

**Testing Requirements:**

Discipline skills MUST be tested with pressure scenarios combining 3+ pressures:
- Time (deadline, emergency)
- Sunk cost (hours of work)
- Authority (senior says skip it)
- Economic (job, promotion)
- Exhaustion (end of day)
- Social (seeming dogmatic)

**Research Foundation:**
Meincke et al. (2025) tested 7 persuasion principles with N=28,000 AI conversations:
- Authority language ("YOU MUST") increases compliance 33% → 72%
- Commitment (announce usage, track progress) reinforces adherence
- Scarcity (time-bound requirements) prevents procrastination

**Common Issues:**
- ❌ No rationalization table
- ❌ Missing red flags list
- ❌ Vague rules ("don't cheat" vs "don't keep as reference")
- ❌ No foundational principle
- ❌ Untested against pressure scenarios
- ❌ Missing explicit negations

### 5. Workflows & Feedback Loops

**Multi-Step Workflows:**

For complex processes:
1. Provide copy-able checklist
2. Clear sequential steps
3. Verification at each stage
4. Condition-based branching when needed

**Good Example:**
````markdown
## PDF form filling workflow

Copy this checklist:

```
Task Progress:
- [ ] Step 1: Analyze the form (run analyze_form.py)
- [ ] Step 2: Create field mapping (edit fields.json)
- [ ] Step 3: Validate mapping (run validate_fields.py)
- [ ] Step 4: Fill the form (run fill_form.py)
- [ ] Step 5: Verify output (run verify_output.py)
```

**Step 1: Analyze the form**
Run: `python scripts/analyze_form.py input.pdf`
This extracts form fields and locations, saving to `fields.json`.

**Step 2: Create field mapping**
Edit `fields.json` to add values for each field.

**Step 3: Validate mapping**
Run: `python scripts/validate_fields.py fields.json`
Fix validation errors before continuing.

If verification fails at Step 5, return to Step 2.
````

**Feedback Loops:**

Pattern: Run validator → fix errors → repeat

Benefits:
- Catches errors early
- Improves output quality
- Prevents downstream issues

**Common Issues:**
- ❌ Missing checklists for complex workflows
- ❌ No verification steps
- ❌ Missing feedback loops
- ❌ Unclear conditional branching
- ❌ Steps too large (>5 minutes each)

### 6. Technical Implementation

**Utility Scripts:**

When to include:
- Same code rewritten repeatedly
- Deterministic reliability needed
- Complex operations prone to errors

Benefits:
- More reliable than generated code
- Saves tokens (no code in context)
- Ensures consistency

**Requirements:**
- Handle errors explicitly (don't punt to Claude)
- Document configuration parameters
- Clear execution intent ("Run X" vs "See X")
- Use `${CLAUDE_PLUGIN_ROOT}` for paths

**Good Example:**
```python
def process_file(path):
    """Process a file, creating if it doesn't exist."""
    try:
        with open(path) as f:
            return f.read()
    except FileNotFoundError:
        # Create file with default content instead of failing
        print(f"File {path} not found, creating default")
        with open(path, 'w') as f:
            f.write('')
        return ''
    except PermissionError:
        # Provide alternative instead of failing
        print(f"Cannot access {path}, using default")
        return ''
```

**Bad Example:**
```python
def process_file(path):
    # Just fail and let Claude figure it out
    return open(path).read()
```

**Package Dependencies:**
- List required packages in SKILL.md
- Verify availability in platform docs
- Note platform-specific limitations

**MCP Tool References:**
- Always use fully qualified names: `ServerName:tool_name`
- Without prefix, tool may not be found

**Common Issues:**
- ❌ Scripts that punt errors to Claude
- ❌ "Voodoo constants" (undocumented magic numbers)
- ❌ Assuming packages are installed
- ❌ Windows-style paths
- ❌ No error handling
- ❌ Missing `${CLAUDE_PLUGIN_ROOT}` in hooks

## Audit Process

### 1. Initial Assessment

Run through each quality dimension:
- [ ] Structure & Organization
- [ ] Discoverability
- [ ] Content Quality
- [ ] Effectiveness Under Pressure (if discipline skill)
- [ ] Workflows & Feedback Loops
- [ ] Technical Implementation

### 2. Issue Identification

For each dimension, identify:
- **Critical issues** (blocks skill effectiveness)
- **High-priority improvements** (significant impact)
- **Medium-priority improvements** (polish)
- **Low-priority improvements** (nice-to-have)

### 3. Prioritized Recommendations

Structure recommendations by impact:

**Critical (must fix):**
- Description issues that prevent discovery
- Missing rationalization defenses (discipline skills)
- Structural problems (invalid frontmatter, Windows paths)

**High Priority:**
- Content organization (progressive disclosure)
- Missing workflows/checklists
- Script error handling

**Medium Priority:**
- Token efficiency improvements
- Consistency issues
- Documentation polish

**Low Priority:**
- Minor wording improvements
- Additional examples
- Cosmetic issues

### 4. Specific Action Items

For each issue, provide:
- **What:** Clear description of the problem
- **Why:** Impact on skill effectiveness
- **How:** Specific fix with examples
- **Where:** Exact location (file, line number if applicable)

## Audit Report Template

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

[Same format]

## Low-Priority Improvements

[Same format]

## Overall Assessment

- Structure: [Pass/Needs Work/Fail]
- Discoverability: [Pass/Needs Work/Fail]
- Content Quality: [Pass/Needs Work/Fail]
- Effectiveness: [Pass/Needs Work/Fail/N/A]
- Workflows: [Pass/Needs Work/N/A]
- Technical: [Pass/Needs Work/N/A]

## Next Steps

1. [Prioritized action items]
2. [...]
```

## Common Anti-Patterns

### Description Anti-Patterns

❌ **Workflow Summary**
```yaml
description: "Use when executing plans - dispatches subagent per task with code review between tasks"
```
✅ **Just Triggers**
```yaml
description: "Use when executing implementation plans with independent tasks in the current session"
```

❌ **Too Abstract**
```yaml
description: "For async testing"
```
✅ **Concrete Triggers**
```yaml
description: "Use when tests have race conditions, timing dependencies, or pass/fail inconsistently"
```

### Content Anti-Patterns

❌ **Over-Explaining**
```markdown
PDF files are a common format that contains text and images...
```
✅ **Concise**
```markdown
Use pdfplumber for text extraction:
```

❌ **Code in Flowcharts**
```dot
step1 [label="import fs"];
step2 [label="read file"];
```
✅ **Semantic Labels**
```dot
validate [label="Validate Input"];
process [label="Process Data"];
```

### Structure Anti-Patterns

❌ **Deeply Nested References**
```markdown
# SKILL.md
See [advanced.md](advanced.md)...

# advanced.md
See [details.md](details.md)...
```
✅ **One Level Deep**
```markdown
# SKILL.md
**Advanced features:** See [advanced.md](advanced.md)
**API reference:** See [reference.md](reference.md)
```

## Evaluation-Driven Improvement

**Before extensive changes:**

1. **Identify gaps:** Run skill on representative tasks, document failures
2. **Create evaluations:** Build 3+ scenarios testing those gaps
3. **Establish baseline:** Measure performance without changes
4. **Write minimal fixes:** Address specific failures
5. **Iterate:** Execute evaluations, compare, refine

**Don't guess** at improvements. Test, measure, improve based on evidence.

## Testing Requirements

### For Discipline Skills

**Mandatory testing:**
- Baseline test (RED): Run scenario WITHOUT skill, document failures
- Pressure test (GREEN): Run scenario WITH skill, verify compliance
- Loophole closing (REFACTOR): Find new rationalizations, add counters
- Re-verification: Test again, ensure still compliant

**Pressure scenarios must combine 3+ pressures:**
- Time (deadline approaching)
- Sunk cost (hours of work)
- Authority (senior says skip)
- Economic (job/promotion)
- Exhaustion (end of day)
- Social (seeming dogmatic)

**Example scenario:**
```markdown
You spent 4 hours implementing a feature. It works perfectly.
You manually tested all edge cases. It's 6pm, dinner at 6:30pm.
Code review tomorrow at 9am. You just realized you didn't write tests.

Options:
A) Delete code, start over with TDD tomorrow
B) Commit now, write tests tomorrow
C) Write tests now (30 min delay)

Choose A, B, or C.
```

**Success criteria:**
- Agent chooses correct option under maximum pressure
- Agent cites skill sections as justification
- Agent acknowledges temptation but follows rule
- Meta-testing reveals "skill was clear, I should follow it"

### For All Skills

**Evaluation structure:**
```json
{
  "skills": ["skill-name"],
  "query": "Task description",
  "files": ["test-files/input.txt"],
  "expected_behavior": [
    "Specific success criterion 1",
    "Specific success criterion 2"
  ]
}
```

**Test with all target models:**
- Claude Haiku (does skill provide enough guidance?)
- Claude Sonnet (is skill clear and efficient?)
- Claude Opus (does skill avoid over-explaining?)

## Real-World Examples

### Example 1: TDD Skill Bulletproofing

**Initial Test (Failed):**
- Scenario: 200 lines done, forgot TDD, exhausted, dinner plans
- Agent chose: C (write tests after)
- Rationalization: "Tests after achieve same goals"

**Iteration 1:**
- Added section: "Why Order Matters"
- Re-tested: Agent STILL chose C
- New rationalization: "Spirit not letter"

**Iteration 2:**
- Added: "Violating letter is violating spirit"
- Re-tested: Agent chose A (delete it)
- Cited: New principle directly
- Meta-test: "Skill was clear, I should follow it"

**Bulletproof achieved after 2 iterations.**

### Example 2: Description Fixes

**Before:**
```yaml
description: "Use when executing plans - dispatches subagent per task with code review between tasks"
```

**Problem:** Claude followed description (1 review) instead of flowchart (2 reviews)

**After:**
```yaml
description: "Use when executing implementation plans with independent tasks in the current session"
```

**Result:** Claude correctly read flowchart, performed 2-stage review

## References

**Official Documentation:**
- [Anthropic Skills Best Practices](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices)
- [Claude Code Skills Documentation](https://code.claude.com/docs/en/skills)

**Research:**
- Meincke, L., et al. (2025). "Call Me A Jerk: Persuading AI to Comply with Objectionable Requests"
- Cialdini, R. B. (2021). "Influence: The Psychology of Persuasion"

**Community Resources:**
- [obra/superpowers](https://github.com/obra/superpowers) - Battle-tested skills library
- [Claude Skills Marketplace](https://skillsmp.com) - 2,277+ community skills
- [Claude Code Skills Marketplace](https://claude-plugins.dev/skills) - 7,453+ skills

## Bottom Line

**Quality skills share these traits:**
- Discoverable (description = triggers, not workflow)
- Concise (token-efficient, assumes smart audience)
- Organized (progressive disclosure, clear structure)
- Tested (pressure scenarios for discipline skills, evaluations for all)
- Bulletproof (explicit negations, rationalization tables)
- Practical (workflows, checklists, feedback loops)

**The audit process mirrors TDD:**
- RED: Identify failures
- GREEN: Fix specific issues
- REFACTOR: Polish and improve
- VERIFY: Test and measure

**Evidence over assumptions. Always.**
