---
name: python-environment
description: "Configure Python projects, manage dependencies with uv, and package code for distribution. Use when setting up new projects, managing virtual environments, or creating PyPI-ready packages. Cluster: Python Development (MERGED)"
---

# Python Environment & Dependency Management

Master project scaffolding, dependency management using `uv`, and modern Python packaging standards. This skill is the single source of truth for your Python development environment.

## When to Use This Skill

- Starting a new Python project or library
- Managing dependencies, virtual environments, and lockfiles
- Configuring development tools (linting, formatting, type checking)
- Packaging code for distribution (PyPI, TestPyPI)
- Migrating from legacy tools (pip, Poetry, requirements.txt)

## Core Principles

1.  **Use `uv` for everything**: Faster, more reliable, and replaces pip/venv/pip-tools.
2.  **`pyproject.toml` is the manifest**: No `requirements.txt` or `setup.py` unless legacy requirement.
3.  **Strict Virtual Environments**: Always use `uv run` and `uv sync`.
4.  **`src/` layout**: Preferred for all distributable packages.

## Quick Start: Project Scaffolding

```bash
# Initialize a new project
uv init --package myproject
cd myproject

# Add dependencies
uv add requests rich
uv add --group dev pytest ruff ty

# Synchronize environment
uv sync --all-groups
```

## Dependency Management Patterns

| Action | Command |
|--------|---------|
| Add package | `uv add <pkg>` |
| Add dev package | `uv add --group dev <pkg>` |
| Remove package | `uv remove <pkg>` |
| Run in venv | `uv run <cmd>` |
| Update locks | `uv lock --upgrade` |

See [references/uv-commands.md](references/uv-commands.md) for a complete CLI reference.

## Tool Configuration (Modern Stack)

| Tool | Purpose | Replaces |
|------|---------|----------|
| **ruff** | Linting & Formatting | black, flake8, isort |
| **ty** | Type Checking | mypy, pyright |
| **pytest** | Testing | unittest |

See [references/pyproject.md](references/pyproject.md) for standard configuration templates.

## Packaging & Distribution

1.  **Build**: `uv build` (or `python -m build`)
2.  **Publish**: `uv publish` (if available) or `twine upload dist/*`

See [references/packaging.md](references/packaging.md) for details on metadata and PyPI.

## Decision Tree: Project Type

```
What are you building?
│
├─ Single-file script? ──> Use PEP 723 inline metadata
├─ Internal tool? ──────> uv init (non-package)
└─ Reusable library? ───> uv init --package (src/ layout)
```

## References

- [UV CLI Reference](references/uv-commands.md)
- [Project Templates & Scaffolding](references/project-scaffolding.md)
- [pyproject.toml Configuration](references/pyproject.md)
- [Packaging & PyPI Guide](references/packaging.md)
- [Migration Guide (Poetry/Pip)](references/migration-guides.md)

---

**Remember:** One tool (`uv`), one manifest (`pyproject.toml`), one source of truth.
