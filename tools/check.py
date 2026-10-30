"""Run the project's full check: lint, type-check, tests.

Run it in the project environment (after ``uv sync --extra dev`` once):

    uv run tools/check.py

Every check runs, even after a failure, so one run shows all problems.
The exit code is 0 only if all checks pass.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CHECKS = [
    ("lint", ["ruff", "check", "src", "tests"]),
    ("types", ["mypy", "src", "tests"]),
    ("tests", ["pytest", "-q"]),
]


def main() -> int:
    failed = []
    for name, args in CHECKS:
        print(f"== {name}: {' '.join(args)}", flush=True)
        result = subprocess.run([sys.executable, "-m", *args], cwd=ROOT)
        if result.returncode != 0:
            failed.append(name)
    if failed:
        print(f"== FAILED: {', '.join(failed)}")
        return 1
    print("== all checks passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
