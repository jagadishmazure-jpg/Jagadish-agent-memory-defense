"""Print the real test total by collecting (not running with -qq)."""
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    env = dict(os.environ)
    env["PYTHONPATH"] = "src"
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "--collect-only", "-q", "tests"],
        cwd=ROOT, capture_output=True, text=True, env=env,
    )
    lines = [ln for ln in result.stdout.splitlines() if "::" in ln]
    print(f"test count: {len(lines)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
