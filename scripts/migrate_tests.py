import os
import re

test_dir = "tests"
files = [f for f in os.listdir(test_dir) if f.endswith(".py") and f != "conftest.py"]

for filename in files:
    filepath = os.path.join(test_dir, filename)
    with open(filepath, "r") as f:
        content = f.read()

    # 1. Add async to test functions
    content = re.sub(r"def test_", "async def test_", content)

    # 2. Add @pytest.mark.asyncio before async tests
    # Avoid double markers if already present
    lines = content.splitlines()
    new_lines = []
    for line in lines:
        if line.strip().startswith("async def test_"):
            if not (new_lines and new_lines[-1].strip() == "@pytest.mark.asyncio"):
                indent = line[: line.find("async def")]
                new_lines.append(f"{indent}@pytest.mark.asyncio")
        new_lines.append(line)
    content = "\n".join(new_lines)

    # 3. Remove content_type="application/json"
    content = content.replace('content_type="application/json",', "")
    content = content.replace("content_type='application/json',", "")

    # 4. response.data -> response.json() or response.content
    # Use re to replace json.loads(response.data) with response.json()
    content = re.sub(r"json\.loads\(response\.data\)", "response.json()", content)
    content = re.sub(r"json\.loads\(response\.content\)", "response.json()", content)

    # 5. Add awaits to session methods
    content = re.sub(
        r"test_session\.commit\(\)", "await test_session.commit()", content
    )
    content = re.sub(r"test_session\.flush\(\)", "await test_session.flush()", content)
    content = re.sub(r"test_session\.refresh\(", "await test_session.refresh(", content)
    content = re.sub(r"test_session\.delete\(", "await test_session.delete(", content)

    # 6. client.set_cookie -> client.cookies.set
    content = content.replace("client.set_cookie", "client.cookies.set")

    # 7. data -> content or json()
    content = content.replace("response.data", "response.content")

    with open(filepath, "w") as f:
        f.write(content)

print(f"Updated {len(files)} test files.")
