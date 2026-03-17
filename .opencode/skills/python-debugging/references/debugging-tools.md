# Python Debugging Tools

Comprehensive guide to Python-specific debugging tools and techniques.

## 1. In-Code Breakpoints

### Modern Python (3.7+)
Use the built-in `breakpoint()` function. It calls `sys.breakpointhook()`, which defaults to `pdb.set_trace()`.

```python
def complex_function(data):
    # ... code ...
    breakpoint()  # Execution pauses here
    # ... more code ...
```

### Manual pdb
For older versions or specific control:
```python
import pdb; pdb.set_trace()
```

## 2. PDB Cheat Sheet

| Command | Action |
|---------|--------|
| `n` (next) | Execute next line |
| `s` (step) | Step into function |
| `c` (continue) | Continue until next breakpoint |
| `l` (list) | Show current code context |
| `p <expr>` | Print expression value |
| `q` (quit) | Exit debugger |

## 3. Post-Mortem Debugging
Debug the state *after* an exception has occurred.

```python
import pdb

try:
    risky_operation()
except Exception:
    pdb.post_mortem()
```

## 4. Logging for Discovery
When breakpoints are impractical (e.g., race conditions, production).

```python
import logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def fetch_user(user_id):
    logger.debug(f"Attempting to fetch user: {user_id}")
    # ...
```

## 5. Performance & CPU Profiling

### cProfile (Standard Library)
Best for aggregate timing.
```bash
python -m cProfile -s cumulative my_script.py
```

### line_profiler
Best for line-by-line analysis.
```python
@profile
def slow_function():
    # ...
```
Run with: `kernprof -l -v my_script.py`
