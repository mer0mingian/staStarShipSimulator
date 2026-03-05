# Quality Criteria Details

Comprehensive breakdown of the six quality dimensions for skill auditing.

## 1. Structure & Organization

### Progressive Disclosure

- **SKILL.md under 500 lines** for optimal performance
- Complex content split into reference files
- **References one level deep** (no skill.md → advanced.md → details.md)
- Clear navigation from SKILL.md to supporting files
- Table of contents for files >100 lines

### File Organization

| Directory | Purpose |
|-----------|---------|
| `SKILL.md` | Core instructions with YAML frontmatter |
| `references/` | Documentation loaded as needed |
| `scripts/` | Executable utilities |
| `assets/` | Templates, images, files for output |

**No extraneous files:** README.md, INSTALLATION_GUIDE, CHANGELOG belong in repo root, not skill directories.

### Frontmatter Requirements

```yaml
---
name: skill-name
description: "What it does. Use when [TRIGGERS]."
---
```

- `name`: lowercase letters, numbers, hyphens only (max 64 chars)
- `description`: max 1024 chars, third person, includes triggers

### Common Issues

- ❌ Verbose SKILL.md (>500 lines)
- ❌ Deeply nested references
- ❌ Missing table of contents in long files
- ❌ Extraneous documentation files
- ❌ Invalid frontmatter fields
- ❌ Windows-style paths (use forward slashes)

---

## 2. Discoverability (Critical)

The description is THE critical trigger mechanism. Poor descriptions = skills never activate.

### MUST Follow This Pattern

```yaml
description: "[WHAT it does]. Use when [SPECIFIC TRIGGERS]."
```

### Key Requirements

- **Third person** (injected into system prompt)
- Describes **WHEN to use**, NOT the workflow/process
- Includes **concrete triggers** users might mention
- Uses **keywords** Claude would search for
- Under 500 characters if possible

### Good Examples

```yaml
# ✅ Clear what + specific when
description: "Extract text and tables from PDF files, fill forms, merge documents. Use when working with PDF files or when the user mentions PDFs, forms, or document extraction."

# ✅ Technologies + triggers
description: "Complete browser automation with Playwright. Use when user wants to test websites, automate browser interactions, validate web functionality."
```

### Bad Examples

```yaml
# ❌ Too vague
description: "Helps with documents"

# ❌ No triggers
description: "Extracts data from PDFs"

# ❌ Workflow summary (causes Claude to skip full skill)
description: "Use when executing plans - dispatches subagent per task"

# ❌ First person
description: "I can help you with async tests"
```

### Why Workflow Summaries Are Dangerous

Testing revealed that when descriptions summarize the skill's workflow, Claude follows the description instead of reading the full skill content. This causes critical steps to be skipped.

### Keyword Coverage

Include triggers for:
- **Error messages:** "Hook timed out", "ENOTEMPTY", "race condition"
- **Symptoms:** "flaky", "hanging", "zombie", "pollution"
- **Synonyms:** "timeout/hang/freeze", "cleanup/teardown"
- **Tools:** Commands, library names, file types
- **Violation symptoms:** "before committing", "claim work is complete"

---

## 3. Content Quality

### Conciseness

**Default assumption:** Claude is already very smart.

Only add context Claude doesn't have. Challenge every paragraph:
- "Does this justify its token cost?"
- "Can I assume Claude knows this?"

**Good (50 tokens):**
```markdown
## Extract PDF text

Use pdfplumber:

```python
import pdfplumber
with pdfplumber.open("file.pdf") as pdf:
    text = pdf.pages[0].extract_text()
```
```

**Bad (150 tokens):**
```markdown
## Extract PDF text

PDF files are a common format that contains text and images...
There are many libraries available... pdfplumber is recommended...
First install it using pip...
```

### Consistency

- One term throughout (not "API endpoint"/"URL"/"path")
- Gerund form for names: "processing-pdfs"
- No time-sensitive information

### Degrees of Freedom

Match specificity to task fragility:

| Level | When to Use | Example |
|-------|-------------|---------|
| **High** | Multiple approaches valid | Code reviews, analysis |
| **Medium** | Preferred pattern exists | Templates, workflows |
| **Low** | Consistency critical | Migrations, critical ops |

### Common Issues

- ❌ Over-explaining (Claude knows basics)
- ❌ Inconsistent terminology
- ❌ Time-sensitive instructions
- ❌ Wrong freedom level for task type

---

## 4. Effectiveness Under Pressure

For discipline-enforcing skills (e.g., TDD, debugging workflows).

These skills must resist rationalization. Agents are smart and find loopholes.

### Required Elements

1. **Foundational Principle (early)**
   ```
   **Violating the letter of the rules is violating the spirit of the rules.**
   ```

2. **Explicit Negations**
   ```
   Write code before test? Delete it. Start over.
   
   **No exceptions:**
   - Don't keep it as "reference"
   - Don't "adapt" it while writing tests
   - Don't look at it
   - Delete means delete
   ```

3. **Rationalization Table**
   | Excuse | Reality |
   |--------|---------|
   | "Too simple to test" | Simple code breaks. Test takes 30 seconds. |
   | "I'll test after" | Tests passing immediately prove nothing. |

4. **Red Flags List**
   ```
   ## Red Flags - STOP and Start Over
   - Code before test
   - "I already manually tested it"
   - "Tests after achieve the same purpose"
   - "It's about spirit not ritual"
   
   **All mean: Delete code. Start over.**
   ```

---

## 5. Workflows & Feedback Loops

### Multi-Step Workflows

For complex processes:
1. Provide copy-able checklist
2. Clear sequential steps
3. Verification at each stage
4. Condition-based branching

### Feedback Loops

Pattern: Run validator → fix errors → repeat

Benefits:
- Catches errors early
- Improves output quality
- Prevents downstream issues

### Common Issues

- ❌ Missing checklists for complex workflows
- ❌ No verification steps
- ❌ Missing feedback loops
- ❌ Steps too large (>5 minutes each)

---

## 6. Technical Implementation

### Utility Scripts

Include when:
- Same code rewritten repeatedly
- Deterministic reliability needed
- Complex operations prone to errors

### Script Requirements

- Handle errors explicitly (don't punt to Claude)
- Document configuration parameters
- Clear execution intent ("Run X" vs "See X")
- Use `${CLAUDE_PLUGIN_ROOT}` for paths

### Package Dependencies

- List required packages in SKILL.md
- Verify availability in platform docs

### MCP Tool References

Always use fully qualified names: `ServerName:tool_name`

### Common Issues

- ❌ Scripts that punt errors to Claude
- ❌ "Voodoo constants" (undocumented magic numbers)
- ❌ Assuming packages are installed
- ❌ Windows-style paths
- ❌ No error handling

---

## Quick Reference Card

| Dimension | Key Question |
|----------|--------------|
| Structure | Is SKILL.md <500 lines? Progressive disclosure used? |
| Discoverability | Does description have triggers, not workflow? |
| Content | Is it concise? Consistent? Right freedom level? |
| Pressure | Does it resist rationalization? |
| Workflows | Are there checklists and feedback loops? |
| Technical | Do scripts handle errors? |
