# Python Packaging & Distribution

Create robust and distributable Python packages for sharing and installation.

## Core Concepts

- **Modern Standard**: Use `pyproject.toml` exclusively for configuration.
- **Build Tool**: Use the `build` package (`python -m build`) or `uv build`.
- **Publishing**: Use `twine` to upload to PyPI/TestPyPI or `uv publish`.

### Key Files
- **`pyproject.toml`**: Primary configuration (Metadata, Dependencies, Build System).
- **`src/`**: Contains package source code (recommended layout).
- **`README.md`**: Essential documentation.

## Workflow

1. **Structure project**: Ensure `src/` layout and `pyproject.toml` exist.
2. **Configure metadata**: Add project name, version, and dependencies to `pyproject.toml`.
3. **Build**: 
   ```bash
   uv build
   ```
4. **Publish**:
   ```bash
   uv publish
   # OR
   twine upload dist/*
   ```

## Best Practices

- **Version Pinning**: Pin dependencies for consistency.
- **Semantic Versioning**: Follow SemVer (Major.Minor.Patch).
- **Clear README**: Explain installation and basic usage.
- **Include LICENSE**: Choose a standard license (e.g., MIT, Apache).

## Templates

### pyproject.toml (Build System)
```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "my-package"
version = "0.1.0"
dependencies = [
    "requests>=2.25.0",
]
```
