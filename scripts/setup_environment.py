"""Create and provision the repository's development virtual environment."""

from __future__ import annotations

import os
import subprocess
import sys
import venv
from pathlib import Path

MINIMUM_PYTHON = (3, 10)
ROOT = Path(__file__).resolve().parents[1]
ENVIRONMENT = ROOT / ".venv"


def run(command: list[str]) -> None:
    """Run a setup command and stop if it fails."""
    subprocess.run(command, cwd=ROOT, check=True)


def environment_python() -> Path:
    """Return the Python executable inside the repository environment."""
    executable = "python.exe" if os.name == "nt" else "python"
    directory = "Scripts" if os.name == "nt" else "bin"
    return ENVIRONMENT / directory / executable


def main() -> None:
    """Create `.venv` when needed and install the project in editable mode."""
    if sys.version_info[:2] < MINIMUM_PYTHON:
        required = ".".join(map(str, MINIMUM_PYTHON))
        actual = ".".join(map(str, sys.version_info[:2]))
        raise SystemExit(f"Python {required}+ is required; found Python {actual}.")

    if not environment_python().exists():
        venv.create(ENVIRONMENT, with_pip=True)

    python = str(environment_python())
    run([python, "-m", "pip", "install", "--upgrade", "pip"])
    run([python, "-m", "pip", "install", "--editable", ".[dev]"])


if __name__ == "__main__":
    main()
