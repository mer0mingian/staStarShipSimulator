import os
import re

test_dir = "tests"
files = [f for f in os.listdir(test_dir) if f.endswith(".py") and f != "conftest.py"]

for filename in files:
    filepath = os.path.join(test_dir, filename)
    with open(filepath, "r") as f:
        content = f.read()

    # 1. Add pytest import if missing but used
    if "@pytest.mark.asyncio" in content and "import pytest" not in content:
        content = "import pytest\n" + content

    # 2. Add async to functions calling await (including fixtures)
    lines = content.splitlines()
    new_lines = []
    for line in lines:
        if (
            line.strip().startswith("def ") and "await " in content
        ):  # Crude but let's see
            # Better: check if function body contains await
            pass
        new_lines.append(line)

    # Let's use a more targeted replacement for fixtures that use session
    content = re.sub(
        r"def ([a-zA-Z0-9_]+)\((.*test_session.*)\):", r"async def \1(\2):", content
    )

    # Ensure test functions are async (already done by previous script, but double checking)
    content = re.sub(r"def test_", "async def test_", content)
    # Fix any double asyncs
    content = content.replace("async async def", "async def")

    with open(filepath, "w") as f:
        f.write(content)

print(f"Updated test files again.")
