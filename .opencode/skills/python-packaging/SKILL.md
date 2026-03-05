---
name: python-packaging
description: "Create distributable Python packages with proper project structure, setup.py/pyproject.toml, and publishing to PyPI. Use when packaging Python libraries, creating CLI tools, or distributing Python code. Covers setuptools, wheel, and twine. Cluster: Python Development (SPLIT)"
---

# Python Packaging Best Practices

Create robust and distributable Python packages for seamless sharing and installation.

## When to Use This Skill

- Packaging a Python library for PyPI
- Creating a command-line interface (CLI) tool
- Distributing Python code for internal use
- Managing dependencies and build configurations
- Understanding package structure and metadata

## Core Concepts & Templates (See references/original_skill.md)

- **Modern Standard**: Use `pyproject.toml` exclusively for configuration.
- **Build Tool**: Use the `build` package (`python -m build`).
- **Publishing**: Use `twine` to upload to PyPI/TestPyPI.

### Key Files
-   **`pyproject.toml`**: Primary configuration (Metadata, Dependencies, Build System).
-   **`src/`**: Contains package source code (recommended layout).
-   **`README.md`**: Essential documentation.

### Workflow Summary
1.  Structure project (`src/`, `pyproject.toml`).
2.  Configure metadata and dependencies in `pyproject.toml`.
3.  Write code and tests.
4.  Build: `python -m build`.
5.  Publish: `twine upload dist/*`.

## Best Practices

-   **Version Pinning**: Pin dependencies in `pyproject.toml`.
-   **Semantic Versioning**: Follow SemVer for releases.
-   **Clear README**: Explain installation, usage, and contribution.
-   **Include LICENSE**: Make usage rights clear.
-   **Test on multiple Python versions**: Use CI for this.

## References

-   [Original Content/Full Details](references/original_skill.md)
-   [pyproject.toml Specification](references/pyproject-spec.md)
-   [Twine Documentation](references/twine-docs.md)

---

**Remember:** Packaging is about making your code easy for others to install and use. Follow standards! (Cluster: Python Development)
