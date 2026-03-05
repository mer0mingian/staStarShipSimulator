---
name: uv-package-manager
description: "Master the uv package manager for fast Python dependency management, virtual environments, and modern Python project workflows. Use when setting up Python projects, managing dependencies, or optimizing Python development workflows with uv. Covers installation, dependency management, version pinning, and CI/CD integration. Detailed templates for common workflows included."
---

# uv Package Manager Mastery (Cluster: Python Development)

Master `uv`, the blazing-fast dependency manager written in Rust, for Python projects.

## When to Use This Skill

- Setting up new Python projects quickly
- Managing Python dependencies faster than pip
- Creating and managing isolated virtual environments
- Speeding up CI/CD pipelines
- Working with lockfiles for reproducible builds

## Core Concepts & Patterns (See references/original_skill.md)

- **Speed**: 10-100x faster than traditional tools.
- **CLI**: Focus on `uv venv`, `uv add`, `uv sync`, `uv lock`, and `uv run`.
- **Virtual Environments**: Strongly favor `uv venv` and `uv run` over manual activation.
- **Lockfiles**: Commit `uv.lock` for CI reproducibility.

## Best Practices

-   **Commit lockfiles** (`uv.lock`).
-   **Pin Python version** (use `.python-version`).
-   **Use `uv run`**: Avoid manual venv activation.
-   **Keep uv updated**: Fast-moving project.

## References

-   [Original Content/Full Details](references/original_skill.md)
-   [Official documentation](references/official-docs.md)
-   [Migration guides](references/migration-guides.md)

---

**Remember:** `uv` is designed for speed. Use its commands directly to leverage Rust performance benefits. (Cluster: Python Development)
