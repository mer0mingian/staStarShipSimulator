---
name: excalidraw-diagrams
description: Creates Excalidraw diagrams programmatically. Use when the user wants flowcharts, architecture diagrams, system designs, or any visual diagram instead of ASCII art. Outputs .excalidraw files that can be opened directly in Excalidraw or VS Code with the Excalidraw extension.
---

# Excalidraw Diagram Generator

Generates professional Excalidraw diagrams programmatically using Python.

**Output:** `.excalidraw` JSON files that can be:
- Opened at https://excalidraw.com (drag & drop)
- Edited in VS Code with Excalidraw extension
- Exported to SVG/PNG for embedding

## Quick Start

```python
#!/usr/bin/env python3
import sys, os
sys.path.insert(0, "~/.claude/skills/excalidraw-diagrams/scripts")
from excalidraw_generator import Diagram, Flowchart, ArchitectureDiagram

# Create diagram
d = Diagram()
box1 = d.box(100, 100, "Step 1", color="blue")
box2 = d.box(300, 100, "Step 2", color="green")
d.arrow_between(box1, box2, "next")
d.save("my_diagram.excalidraw")
```

Run: `python3 your_script.py`

## Diagram Classes

| Class | Purpose | Key Methods |
|-------|---------|-------------|
| `Diagram` | Base class | `box()`, `text_box()`, `arrow_between()`, `line_between()` |
| `Flowchart` | Auto-positioning flowcharts | `start()`, `end()`, `process()`, `decision()`, `connect()` |
| `ArchitectureDiagram` | System architecture | `component()`, `database()`, `service()`, `user()`, `connect()` |

## Common Patterns

See [references/patterns.md](references/patterns.md) for:
- Flowchart examples
- Architecture diagrams
- API call flows
- Database schemas

## Testing

```bash
# Unit tests
python tests/test_generator.py

# API integration test
ANTHROPIC_API_KEY=sk-... python tests/test_api_skill.py
```

## References

- [Pattern Gallery](references/patterns.md) - Common diagram patterns
- [API Reference](references/api.md) - Full class documentation
- [Troubleshooting](references/troubleshooting.md) - Common issues

---

**Note:** No external dependencies - uses Python standard library only.
