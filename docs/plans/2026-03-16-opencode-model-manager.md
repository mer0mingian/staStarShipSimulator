# OpenCode Model Manager Implementation Plan

> **For Claude:** Use python-dev agent to implement.

**Goal:** Create an interactive Python script to manage OpenCode subagent models, list free models from APIs, sort by benchmark scores, and manage via config.

**Architecture:** Single Python script with minimal dependencies (requests or curl fallback). Interactive CLI using built-in input().

**Tech Stack:** Python 3, requests (optional), JSONC config parsing

---

### Task 1: Create Config File Template

**Files:**
- Create: `opencode/model-settings.jsonc`

**Step 1: Write the config file**

```jsonc
{
  // Providers to include (empty = all)
  "providers": {
    "include": [],
    "exclude": []
  },
  // Model whitelist/blacklist
  "models": {
    "whitelist": [],
    "blacklist": []
  },
  // Default settings
  "defaults": {
    "min_context_window": 200000,
    "preferred_model": ""
  },
  // Subagent model overrides (filled by script)
  "subagent_overrides": {}
}
```

---

### Task 2: Create the Model Manager Script

**Files:**
- Create: `opencode-model-manager.py`

**Step 1: Write the script**

See full implementation below. The script should:
1. Load config from `opencode/model-settings.jsonc`
2. Query OpenRouter API for free models (no auth required for list)
3. Query Groq API for models (requires GROQ_API_KEY env var)
4. Filter by min context window
5. Apply whitelist/blacklist
6. Sort by benchmark scores (hardcoded dict)
7. List available subagents from `.opencode/agents/*.md`
8. Allow user to select subagent and new model
9. Save overrides to config

---

### Task 3: Test the Script

**Step 1: Run with help**

```bash
python opencode-model-manager.py --help
```

Expected: Show usage info

**Step 2: Run list command**

```bash
python opencode-model-manager.py list
```

Expected: List free models sorted by capability

---

## Implementation Notes

- Use `requests` library if available, fall back to `curl` subprocess
- Parse JSONC by stripping `//` and `/* */` comments
- Benchmark scores from LiveCodeBench/SWE-Bench (hardcoded)
- Use input() for interactive selection
