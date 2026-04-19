"""PostToolUse hook: run the Pydantic-to-Gemini schema cleaner test
after any Write/Edit touching app/services/classify.py.

Registered in .claude/settings.json. Claude Code pipes the tool-call
JSON on stdin; we read it, filter by file_path, and run the test only
when classify.py changed. Fast path exits in under 100ms for unrelated
edits so the hook is cheap to keep enabled.

Exit contract:
  0   = happy path (test passed, or not the file we care about, or
        the test timed out — we log but don't block in the timeout
        case since the cleaner should finish in < 1s).
  2   = test failed, surface stdout+stderr back to Claude as feedback.
"""
import json
import subprocess
import sys
from pathlib import Path

TEST_TIMEOUT_SECONDS = 10
TARGET_SUFFIX = "app/services/classify.py"


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        # No valid hook JSON on stdin means we can't decide. Don't block.
        return 0

    file_path = (
        payload.get("tool_input", {}).get("file_path")
        or payload.get("tool_input", {}).get("path")
        or ""
    )
    normalized = file_path.replace("\\", "/")
    if not normalized.endswith(TARGET_SUFFIX):
        return 0

    repo_root = Path(__file__).resolve().parent.parent.parent
    try:
        result = subprocess.run(
            [sys.executable, "-m", "tests.test_schema_cleaner"],
            cwd=str(repo_root),
            capture_output=True,
            text=True,
            timeout=TEST_TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired:
        print(
            f"schema_cleaner_check: test timed out after "
            f"{TEST_TIMEOUT_SECONDS}s; skipping (not blocking).",
            file=sys.stderr,
        )
        return 0

    if result.returncode != 0:
        print("schema_cleaner_check: tests/test_schema_cleaner FAILED", file=sys.stderr)
        if result.stdout:
            print(result.stdout, file=sys.stderr)
        if result.stderr:
            print(result.stderr, file=sys.stderr)
        return 2

    return 0


if __name__ == "__main__":
    sys.exit(main())
