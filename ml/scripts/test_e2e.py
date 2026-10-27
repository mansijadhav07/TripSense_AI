#!/usr/bin/env python3
"""
Runs every automated check in the repo: the ML tests and the API workflow tests
(which use the real trained artifacts and catalogue, no mocks).

    python ml/scripts/test_e2e.py
"""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def run(cmd, cwd):
    print("$", " ".join(cmd), f"(in {cwd.relative_to(ROOT) if cwd != ROOT else '.'})")
    return subprocess.call(cmd, cwd=cwd)


if __name__ == "__main__":
    rc = run([sys.executable, "-m", "pytest", "ml/tests", "-q", "--no-cov", "-p", "no:cacheprovider"], ROOT)
    rc |= run([sys.executable, "-m", "pytest", "-q", "--no-cov", "-p", "no:cacheprovider"], ROOT / "apps" / "api")
    sys.exit(rc)
